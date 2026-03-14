"""Vehicle Log Analyzer - Standalone Analysis Engine.

A cross-platform Python module for analyzing flight/vehicle telemetry logs.
Designed to run on Android (via Chaquopy) and Windows (via Electron/PyInstaller).

Usage:
    from analysis_engine import AnalysisAPI
    
    api = AnalysisAPI()
    log_data = api.parse_log('path/to/log.bin')
    diagnostics = api.analyze_diagnostics(log_data['signals'])
    harmonics = api.analyze_motor_harmonics(log_data['signals']['RCOU'])
"""

__version__ = "2.0.0"
__author__ = "Vehicle Log Analyzer Team"

from .api import AnalysisAPI

__all__ = ['AnalysisAPI']
