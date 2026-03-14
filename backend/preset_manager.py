"""Preset management system for graph layouts and configurations."""
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class PresetManager:
    """Manage analysis presets for signal plotting and configurations."""
    
    def __init__(self, preset_dir: str = None):
        self.preset_dir = Path(preset_dir or "/app/backend/presets")
        self.preset_dir.mkdir(exist_ok=True)
        self.presets: Dict[str, Dict] = {}
        self._load_default_presets()
    
    def _load_default_presets(self):
        """Load built-in default presets."""
        default_presets = [
            {
                "id": "attitude",
                "name": "Attitude",
                "description": "Roll, Pitch, Yaw analysis",
                "signals": [
                    {"type": "ATT", "field": "Roll"},
                    {"type": "ATT", "field": "Pitch"},
                    {"type": "ATT", "field": "Yaw"},
                ],
                "chart_config": {
                    "title": "Attitude Analysis",
                    "y_label": "Degrees",
                    "show_grid": True,
                },
                "is_default": True,
            },
            {
                "id": "vibration",
                "name": "Vibration",
                "description": "3-axis vibration analysis",
                "signals": [
                    {"type": "VIBE", "field": "VibeX"},
                    {"type": "VIBE", "field": "VibeY"},
                    {"type": "VIBE", "field": "VibeZ"},
                ],
                "chart_config": {
                    "title": "Vibration Analysis",
                    "y_label": "m/s²",
                    "show_threshold": True,
                    "threshold_value": 30.0,
                },
                "is_default": True,
            },
            {
                "id": "motors",
                "name": "Motors",
                "description": "Motor output comparison",
                "signals": [
                    {"type": "RCOU", "field": "C1"},
                    {"type": "RCOU", "field": "C2"},
                    {"type": "RCOU", "field": "C3"},
                    {"type": "RCOU", "field": "C4"},
                ],
                "chart_config": {
                    "title": "Motor Outputs",
                    "y_label": "PWM",
                    "y_min": 1000,
                    "y_max": 2000,
                },
                "is_default": True,
            },
            {
                "id": "battery",
                "name": "Battery",
                "description": "Battery voltage and current",
                "signals": [
                    {"type": "BAT", "field": "Volt"},
                    {"type": "BAT", "field": "Curr"},
                ],
                "chart_config": {
                    "title": "Battery Health",
                    "dual_axis": True,
                },
                "is_default": True,
            },
        ]
        
        for preset in default_presets:
            self.presets[preset["id"]] = preset
    
    def create_preset(self, name: str, signals: List[Dict], description: str = "", 
                     chart_config: Dict = None, author: str = "User") -> Dict:
        """Create a new preset."""
        preset_id = str(uuid.uuid4())
        preset = {
            "id": preset_id,
            "name": name,
            "description": description,
            "signals": signals,
            "chart_config": chart_config or {},
            "author": author,
            "is_default": False,
            "created_at": self._get_timestamp(),
        }
        
        self.presets[preset_id] = preset
        self._save_preset_to_file(preset)
        return preset
    
    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """Get a preset by ID."""
        return self.presets.get(preset_id)
    
    def list_presets(self, include_defaults: bool = True) -> List[Dict]:
        """List all presets."""
        if include_defaults:
            return list(self.presets.values())
        return [p for p in self.presets.values() if not p.get('is_default', False)]
    
    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset."""
        if preset_id in self.presets:
            preset = self.presets[preset_id]
            if preset.get('is_default'):
                return False  # Cannot delete default presets
            
            del self.presets[preset_id]
            preset_file = self.preset_dir / f"{preset_id}.json"
            if preset_file.exists():
                preset_file.unlink()
            return True
        return False
    
    def export_preset(self, preset_id: str) -> Optional[str]:
        """Export a preset as JSON string."""
        preset = self.get_preset(preset_id)
        if preset:
            return json.dumps(preset, indent=2)
        return None
    
    def import_preset(self, preset_json: str) -> Optional[Dict]:
        """Import a preset from JSON string."""
        try:
            preset_data = json.loads(preset_json)
            # Generate new ID to avoid conflicts
            preset_data['id'] = str(uuid.uuid4())
            preset_data['is_default'] = False
            preset_data['imported_at'] = self._get_timestamp()
            
            self.presets[preset_data['id']] = preset_data
            self._save_preset_to_file(preset_data)
            return preset_data
        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            return None
    
    def _save_preset_to_file(self, preset: Dict):
        """Save preset to disk."""
        if preset.get('is_default'):
            return  # Don't save default presets to disk
        
        try:
            preset_file = self.preset_dir / f"{preset['id']}.json"
            with open(preset_file, 'w') as f:
                json.dump(preset, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
