import numpy as np
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq
from typing import Dict, List, Any, Optional
import io
import csv


class SignalProcessor:
    """Advanced signal processing for ArduPilot flight data."""

    def compute_fft(
        self,
        timestamps: List[float],
        values: List[float],
        window_size: int = 1024,
        overlap: float = 0.5,
    ) -> Dict[str, Any]:
        """Compute FFT with windowing and peak detection."""
        t = np.array(timestamps)
        v = np.array(values)

        if len(v) < window_size:
            window_size = len(v)

        # Compute sample rate
        dt = np.median(np.diff(t))
        if dt <= 0:
            dt = 0.01
        fs = 1.0 / dt

        # Detrend (remove DC offset and linear trend)
        v_segment = v[:window_size]
        v_detrended = scipy_signal.detrend(v_segment, type='linear')

        # Apply Hanning window
        window = np.hanning(window_size)
        v_windowed = v_detrended * window

        # Compute FFT
        N = window_size
        yf = fft(v_windowed)
        xf = fftfreq(N, dt)

        # Take positive frequencies only
        pos_mask = xf > 0
        freqs = xf[pos_mask].tolist()
        magnitude = (2.0 / N * np.abs(yf[pos_mask])).tolist()

        # Power spectral density
        psd = (np.abs(yf[pos_mask]) ** 2 / (N * fs)).tolist()

        # Peak detection
        mag_arr = np.array(magnitude)
        peaks = self._detect_peaks(freqs, mag_arr)

        return {
            "frequencies": freqs,
            "magnitude": magnitude,
            "psd": psd,
            "sample_rate": round(fs, 1),
            "window_size": window_size,
            "peaks": peaks,
            "nyquist": round(fs / 2, 1),
        }

    def compute_spectrogram(
        self,
        timestamps: List[float],
        values: List[float],
        window_size: int = 256,
        overlap: float = 0.5,
    ) -> Dict[str, Any]:
        """Compute spectrogram for time-frequency analysis."""
        t = np.array(timestamps)
        v = np.array(values)

        dt = np.median(np.diff(t))
        if dt <= 0:
            dt = 0.01
        fs = 1.0 / dt

        noverlap = int(window_size * overlap)

        if len(v) < window_size:
            return {"times": [], "frequencies": [], "power": [], "sample_rate": fs}

        f, t_spec, Sxx = scipy_signal.spectrogram(
            v, fs=fs, nperseg=min(window_size, len(v)),
            noverlap=min(noverlap, len(v) - 1),
            window='hann'
        )

        # Convert to dB
        Sxx_db = 10 * np.log10(Sxx + 1e-12)

        # Downsample spectrogram for transfer
        max_freq_bins = 128
        max_time_bins = 200
        if len(f) > max_freq_bins:
            step = len(f) // max_freq_bins
            f = f[::step]
            Sxx_db = Sxx_db[::step, :]
        if len(t_spec) > max_time_bins:
            step = len(t_spec) // max_time_bins
            t_spec = t_spec[::step]
            Sxx_db = Sxx_db[:, ::step]

        return {
            "times": (t_spec + t[0]).tolist(),
            "frequencies": f.tolist(),
            "power": Sxx_db.tolist(),
            "sample_rate": round(fs, 1),
        }

    def _detect_peaks(self, freqs: list, magnitude: np.ndarray, num_peaks: int = 10) -> list:
        """Detect frequency peaks and identify harmonics."""
        if len(magnitude) < 3:
            return []

        # Find peaks using scipy
        peak_indices, properties = scipy_signal.find_peaks(
            magnitude, height=np.max(magnitude) * 0.05,
            distance=max(1, len(magnitude) // 50),
            prominence=np.max(magnitude) * 0.02
        )

        if len(peak_indices) == 0:
            return []

        # Sort by magnitude
        sorted_idx = np.argsort(magnitude[peak_indices])[::-1][:num_peaks]
        peak_indices = peak_indices[sorted_idx]

        peaks = []
        fundamental = freqs[peak_indices[0]] if len(peak_indices) > 0 else 0

        for idx in peak_indices:
            freq = freqs[idx]
            mag = float(magnitude[idx])
            harmonic = round(freq / fundamental, 1) if fundamental > 0 else 0
            is_harmonic = abs(harmonic - round(harmonic)) < 0.15 and harmonic > 1.5

            peaks.append({
                "frequency": round(freq, 2),
                "magnitude": round(mag, 4),
                "harmonic_ratio": harmonic,
                "is_harmonic": bool(is_harmonic),
                "label": f"{round(freq, 1)} Hz" + (f" (H{int(round(harmonic))})" if is_harmonic else ""),
            })

        return peaks

    def downsample_lttb(self, x: list, y: list, target_points: int) -> tuple:
        """Largest Triangle Three Buckets downsampling algorithm."""
        if len(x) <= target_points:
            return x, y

        x = np.array(x)
        y = np.array(y)
        n = len(x)

        bucket_size = (n - 2) / (target_points - 2)
        out_x = [x[0]]
        out_y = [y[0]]

        a = 0
        for i in range(1, target_points - 1):
            bucket_start = int((i - 1) * bucket_size) + 1
            bucket_end = int(i * bucket_size) + 1
            next_start = int(i * bucket_size) + 1
            next_end = min(int((i + 1) * bucket_size) + 1, n)

            avg_x = np.mean(x[next_start:next_end])
            avg_y = np.mean(y[next_start:next_end])

            max_area = -1
            max_idx = bucket_start

            for j in range(bucket_start, min(bucket_end, n)):
                area = abs(
                    (x[a] - avg_x) * (y[j] - y[a])
                    - (x[a] - x[j]) * (avg_y - y[a])
                )
                if area > max_area:
                    max_area = area
                    max_idx = j

            out_x.append(float(x[max_idx]))
            out_y.append(float(y[max_idx]))
            a = max_idx

        out_x.append(float(x[-1]))
        out_y.append(float(y[-1]))

        return out_x, out_y

    def to_csv(self, signal_data: Dict[str, list]) -> str:
        """Convert signal data to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        fields = list(signal_data.keys())
        writer.writerow(fields)

        n = max(len(v) for v in signal_data.values())
        for i in range(n):
            row = []
            for field in fields:
                vals = signal_data[field]
                row.append(vals[i] if i < len(vals) else "")
            writer.writerow(row)

        return output.getvalue()
