"""
Memory Bank Security Validator
==============================

Advanced security validation for Memory Bank operations with:
- Content sanitization and validation
- Access control and permissions
- Encryption and data protection
- Audit logging and compliance
- Integration with Phase 1 security logging
"""

import os
import hashlib
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from ..advanced_logging.factory import LoggerFactory
    from .config_manager import get_memory_bank_config_manager
except ImportError:
    try:
        from advanced_logging.factory import LoggerFactory
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager
    except ImportError:
        # Create stub classes for standalone operation
        class LoggerFactory:
            def get_logger(self, *args): 
                class MockLogger:
                    def debug(self, *args, **kwargs): pass
                    def info(self, *args, **kwargs): pass
                    def warning(self, *args, **kwargs): pass
                    def error(self, *args, **kwargs): pass
                return MockLogger()
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager


class SecurityLevel(Enum):
    """Security validation levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityThreat(Enum):
    """Types of security threats"""
    MALICIOUS_CONTENT = "malicious_content"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INJECTION_ATTACK = "injection_attack"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_CORRUPTION = "data_corruption"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class SecurityViolation:
    """Security violation information"""
    threat_type: SecurityThreat
    severity: SecurityLevel
    message: str
    document_type: Optional[str] = None
    file_path: Optional[str] = None
    content_snippet: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ValidationResult:
    """Result of security validation"""
    is_valid: bool
    violations: List[SecurityViolation]
    sanitized_content: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class MemoryBankSecurityValidator:
    """
    Enhanced Memory Bank Security Validator
    
    Provides comprehensive security validation with:
    - Content sanitization and threat detection
    - Data classification and protection
    - Access control validation
    - Compliance checking
    """
    
    def __init__(self):
        """Initialize security validator"""
        self.config_manager = get_memory_bank_config_manager()
        self.security_logger = LoggerFactory().get_logger("memory_bank", "security")
        
        # Security patterns
        self._sensitive_patterns = [
            # API keys and tokens
            r'(?i)(api[_-]?key|token|secret)["\s]*[:=]["\s]*([a-zA-Z0-9+/=]{20,})',
            
            # Passwords
            r'(?i)(password|pwd|pass)["\s]*[:=]["\s]*["\']([^"\']{6,})["\']',
            
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            
            # Credit card numbers (simplified)
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            
            # Social security numbers (US format)
            r'\b\d{3}-?\d{2}-?\d{4}\b',
            
            # IP addresses
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            
            # URLs with credentials
            r'https?://[^:]+:[^@]+@[^\s]+',
        ]
        
        # Malicious patterns
        self._malicious_patterns = [
            # Script injections
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'eval\s*\(',
            r'document\.write',
            
            # SQL injection attempts
            r'(?i)(union|select|insert|update|delete|drop|create|alter)\s+',
            
            # Command injection
            r'[;&|`$(){}]',
            
            # Path traversal
            r'\.\./|\.\.\\\\'
        ]
        
        # File integrity tracking
        self._file_hashes: Dict[str, str] = {}
        
    def validate_content(
        self,
        content: str,
        document_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate content for security threats and compliance
        
        Args:
            content: Content to validate
            document_type: Type of document
            context: Additional validation context
            
        Returns:
            ValidationResult: Validation result with violations and sanitized content
        """
        config = self.config_manager.get_config()
        violations = []
        warnings = []
        sanitized_content = content
        
        # Check for sensitive data exposure
        sensitive_violations = self._check_sensitive_data(content, document_type)
        violations.extend(sensitive_violations)
        
        # Check for malicious content
        malicious_violations = self._check_malicious_content(content, document_type)
        violations.extend(malicious_violations)
        
        # Check document size limits
        size_violations = self._check_size_limits(content, document_type)
        violations.extend(size_violations)
        
        # Sanitize content if needed
        if config.sensitive_data_mask and sensitive_violations:
            sanitized_content = self._sanitize_content(content)
        
        # Check for compliance violations
        compliance_warnings = self._check_compliance(content, document_type)
        warnings.extend(compliance_warnings)
        
        # Log security events
        if violations:
            self._log_security_violations(violations, document_type, context)
        
        is_valid = len([v for v in violations if v.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            sanitized_content=sanitized_content,
            warnings=warnings
        )
    
    def validate_file_access(
        self,
        file_path: str,
        operation: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validate file access permissions and security
        
        Args:
            file_path: Path to file being accessed
            operation: Type of operation (read, write, delete)
            user_context: User context for access control
            
        Returns:
            bool: True if access is allowed
        """
        config = self.config_manager.get_config()
        
        if not config.access_logging:
            return True
        
        path = Path(file_path)
        
        # Check if file is within allowed directories
        allowed_paths = [
            config.base_path,
            config.backup_path,
            "memory-bank",
            "staging-memory-bank"
        ]
        
        is_allowed = any(
            str(path.resolve()).startswith(str(Path(allowed_path).resolve()))
            for allowed_path in allowed_paths
        )
        
        if not is_allowed:
            self._log_security_event(
                "unauthorized_file_access",
                {
                    'file_path': file_path,
                    'operation': operation,
                    'user_context': user_context,
                    'severity': SecurityLevel.HIGH.value
                }
            )
            return False
        
        # Log access for audit trail
        self.security_logger.info(
            "File access request",
            extra={
                'file_path': file_path,
                'operation': operation,
                'allowed': is_allowed,
                'user_context': user_context
            }
        )
        
        return is_allowed
    
    def validate_file_integrity(
        self,
        file_path: str,
        expected_hash: Optional[str] = None
    ) -> bool:
        """
        Validate file integrity using checksums
        
        Args:
            file_path: Path to file to validate
            expected_hash: Expected file hash (if known)
            
        Returns:
            bool: True if file integrity is valid
        """
        config = self.config_manager.get_config()
        
        if not config.integrity_checks:
            return True
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False
            
            # Calculate current file hash
            current_hash = self._calculate_file_hash(file_path)
            
            # Check against expected hash
            if expected_hash:
                if current_hash != expected_hash:
                    self._log_security_event(
                        "file_integrity_violation",
                        {
                            'file_path': file_path,
                            'expected_hash': expected_hash,
                            'actual_hash': current_hash,
                            'severity': SecurityLevel.HIGH.value
                        }
                    )
                    return False
            
            # Update tracked hash
            self._file_hashes[file_path] = current_hash
            
            return True
            
        except Exception as e:
            self.security_logger.error(
                "File integrity check failed",
                extra={
                    'file_path': file_path,
                    'error': str(e)
                }
            )
            return False
    
    def encrypt_content(self, content: str, key: Optional[str] = None) -> str:
        """
        Encrypt content for secure storage (simplified implementation)
        
        Args:
            content: Content to encrypt
            key: Encryption key (optional)
            
        Returns:
            str: Encrypted content
        """
        config = self.config_manager.get_config()
        
        if not config.encryption_enabled:
            return content
        
        # This is a simplified encryption - in production, use proper encryption
        try:
            import base64
            
            # Simple base64 encoding (NOT SECURE - use proper encryption in production)
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            return f"ENCRYPTED:{encoded_content}"
            
        except Exception as e:
            self.security_logger.error(
                "Content encryption failed",
                extra={'error': str(e)}
            )
            return content
    
    def decrypt_content(self, encrypted_content: str, key: Optional[str] = None) -> str:
        """
        Decrypt content from secure storage (simplified implementation)
        
        Args:
            encrypted_content: Encrypted content
            key: Decryption key (optional)
            
        Returns:
            str: Decrypted content
        """
        config = self.config_manager.get_config()
        
        if not config.encryption_enabled or not encrypted_content.startswith("ENCRYPTED:"):
            return encrypted_content
        
        try:
            import base64
            
            # Extract and decode content
            encoded_content = encrypted_content[10:]  # Remove "ENCRYPTED:" prefix
            decoded_content = base64.b64decode(encoded_content).decode('utf-8')
            return decoded_content
            
        except Exception as e:
            self.security_logger.error(
                "Content decryption failed",
                extra={'error': str(e)}
            )
            return encrypted_content
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security summary for the specified time period
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Dict containing security summary
        """
        # This would be implemented with actual security event storage
        return {
            'time_period_hours': hours,
            'total_violations': 0,
            'critical_violations': 0,
            'high_violations': 0,
            'medium_violations': 0,
            'low_violations': 0,
            'file_integrity_checks': len(self._file_hashes),
            'encryption_status': self.config_manager.get_config().encryption_enabled
        }
    
    def _check_sensitive_data(self, content: str, document_type: str) -> List[SecurityViolation]:
        """Check for sensitive data exposure"""
        violations = []
        
        for pattern in self._sensitive_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                violations.append(SecurityViolation(
                    threat_type=SecurityThreat.SENSITIVE_DATA_EXPOSURE,
                    severity=SecurityLevel.HIGH,
                    message=f"Sensitive data detected: {match.group(1) if match.groups() else 'pattern match'}",
                    document_type=document_type,
                    content_snippet=match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                ))
        
        return violations
    
    def _check_malicious_content(self, content: str, document_type: str) -> List[SecurityViolation]:
        """Check for malicious content patterns"""
        violations = []
        
        for pattern in self._malicious_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                violations.append(SecurityViolation(
                    threat_type=SecurityThreat.MALICIOUS_CONTENT,
                    severity=SecurityLevel.CRITICAL,
                    message=f"Malicious content detected: {pattern}",
                    document_type=document_type,
                    content_snippet=match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                ))
        
        return violations
    
    def _check_size_limits(self, content: str, document_type: str) -> List[SecurityViolation]:
        """Check document size limits"""
        violations = []
        config = self.config_manager.get_config()
        
        max_size = config.max_document_sizes.get(document_type, 50000)
        content_size = len(content.encode('utf-8'))
        
        if content_size > max_size:
            violations.append(SecurityViolation(
                threat_type=SecurityThreat.DATA_CORRUPTION,
                severity=SecurityLevel.MEDIUM,
                message=f"Document size {content_size} exceeds limit {max_size}",
                document_type=document_type
            ))
        
        return violations
    
    def _check_compliance(self, content: str, document_type: str) -> List[str]:
        """Check for compliance violations"""
        warnings = []
        
        # Check for proper markdown formatting
        if not content.strip().startswith('#'):
            warnings.append(f"Document {document_type} should start with a header")
        
        # Check for minimum content length
        if len(content.strip()) < 100:
            warnings.append(f"Document {document_type} may be too short for meaningful content")
        
        return warnings
    
    def _sanitize_content(self, content: str) -> str:
        """Sanitize content by masking sensitive data"""
        sanitized = content
        
        for pattern in self._sensitive_patterns:
            sanitized = re.sub(pattern, r'\1: [REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _log_security_violations(
        self,
        violations: List[SecurityViolation],
        document_type: str,
        context: Optional[Dict[str, Any]]
    ):
        """Log security violations"""
        for violation in violations:
            severity_map = {
                SecurityLevel.LOW: "info",
                SecurityLevel.MEDIUM: "warning", 
                SecurityLevel.HIGH: "error",
                SecurityLevel.CRITICAL: "critical"
            }
            
            log_level = severity_map.get(violation.severity, "warning")
            
            getattr(self.security_logger, log_level)(
                f"Security violation: {violation.message}",
                extra={
                    'threat_type': violation.threat_type.value,
                    'severity': violation.severity.value,
                    'document_type': document_type,
                    'content_snippet': violation.content_snippet,
                    'context': context
                }
            )
    
    def _log_security_event(self, event_type: str, data: Dict[str, Any]):
        """Log general security events"""
        self.security_logger.warning(
            f"Security event: {event_type}",
            extra={
                'event_type': event_type,
                **data
            }
        )


# Global security validator instance
_security_validator_instance: Optional[MemoryBankSecurityValidator] = None


def get_memory_bank_security_validator() -> MemoryBankSecurityValidator:
    """Get global Memory Bank security validator instance"""
    global _security_validator_instance
    
    if _security_validator_instance is None:
        _security_validator_instance = MemoryBankSecurityValidator()
    
    return _security_validator_instance 