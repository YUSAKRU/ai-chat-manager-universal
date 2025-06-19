"""
Secrets Management - Güvenli configuration değerleri yönetimi
"""
import os
from typing import Dict, Any, Optional


class SecretsManager:
    """Configuration secrets yönetimi"""
    
    def __init__(self, 
                 secrets_prefix: str = 'SECRET_',
                 env_prefix: str = 'LOG_'):
        self.secrets_prefix = secrets_prefix
        self.env_prefix = env_prefix
    
    def resolve_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configuration'daki secret referanslarını çöz"""
        return self._resolve_recursive(config)
    
    def _resolve_recursive(self, obj: Any) -> Any:
        """Recursive secret resolution"""
        if isinstance(obj, dict):
            return {key: self._resolve_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._resolve_string_value(obj)
        else:
            return obj
    
    def _resolve_string_value(self, value: str) -> str:
        """String değerindeki secret referanslarını çöz"""
        if not isinstance(value, str):
            return value
        
        # Environment variable reference: ${ENV_VAR_NAME}
        if value.startswith('${') and value.endswith('}'):
            env_var_name = value[2:-1]
            env_value = os.getenv(env_var_name)
            if env_value is not None:
                return env_value
            else:
                print(f"Warning: Environment variable {env_var_name} not found")
                return value
        
        # Secret file reference: file:/path/to/secret
        if value.startswith('file:'):
            file_path = value[5:]  # Remove 'file:' prefix
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Failed to read secret file {file_path}: {str(e)}")
                return value
        
        # Direct environment variable with prefix
        if value.startswith(self.secrets_prefix):
            env_value = os.getenv(value)
            if env_value is not None:
                return env_value
            else:
                print(f"Warning: Secret environment variable {value} not found")
                return value
        
        return value
    
    def get_environment_secrets(self) -> Dict[str, str]:
        """Environment'daki secret değerleri topla"""
        secrets = {}
        
        # LOG_ prefix ile başlayan environment variables
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix):].lower()
                secrets[config_key] = value
        
        # SECRET_ prefix ile başlayan environment variables
        for key, value in os.environ.items():
            if key.startswith(self.secrets_prefix):
                secrets[key] = value
        
        return secrets
    
    def create_secret_config_template(self) -> Dict[str, Any]:
        """Secret kullanımı için template config"""
        return {
            'level': '${LOG_LEVEL}',  # Environment variable
            'format': 'json',
            'log_dir': '${LOG_DIR}',
            'handlers': {
                'console': {
                    'enabled': True,
                    'level': '${LOG_CONSOLE_LEVEL}',
                    'format': 'plain'
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'format': 'json',
                    'filename': 'app.log'
                }
            }
        }
    
    def get_secrets_summary(self) -> Dict[str, Any]:
        """Secrets manager özeti"""
        return {
            'secrets_prefix': self.secrets_prefix,
            'env_prefix': self.env_prefix,
            'available_env_secrets': len(self.get_environment_secrets()),
            'environment_secrets': list(self.get_environment_secrets().keys())
        }
    
    def close(self):
        """Secrets manager'ı kapat"""
        pass 