"""Data structures for log analysis."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class SignalData:
    """Container for signal time series data."""
    message_type: str
    field_name: str
    timestamps: List[float]
    values: List[float]
    unit: Optional[str] = None
    
    def __len__(self) -> int:
        return len(self.values)
    
    def to_dict(self) -> Dict:
        return {
            'message_type': self.message_type,
            'field_name': self.field_name,
            'timestamps': self.timestamps,
            'values': self.values,
            'unit': self.unit,
        }


@dataclass
class LogData:
    """Container for parsed log data."""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = "unknown.bin"
    duration_sec: float = 0.0
    message_types: List[str] = field(default_factory=list)
    signals: Dict[str, Dict[str, List]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_signal(self, message_type: str, field: str) -> Optional[SignalData]:
        """Get a specific signal."""
        if message_type not in self.signals:
            return None
        
        msg_data = self.signals[message_type]
        if field not in msg_data or 'TimeUS' not in msg_data:
            return None
        
        return SignalData(
            message_type=message_type,
            field_name=field,
            timestamps=msg_data['TimeUS'],
            values=msg_data[field],
        )
    
    def to_dict(self) -> Dict:
        return {
            'log_id': self.log_id,
            'filename': self.filename,
            'duration_sec': self.duration_sec,
            'message_types': self.message_types,
            'signals': self.signals,
            'metadata': self.metadata,
        }


@dataclass
class DiagnosticsResult:
    """Container for diagnostics analysis results."""
    health_score: int
    checks: List[Dict[str, Any]]
    critical: int
    warnings: int
    passed: int
    parameter_limits: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'health_score': self.health_score,
            'checks': self.checks,
            'critical': self.critical,
            'warnings': self.warnings,
            'passed': self.passed,
            'parameter_limits': self.parameter_limits,
        }


@dataclass
class MotorHarmonicsResult:
    """Container for motor harmonics analysis."""
    motor_harmonics: List[Dict[str, Any]]
    motor_imbalance: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'motor_harmonics': self.motor_harmonics,
            'motor_imbalance': self.motor_imbalance,
        }


@dataclass
class CorrelationResult:
    """Container for correlation analysis."""
    status: str
    correlations: List[Dict[str, Any]]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status,
            'correlations': self.correlations,
            'summary': self.summary,
        }
