"""Motor harmonic detection module for RCOU signal analysis."""
import numpy as np
from typing import Dict, List, Any
from scipy.fft import fft, fftfreq
from scipy import signal as scipy_signal


class MotorHarmonicsDetector:
    """Detect motor harmonics and imbalance using FFT analysis on motor outputs."""

    def analyze(self, rcou_data: Dict, duration_sec: float) -> Dict[str, Any]:
        """Analyze motor outputs for harmonic content."""
        if not rcou_data or 'TimeUS' not in rcou_data:
            return {"motor_harmonics": [], "motor_imbalance": None}

        motor_fields = [f for f in ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'] if f in rcou_data]
        if len(motor_fields) < 2:
            return {"motor_harmonics": [], "motor_imbalance": None}

        results = []
        timestamps = np.array(rcou_data['TimeUS'])
        dt = np.median(np.diff(timestamps))
        fs = 1.0 / dt if dt > 0 else 50.0

        # Analyze each motor
        for motor_field in motor_fields:
            values = np.array(rcou_data[motor_field])
            if len(values) < 256:
                continue

            # Compute FFT
            harmonics = self._compute_motor_fft(values, fs)
            if harmonics:
                results.append({
                    "motor": motor_field,
                    "motor_num": int(motor_field[1]),
                    "harmonics": harmonics,
                    "dominant_freq": harmonics[0]['frequency'],
                    "total_harmonic_distortion": self._compute_thd(harmonics),
                })

        # Compute motor imbalance
        imbalance = self._compute_motor_imbalance(rcou_data, motor_fields)

        return {
            "motor_harmonics": results,
            "motor_imbalance": imbalance,
        }

    def _compute_motor_fft(self, values: np.ndarray, fs: float, window_size: int = 1024) -> List[Dict]:
        """Compute FFT and extract harmonic peaks."""
        if len(values) < window_size:
            window_size = len(values)

        # Detrend and window
        v_segment = values[:window_size]
        v_detrended = scipy_signal.detrend(v_segment, type='linear')
        window = np.hanning(window_size)
        v_windowed = v_detrended * window

        # FFT
        yf = fft(v_windowed)
        xf = fftfreq(window_size, 1/fs)

        # Positive frequencies
        pos_mask = xf > 0
        freqs = xf[pos_mask]
        magnitude = 2.0 / window_size * np.abs(yf[pos_mask])

        # Find peaks (motor harmonics)
        peak_indices, _ = scipy_signal.find_peaks(
            magnitude,
            height=np.max(magnitude) * 0.1,
            distance=max(1, len(magnitude) // 50)
        )

        if len(peak_indices) == 0:
            return []

        # Sort by magnitude, take top 5
        sorted_idx = np.argsort(magnitude[peak_indices])[::-1][:5]
        harmonics = []

        for idx in peak_indices[sorted_idx]:
            harmonics.append({
                "frequency": round(float(freqs[idx]), 2),
                "magnitude": round(float(magnitude[idx]), 4),
                "power_db": round(20 * np.log10(magnitude[idx] + 1e-12), 2),
            })

        return harmonics

    def _compute_thd(self, harmonics: List[Dict]) -> float:
        """Compute Total Harmonic Distortion."""
        if len(harmonics) < 2:
            return 0.0

        fundamental = harmonics[0]['magnitude']
        harmonic_sum = sum(h['magnitude']**2 for h in harmonics[1:])
        thd = np.sqrt(harmonic_sum) / fundamental if fundamental > 0 else 0
        return round(float(thd * 100), 2)  # Percentage

    def _compute_motor_imbalance(self, rcou_data: Dict, motor_fields: List[str]) -> Dict:
        """Compute motor imbalance metrics."""
        motor_avgs = {}
        motor_stds = {}
        motor_ranges = {}

        for field in motor_fields:
            values = np.array(rcou_data[field])
            motor_avgs[field] = float(np.mean(values))
            motor_stds[field] = float(np.std(values))
            motor_ranges[field] = float(np.max(values) - np.min(values))

        overall_avg = np.mean(list(motor_avgs.values()))
        deviations = {f: abs(motor_avgs[f] - overall_avg) for f in motor_fields}
        max_deviation_motor = max(deviations, key=deviations.get)
        max_deviation = deviations[max_deviation_motor]

        return {
            "motor_averages": motor_avgs,
            "overall_average": round(overall_avg, 2),
            "max_deviation": round(max_deviation, 2),
            "max_deviation_motor": max_deviation_motor,
            "imbalance_percentage": round(max_deviation / overall_avg * 100, 2) if overall_avg > 0 else 0,
            "status": "balanced" if max_deviation < 30 else "warning" if max_deviation < 50 else "critical",
        }
