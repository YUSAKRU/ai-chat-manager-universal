"""
Enhanced Memory Bank System
===========================

This module provides an enterprise-grade Memory Bank system with:
- Robust error handling and recovery
- Comprehensive logging and monitoring  
- Environment-specific configuration management
- Performance optimization and caching
- Security and integrity validation

Components:
-----------
- MemoryBankManager: Main orchestrator with error handling
- MemoryBankConfig: Configuration management and validation
- MemoryBankLogger: Specialized logging for Memory Bank operations
- MemoryBankPerformance: Performance monitoring and metrics
- MemoryBankSecurity: Security and integrity validation
"""

try:
    from .config_manager import MemoryBankConfigManager
    from .memory_bank_manager import MemoryBankManager
    from .performance_monitor import MemoryBankPerformanceMonitor
    from .security_validator import MemoryBankSecurityValidator
    from .error_handler import MemoryBankErrorHandler
except ImportError:
    # Module can be imported but components may not be fully functional
    MemoryBankConfigManager = None
    MemoryBankManager = None
    MemoryBankPerformanceMonitor = None
    MemoryBankSecurityValidator = None
    MemoryBankErrorHandler = None

__version__ = "1.0.0"
__author__ = "AI Chrome Chat Manager Team"

__all__ = [
    "MemoryBankConfigManager",
    "MemoryBankManager", 
    "MemoryBankPerformanceMonitor",
    "MemoryBankSecurityValidator",
    "MemoryBankErrorHandler",
] 