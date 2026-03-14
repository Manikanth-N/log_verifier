"""FFT Analysis Module."""
import numpy as np
from scipy.fft import fft, fftfreq
from scipy import signal
from typing import Dict, List, Any


class FFTAnalyzer:
    """Perform FFT analysis on time series data."""
    
    def analyze(self, timestamps: List[float], values: List[float], 
                window_size: int = 1024) -> Dict[str, Any]:
        """Perform FFT analysis on signal data.
        
        Args:
            timestamps: Time values in microseconds
            values: Signal amplitude values
            window_size: FFT window size (power of 2)
        
        Returns:
            Dictionary containing FFT results
        """
        if len(values) < window_size:
            window_size = len(values)
        
        # Calculate sampling rate
        if len(timestamps) > 1:
            dt_us = np.median(np.diff(timestamps[:1000]))
            fs = 1.0 / (dt_us / 1e6) if dt_us > 0 else 100.0
        else:
            fs = 100.0
        
        # Take a segment
        segment = values[:window_size]
        
        # Detrend
        segment_detrended = signal.detrend(segment, type='linear')
        
        # Apply Hanning window
        window = np.hanning(len(segment_detrended))
        segment_windowed = segment_detrended * window
        
        # Perform FFT
        yf = fft(segment_windowed)
        xf = fftfreq(len(segment_windowed), 1/fs)
        
        # Positive frequencies only
        pos_mask = xf > 0
        frequencies = xf[pos_mask].tolist()
        magnitudes = (2.0/len(segment_windowed) * np.abs(yf[pos_mask])).tolist()
        
        # Power spectral density
        psd = (np.abs(yf[pos_mask])**2).tolist()
        
        # Find dominant frequency
        if len(magnitudes) > 0:
            dominant_idx = np.argmax(magnitudes)
            dominant_frequency = frequencies[dominant_idx]
            dominant_magnitude = magnitudes[dominant_idx]
        else:
            dominant_frequency = 0.0
            dominant_magnitude = 0.0
        
        return {
            'frequencies': frequencies,
            'magnitudes': magnitudes,
            'psd': psd,
            'sampling_rate': fs,
            'window_size': window_size,
            'dominant_frequency': dominant_frequency,
            'dominant_magnitude': dominant_magnitude,
        }
    
    def spectrogram(self, timestamps: List[float], values: List[float],
                   nperseg: int = 256) -> Dict[str, Any]:
        """Generate spectrogram data.
        
        Args:
            timestamps: Time values
            values: Signal values
            nperseg: Length of each segment
        
        Returns:
            Dictionary containing spectrogram data
        """
        if len(values) < nperseg:
            nperseg = len(values) // 2
        
        # Calculate sampling rate
        if len(timestamps) > 1:
            dt_us = np.median(np.diff(timestamps[:1000]))
            fs = 1.0 / (dt_us / 1e6) if dt_us > 0 else 100.0
        else:
            fs = 100.0
        
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            values,
            fs=fs,
            nperseg=nperseg,
            noverlap=nperseg//2,
        )
        
        return {
            'frequencies': f.tolist(),
            'times': t.tolist(),
            'power': Sxx.tolist(),
            'sampling_rate': fs,
        }
