"""Plugin system for extensible analysis modules."""
import importlib
import os
import inspect
from pathlib import Path
from typing import Dict, Any, List, Callable
import logging

logger = logging.getLogger(__name__)


class AnalysisPlugin:
    """Base class for analysis plugins."""
    
    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base analysis plugin"
    author: str = "Unknown"
    
    def analyze(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on log data."""
        raise NotImplementedError("Plugin must implement analyze method")

    def get_metadata(self) -> Dict[str, str]:
        """Return plugin metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
        }


class PluginManager:
    """Manage analysis plugins."""
    
    def __init__(self, plugin_dir: str = None):
        self.plugin_dir = Path(plugin_dir or "/app/backend/plugins")
        self.plugins: Dict[str, AnalysisPlugin] = {}
        self.plugin_dir.mkdir(exist_ok=True)
        
    def load_plugins(self) -> int:
        """Discover and load all plugins from plugin directory."""
        loaded = 0
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            try:
                plugin_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, AnalysisPlugin) and obj != AnalysisPlugin:
                            plugin_instance = obj()
                            self.plugins[plugin_instance.name] = plugin_instance
                            logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                            loaded += 1
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")
                
        return loaded
    
    def get_plugin(self, name: str) -> AnalysisPlugin:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """List all loaded plugins."""
        return [p.get_metadata() for p in self.plugins.values()]
    
    def run_plugin(self, plugin_name: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific plugin on log data."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {"error": f"Plugin '{plugin_name}' not found"}
        
        try:
            return plugin.analyze(log_data)
        except Exception as e:
            logger.error(f"Plugin {plugin_name} failed: {e}")
            return {"error": str(e)}
    
    def run_all_plugins(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all loaded plugins."""
        results = {}
        for plugin_name, plugin in self.plugins.items():
            try:
                results[plugin_name] = plugin.analyze(log_data)
            except Exception as e:
                logger.error(f"Plugin {plugin_name} failed: {e}")
                results[plugin_name] = {"error": str(e)}
        return results


# Example plugin implementation
class VibrationAnalysisPlugin(AnalysisPlugin):
    """Enhanced vibration analysis plugin."""
    
    name = "vibration_analysis_enhanced"
    version = "1.0.0"
    description = "Enhanced vibration analysis with spectral decomposition"
    author = "Vehicle Log Analyzer Team"
    
    def analyze(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vibration patterns."""
        signals = log_data.get('signals', {})
        if 'VIBE' not in signals:
            return {"status": "no_vibe_data"}
        
        vibe = signals['VIBE']
        results = {
            "analyzed_axes": [],
            "spectral_content": {},
        }
        
        for axis in ['VibeX', 'VibeY', 'VibeZ']:
            if axis in vibe:
                import numpy as np
                values = np.array(vibe[axis])
                results["analyzed_axes"].append({
                    "axis": axis,
                    "mean": float(np.mean(values)),
                    "max": float(np.max(values)),
                    "std": float(np.std(values)),
                    "p95": float(np.percentile(values, 95)),
                })
        
        return results
