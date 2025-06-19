"""
Environment Detection - Çalışma ortamını otomatik algılar
"""
import os
import platform
import socket
from typing import Dict, Any, Optional


class EnvironmentDetector:
    """
    Çalışma ortamını algılar
    - Development, staging, production detection
    - Container/cloud environment detection
    - System information collection
    """
    
    def __init__(self):
        self._detected_env = None
        self._system_info = None
    
    def detect(self) -> str:
        """Ana environment detection metodu"""
        if self._detected_env is None:
            self._detected_env = self._detect_environment()
        return self._detected_env
    
    def _detect_environment(self) -> str:
        """Environment detection logic"""
        # 1. Explicit environment variable
        explicit_env = os.getenv('ENVIRONMENT', '').lower()
        if explicit_env in ['development', 'dev', 'staging', 'stage', 'production', 'prod']:
            return self._normalize_env_name(explicit_env)
        
        # 2. Flask environment
        flask_env = os.getenv('FLASK_ENV', '').lower()
        if flask_env in ['development', 'production']:
            return flask_env
        
        # 3. Python environment indicators
        if os.getenv('PYTHONDEBUG') or os.getenv('DEBUG'):
            return 'development'
        
        # 4. Development indicators
        if self._is_development_environment():
            return 'development'
        
        # 5. Production indicators  
        if self._is_production_environment():
            return 'production'
        
        # 6. Container/cloud detection
        container_env = self._detect_container_environment()
        if container_env:
            return container_env
        
        # 7. Default fallback
        return 'development'
    
    def _normalize_env_name(self, env: str) -> str:
        """Environment adını normalize et"""
        env = env.lower()
        if env in ['dev', 'development']:
            return 'development'
        elif env in ['stage', 'staging']:
            return 'staging'
        elif env in ['prod', 'production']:
            return 'production'
        return env
    
    def _is_development_environment(self) -> bool:
        """Development environment indicators"""
        dev_indicators = [
            # Development tools
            os.path.exists('.git'),
            os.path.exists('package.json'),
            os.path.exists('requirements.txt'),
            os.path.exists('pyproject.toml'),
            
            # IDE indicators
            os.path.exists('.vscode'),
            os.path.exists('.idea'),
            
            # Development environment variables
            os.getenv('DEVELOPMENT') == '1',
            os.getenv('LOCAL_DEVELOPMENT') == 'true',
            
            # Interactive terminal
            os.isatty(0),  # stdin is terminal
        ]
        
        return any(dev_indicators)
    
    def _is_production_environment(self) -> bool:
        """Production environment indicators"""
        prod_indicators = [
            # Production environment variables
            os.getenv('PRODUCTION') == '1',
            os.getenv('PROD') == 'true',
            
            # Web server indicators
            os.getenv('WSGI_MODULE'),
            os.getenv('GUNICORN_CMD_ARGS'),
            
            # System service indicators
            os.getenv('SUPERVISOR_ENABLED'),
            os.getenv('SYSTEMD_EXEC_PID'),
            
            # No development tools
            not os.path.exists('.git') and not os.path.exists('requirements.txt')
        ]
        
        return any(prod_indicators)
    
    def _detect_container_environment(self) -> Optional[str]:
        """Container/cloud environment detection"""
        # Docker
        if os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER'):
            return 'production'  # Docker genelde production
        
        # Kubernetes
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            return 'production'
        
        # Cloud providers
        if os.getenv('AWS_EXECUTION_ENV') or os.getenv('AWS_LAMBDA_RUNTIME_API'):
            return 'production'
        
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            return 'production'
        
        if os.getenv('AZURE_FUNCTIONS_ENVIRONMENT'):
            return 'production'
        
        # Heroku
        if os.getenv('DYNO'):
            return 'production'
        
        return None
    
    def get_system_info(self) -> Dict[str, Any]:
        """Sistem bilgilerini topla"""
        if self._system_info is None:
            self._system_info = self._collect_system_info()
        return self._system_info
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Detaylı sistem bilgisi toplama"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            hostname = 'unknown'
            ip_address = 'unknown'
        
        return {
            # Environment info
            'environment': self.detect(),
            'hostname': hostname,
            'ip_address': ip_address,
            
            # System info
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            
            # Process info
            'pid': os.getpid(),
            'working_directory': os.getcwd(),
            'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            
            # Environment variables (filtered)
            'environment_variables': self._get_relevant_env_vars(),
            
            # Container/cloud detection
            'is_docker': os.path.exists('/.dockerenv'),
            'is_kubernetes': bool(os.getenv('KUBERNETES_SERVICE_HOST')),
            'is_aws': bool(os.getenv('AWS_EXECUTION_ENV')),
            'is_gcp': bool(os.getenv('GOOGLE_CLOUD_PROJECT')),
            'is_azure': bool(os.getenv('AZURE_FUNCTIONS_ENVIRONMENT')),
            'is_heroku': bool(os.getenv('DYNO'))
        }
    
    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Logging için relevantolan environment variables"""
        relevant_vars = [
            'ENVIRONMENT', 'FLASK_ENV', 'DEBUG', 'PYTHONDEBUG',
            'LOG_LEVEL', 'LOG_FORMAT', 'LOG_DIR',
            'DOCKER_CONTAINER', 'KUBERNETES_SERVICE_HOST',
            'AWS_EXECUTION_ENV', 'GOOGLE_CLOUD_PROJECT', 'DYNO'
        ]
        
        return {var: os.getenv(var, '') for var in relevant_vars if os.getenv(var)}
    
    def is_development(self) -> bool:
        """Development environment mi?"""
        return self.detect() == 'development'
    
    def is_staging(self) -> bool:
        """Staging environment mi?"""
        return self.detect() == 'staging'
    
    def is_production(self) -> bool:
        """Production environment mi?"""
        return self.detect() == 'production'
    
    def get_environment_config_recommendations(self) -> Dict[str, Any]:
        """Environment'a göre config önerileri"""
        env = self.detect()
        
        if env == 'development':
            return {
                'level': 'DEBUG',
                'handlers': {
                    'console': {'enabled': True, 'level': 'DEBUG', 'format': 'plain'},
                    'file': {'enabled': True, 'level': 'DEBUG'},
                    'error_file': {'enabled': False}
                },
                'context': {
                    'include_system_info': False,
                    'include_performance': True
                }
            }
        
        elif env == 'staging':
            return {
                'level': 'INFO',
                'handlers': {
                    'console': {'enabled': True, 'level': 'INFO', 'format': 'json'},
                    'file': {'enabled': True, 'level': 'INFO'},
                    'error_file': {'enabled': True, 'level': 'WARNING'}
                },
                'context': {
                    'include_system_info': True,
                    'include_performance': True
                }
            }
        
        elif env == 'production':
            return {
                'level': 'WARNING',
                'handlers': {
                    'console': {'enabled': False},
                    'file': {'enabled': True, 'level': 'INFO'},
                    'error_file': {'enabled': True, 'level': 'WARNING'}
                },
                'context': {
                    'include_system_info': True,
                    'include_performance': False
                },
                'rotation': {
                    'max_size': 50 * 1024 * 1024,  # 50MB for production
                    'backup_count': 20
                }
            }
        
        return {} 