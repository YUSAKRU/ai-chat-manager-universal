import os
import importlib.util
import inspect
import re
from typing import Dict, List, Any, Callable
from abc import ABC, abstractmethod
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """Base class that all plugins must inherit from"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.triggers = []
        self.is_active = True
        
    @abstractmethod
    def get_triggers(self) -> List[str]:
        """Return list of trigger patterns (regex) that activate this plugin"""
        pass
    
    @abstractmethod
    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin logic when triggered"""
        pass
    
    def get_info(self) -> Dict[str, str]:
        """Return plugin information"""
        return {
            "name": self.name,
            "description": self.__doc__ or "No description available",
            "triggers": self.get_triggers(),
            "active": self.is_active
        }

class PluginManager:
    """Manages loading, registration and execution of plugins"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, BasePlugin] = {}
        self.message_handlers: List[Callable] = []
        
        # Create plugins directory if it doesn't exist
        os.makedirs(plugins_dir, exist_ok=True)
        
        # Create __init__.py in plugins directory
        init_file = os.path.join(plugins_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'w').close()
    
    def load_plugins(self):
        """Dynamically load all plugins from plugins directory"""
        logger.info(f"Loading plugins from {self.plugins_dir}")
        
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist")
            return
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                self._load_plugin_file(filename)
    
    def _load_plugin_file(self, filename: str):
        """Load a single plugin file"""
        try:
            plugin_path = os.path.join(self.plugins_dir, filename)
            plugin_name = filename[:-3]  # Remove .py extension
            
            # Load module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load spec for {filename}")
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find classes that inherit from BasePlugin
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BasePlugin) and 
                    obj is not BasePlugin and 
                    not inspect.isabstract(obj)):
                    
                    # Instantiate plugin
                    plugin_instance = obj()
                    self.register_plugin(plugin_instance)
                    logger.info(f"Loaded plugin: {name} from {filename}")
                    
        except Exception as e:
            logger.error(f"Error loading plugin {filename}: {str(e)}")
    
    def register_plugin(self, plugin: BasePlugin):
        """Register a plugin instance"""
        self.plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name}")
    
    def get_plugin_info(self) -> Dict[str, Dict]:
        """Get information about all loaded plugins"""
        return {name: plugin.get_info() for name, plugin in self.plugins.items()}
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Process a message through all applicable plugins"""
        if context is None:
            context = {}
            
        results = []
        
        for plugin_name, plugin in self.plugins.items():
            if not plugin.is_active:
                continue
                
            # Check if any of the plugin's triggers match the message
            for trigger_pattern in plugin.get_triggers():
                if re.search(trigger_pattern, message, re.IGNORECASE):
                    logger.info(f"Plugin {plugin_name} triggered by pattern: {trigger_pattern}")
                    
                    try:
                        result = await plugin.execute(message, context)
                        if result:
                            result['plugin_name'] = plugin_name
                            result['trigger_pattern'] = trigger_pattern
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error executing plugin {plugin_name}: {str(e)}")
                        results.append({
                            'plugin_name': plugin_name,
                            'error': str(e),
                            'type': 'error'
                        })
        
        return results
    
    def enable_plugin(self, plugin_name: str):
        """Enable a specific plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].is_active = True
            logger.info(f"Enabled plugin: {plugin_name}")
    
    def disable_plugin(self, plugin_name: str):
        """Disable a specific plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].is_active = False
            logger.info(f"Disabled plugin: {plugin_name}")
    
    def reload_plugins(self):
        """Reload all plugins"""
        self.plugins.clear()
        self.load_plugins()

# Global plugin manager instance
plugin_manager = PluginManager() 