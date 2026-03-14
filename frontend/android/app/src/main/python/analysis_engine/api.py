"""Unified API Interface for Vehicle Log Analyzer.

This is the single entry point for all analysis operations.
Use this from Android (Chaquopy) or Windows (Electron/PyInstaller).

Example Usage:
    >>> from analysis_engine import AnalysisAPI
    >>> 
    >>> api = AnalysisAPI()
    >>> log_data = api.parse_log('/path/to/flight.bin')
    >>> diagnostics = api.analyze_diagnostics(log_data['signals'])
    >>> harmonics = api.analyze_motor_harmonics(log_data['signals'])
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .core.log_parser import LogParser, generate_demo_log
from .core.signal_processor import SignalProcessor
from .core.data_structures import LogData, DiagnosticsResult, MotorHarmonicsResult, CorrelationResult

from .analysis.diagnostics_engine import DiagnosticsEngine
from .analysis.motor_harmonics import MotorHarmonicsDetector
from .analysis.correlation_analyzer import CorrelationAnalyzer
from .analysis.fft_analyzer import FFTAnalyzer

from .reporting.report_generator import generate_pdf_report, generate_html_report, generate_markdown_report
from .reporting.chart_generator import generate_multi_signal_chart

logger = logging.getLogger(__name__)


class AnalysisAPI:
    """Unified API for all log analysis operations.
    
    This class provides a simple interface for:
    - Parsing flight logs
    - Running diagnostics
    - Analyzing motor harmonics
    - Detecting correlations
    - Generating reports
    - Exporting data
    """
    
    def __init__(self):
        """Initialize the analysis engine."""
        self.log_parser = LogParser()
        self.signal_processor = SignalProcessor()
        self.diagnostics_engine = DiagnosticsEngine()
        self.motor_harmonics_detector = MotorHarmonicsDetector()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.fft_analyzer = FFTAnalyzer()
        logger.info("AnalysisAPI initialized")
    
    # ==================== LOG PARSING ====================
    
    def parse_log(self, file_path: str) -> Dict[str, Any]:
        """Parse a flight log file (.BIN or .LOG).
        
        Args:
            file_path: Path to the log file
        
        Returns:
            Dictionary containing:
                - log_id: Unique identifier
                - filename: Original filename
                - duration_sec: Log duration in seconds
                - message_types: List of available message types
                - signals: Dictionary of signal data
        
        Example:
            >>> result = api.parse_log('/path/to/flight.bin')
            >>> print(result['duration_sec'])
            120.5
            >>> print(result['message_types'])
            ['ATT', 'GPS', 'IMU', 'VIBE', ...]
        """
        try:
            path = Path(file_path)
            log_data = self.log_parser.parse_file(str(path))
            
            return {
                'log_id': log_data.log_id,
                'filename': path.name,
                'duration_sec': log_data.duration_sec,
                'message_types': log_data.message_types,
                'signals': log_data.signals,
                'metadata': log_data.metadata,
            }
        except Exception as e:
            logger.error(f"Failed to parse log: {e}")
            raise
    
    def generate_demo_log(self, duration_sec: float = 120.0) -> Dict[str, Any]:
        """Generate a synthetic demo flight log for testing.
        
        Args:
            duration_sec: Duration of demo log in seconds
        
        Returns:
            Same format as parse_log()
        """
        try:
            log_data = generate_demo_log(duration_sec)
            return {
                'log_id': log_data.log_id,
                'filename': 'demo_flight.bin',
                'duration_sec': log_data.duration_sec,
                'message_types': log_data.message_types,
                'signals': log_data.signals,
                'metadata': log_data.metadata,
            }
        except Exception as e:
            logger.error(f"Failed to generate demo log: {e}")
            raise
    
    # ==================== SIGNAL PROCESSING ====================
    
    def get_signal_data(self, signals: Dict, signal_requests: List[Dict],
                       max_points: int = 3000) -> List[Dict[str, Any]]:
        """Get downsampled signal data for plotting.
        
        Args:
            signals: Parsed signals dictionary
            signal_requests: List of {'type': 'ATT', 'field': 'Roll'} requests
            max_points: Maximum points to return (for performance)
        
        Returns:
            List of signal data with timestamps and values
        
        Example:
            >>> signals = log_data['signals']
            >>> data = api.get_signal_data(signals, [
            ...     {'type': 'ATT', 'field': 'Roll'},
            ...     {'type': 'ATT', 'field': 'Pitch'}
            ... ])
        """
        try:
            result = []
            for req in signal_requests:
                msg_type = req.get('type')
                field = req.get('field')
                
                if msg_type not in signals:
                    continue
                
                msg_data = signals[msg_type]
                if field not in msg_data or 'TimeUS' not in msg_data:
                    continue
                
                timestamps = msg_data['TimeUS']
                values = msg_data[field]
                
                # Downsample if needed
                if len(values) > max_points:
                    downsampled = self.signal_processor.downsample_lttb(
                        timestamps, values, max_points
                    )
                    timestamps = downsampled['timestamps']
                    values = downsampled['values']
                
                result.append({
                    'type': msg_type,
                    'field': field,
                    'timestamps': timestamps,
                    'values': values,
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get signal data: {e}")
            raise
    
    def export_csv(self, signal_data: Dict[str, List]) -> str:
        """Export signal data to CSV format.
        
        Args:
            signal_data: Dictionary with field names as keys and value lists
        
        Returns:
            CSV string
        """
        try:
            return self.signal_processor.to_csv(signal_data)
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    # ==================== FFT ANALYSIS ====================
    
    def analyze_fft(self, timestamps: List[float], values: List[float],
                   window_size: int = 1024) -> Dict[str, Any]:
        """Perform FFT analysis on a signal.
        
        Args:
            timestamps: Time values (microseconds)
            values: Signal amplitude values
            window_size: FFT window size (power of 2)
        
        Returns:
            Dictionary with frequencies, magnitudes, PSD
        """
        try:
            return self.fft_analyzer.analyze(timestamps, values, window_size)
        except Exception as e:
            logger.error(f"FFT analysis failed: {e}")
            raise
    
    def generate_spectrogram(self, timestamps: List[float], values: List[float],
                            nperseg: int = 256) -> Dict[str, Any]:
        """Generate spectrogram data.
        
        Args:
            timestamps: Time values
            values: Signal values
            nperseg: Segment length for spectrogram
        
        Returns:
            Dictionary with time-frequency data
        """
        try:
            return self.fft_analyzer.spectrogram(timestamps, values, nperseg)
        except Exception as e:
            logger.error(f"Spectrogram generation failed: {e}")
            raise
    
    # ==================== DIAGNOSTICS ====================
    
    def analyze_diagnostics(self, signals: Dict[str, Any],
                           mode: str = 'full') -> Dict[str, Any]:
        """Run automated flight diagnostics.
        
        Args:
            signals: Parsed signals dictionary
            mode: 'quick' or 'full' analysis
        
        Returns:
            Dictionary containing:
                - health_score: 0-100 score
                - checks: List of diagnostic checks
                - critical/warnings/passed counts
                - parameter_limits: Detected limit violations
        
        Example:
            >>> diagnostics = api.analyze_diagnostics(log_data['signals'])
            >>> print(f"Health: {diagnostics['health_score']}/100")
            >>> for check in diagnostics['checks']:
            ...     print(f"{check['name']}: {check['status']}")
        """
        try:
            result = self.diagnostics_engine.analyze(signals, mode)
            return result
        except Exception as e:
            logger.error(f"Diagnostics analysis failed: {e}")
            raise
    
    # ==================== MOTOR HARMONICS ====================
    
    def analyze_motor_harmonics(self, rcou_data: Dict[str, List],
                                duration_sec: float) -> Dict[str, Any]:
        """Analyze motor outputs for harmonic content.
        
        Args:
            rcou_data: RCOU signal data (motor PWM outputs)
            duration_sec: Log duration
        
        Returns:
            Dictionary containing:
                - motor_harmonics: FFT analysis for each motor
                - motor_imbalance: Deviation between motors
        
        Example:
            >>> if 'RCOU' in log_data['signals']:
            ...     harmonics = api.analyze_motor_harmonics(
            ...         log_data['signals']['RCOU'],
            ...         log_data['duration_sec']
            ...     )
            ...     print(harmonics['motor_imbalance']['imbalance_percentage'])
        """
        try:
            return self.motor_harmonics_detector.analyze(rcou_data, duration_sec)
        except Exception as e:
            logger.error(f"Motor harmonics analysis failed: {e}")
            raise
    
    # ==================== CORRELATION ANALYSIS ====================
    
    def analyze_vibration_throttle_correlation(self, signals: Dict) -> Dict[str, Any]:
        """Analyze correlation between vibration and throttle.
        
        Args:
            signals: Parsed signals dictionary
        
        Returns:
            Dictionary with correlation analysis per axis
        """
        try:
            return self.correlation_analyzer.analyze_vibration_throttle_correlation(signals)
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            raise
    
    def analyze_battery_load_correlation(self, signals: Dict) -> Dict[str, Any]:
        """Analyze battery voltage vs current correlation.
        
        Args:
            signals: Parsed signals dictionary
        
        Returns:
            Dictionary with sag events and correlation data
        """
        try:
            return self.correlation_analyzer.analyze_battery_load_correlation(signals)
        except Exception as e:
            logger.error(f"Battery correlation analysis failed: {e}")
            raise
    
    # ==================== REPORTING ====================
    
    def generate_report(self, log_data: Dict, diagnostics: Dict,
                       format: str = 'pdf', output_path: Optional[str] = None) -> bytes:
        """Generate a flight analysis report.
        
        Args:
            log_data: Parsed log data
            diagnostics: Diagnostics results
            format: 'pdf', 'html', or 'md'
            output_path: Optional path to save file
        
        Returns:
            Report content as bytes
        
        Example:
            >>> pdf_bytes = api.generate_report(
            ...     log_data, diagnostics, format='pdf'
            ... )
            >>> with open('report.pdf', 'wb') as f:
            ...     f.write(pdf_bytes)
        """
        try:
            if format == 'pdf':
                content = generate_pdf_report(log_data, diagnostics)
            elif format == 'html':
                content = generate_html_report(log_data, diagnostics)
            elif format == 'md' or format == 'markdown':
                content = generate_markdown_report(log_data, diagnostics)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            if output_path:
                mode = 'wb' if format == 'pdf' else 'w'
                with open(output_path, mode) as f:
                    f.write(content)
            
            return content
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise
    
    def generate_chart(self, signal_data: List[Dict], title: str = "Signal Analysis",
                      format: str = 'png', output_path: Optional[str] = None) -> bytes:
        """Generate a chart from signal data.
        
        Args:
            signal_data: List of signals with timestamps and values
            title: Chart title
            format: 'png' or 'svg'
            output_path: Optional path to save
        
        Returns:
            Chart image as bytes
        """
        try:
            content = generate_multi_signal_chart(signal_data, title, format)
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(content)
            
            return content
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            raise
    
    # ==================== METADATA ====================
    
    def get_version(self) -> str:
        """Get analysis engine version."""
        from . import __version__
        return __version__
    
    def get_available_signals(self, signals: Dict) -> Dict[str, List[str]]:
        """Get list of available signals organized by message type.
        
        Args:
            signals: Parsed signals dictionary
        
        Returns:
            Dictionary mapping message type to list of field names
        """
        result = {}
        for msg_type, msg_data in signals.items():
            fields = [k for k in msg_data.keys() if k != 'TimeUS']
            result[msg_type] = fields
        return result
