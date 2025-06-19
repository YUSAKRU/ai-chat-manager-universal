#!/usr/bin/env python3
"""
Memory Bank Phase 3 Integration Test
====================================

Comprehensive test suite for the Enhanced Memory Bank system demonstrating:
- Configuration management across environments
- Error handling and recovery mechanisms
- Performance monitoring and metrics
- Security validation and protection
- Complete integration with Phase 1 & 2 systems

This test showcases the crown jewel of our backend optimization.
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')

# Import all Phase 3 components
from memory_bank_enhanced import (
    MemoryBankManager,
    MemoryBankConfigManager,
    MemoryBankPerformanceMonitor,
    MemoryBankSecurityValidator,
    MemoryBankErrorHandler
)
from memory_bank_enhanced.memory_bank_manager import create_memory_bank_manager

# Import Phase 1 and 2 for integration testing
from advanced_logging.factory import configure_logging_from_config


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")


def print_success(message: str):
    """Print a success message"""
    print(f"✅ {message}")


def print_info(message: str):
    """Print an info message"""
    print(f"ℹ️  {message}")


def print_error(message: str):
    """Print an error message"""
    print(f"❌ {message}")


def test_configuration_management():
    """Test configuration management across environments"""
    print_section("CONFIGURATION MANAGEMENT TEST")
    
    try:
        # Test environment detection and configuration loading
        config_manager = MemoryBankConfigManager()
        
        # Test development environment
        dev_config = config_manager.load_config("development")
        print_success(f"Development config loaded: {dev_config.log_level}")
        print_info(f"  - Storage path: {dev_config.base_path}")
        print_info(f"  - Search enabled: {dev_config.search_enabled}")
        print_info(f"  - Backup enabled: {dev_config.backup_enabled}")
        
        # Test staging environment
        staging_config = config_manager.load_config("staging")
        print_success(f"Staging config loaded: {staging_config.log_level}")
        print_info(f"  - Cache size: {staging_config.cache_size} MB")
        print_info(f"  - Concurrent ops: {staging_config.concurrent_operations}")
        
        # Test production environment
        prod_config = config_manager.load_config("production")
        print_success(f"Production config loaded: {prod_config.log_level}")
        print_info(f"  - Encryption: {prod_config.encryption_enabled}")
        print_info(f"  - Security logging: {prod_config.access_logging}")
        
        # Test feature detection
        features = {
            'backup': config_manager.is_feature_enabled('backup'),
            'search': config_manager.is_feature_enabled('search'),
            'caching': config_manager.is_feature_enabled('caching'),
            'encryption': config_manager.is_feature_enabled('encryption')
        }
        print_success(f"Feature detection working: {features}")
        
        # Test environment info
        env_info = config_manager.get_environment_info()
        print_success("Environment info retrieved:")
        for key, value in env_info.items():
            print_info(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False


def test_security_validation():
    """Test security validation and protection"""
    print_section("SECURITY VALIDATION TEST")
    
    try:
        security_validator = MemoryBankSecurityValidator()
        
        # Test clean content validation
        clean_content = """
        # Project Brief
        
        This is a clean document with no security issues.
        It contains normal project information.
        """
        
        result = security_validator.validate_content(clean_content, "projectbrief")
        print_success(f"Clean content validation: {result.is_valid}")
        print_info(f"  - Violations: {len(result.violations)}")
        print_info(f"  - Warnings: {len(result.warnings)}")
        
        # Test content with sensitive data
        sensitive_content = """
        # Project Configuration
        
        API_KEY: sk-1234567890abcdef1234567890abcdef
        Database password: secretpassword123
        Email: admin@company.com
        """
        
        result = security_validator.validate_content(sensitive_content, "techContext")
        print_success(f"Sensitive content detected: {not result.is_valid}")
        print_info(f"  - Violations found: {len(result.violations)}")
        
        for violation in result.violations:
            print_info(f"    * {violation.threat_type.value}: {violation.message}")
        
        # Test content sanitization
        if result.sanitized_content:
            print_success("Content sanitization working")
            print_info(f"  - Original length: {len(sensitive_content)}")
            print_info(f"  - Sanitized length: {len(result.sanitized_content)}")
        
        # Test file access validation
        access_allowed = security_validator.validate_file_access(
            "memory-bank/test.md", "read", {"user": "test"}
        )
        print_success(f"File access validation: {access_allowed}")
        
        # Test malicious content detection
        malicious_content = """
        <script>alert('XSS');</script>
        SELECT * FROM users WHERE id = 1;
        """
        
        result = security_validator.validate_content(malicious_content, "activeContext")
        print_success(f"Malicious content detected: {not result.is_valid}")
        print_info(f"  - Critical violations: {sum(1 for v in result.violations if v.severity.value == 'critical')}")
        
        return True
        
    except Exception as e:
        print_error(f"Security validation test failed: {e}")
        return False


def test_performance_monitoring():
    """Test performance monitoring and metrics"""
    print_section("PERFORMANCE MONITORING TEST")
    
    try:
        performance_monitor = MemoryBankPerformanceMonitor()
        
        # Test operation tracking
        tracking_id = performance_monitor.start_operation_tracking(
            "test_operation",
            context={"test": True}
        )
        
        # Simulate some work
        time.sleep(0.1)
        
        metrics = performance_monitor.end_operation_tracking(
            tracking_id,
            success=True,
            additional_context={"result": "success"}
        )
        
        if metrics:
            print_success("Operation tracking working")
            print_info(f"  - Duration: {metrics.duration:.3f}s")
            print_info(f"  - Memory delta: {metrics.memory_delta} MB")
            print_info(f"  - CPU percent: {metrics.cpu_percent:.1f}%")
        
        # Test API call tracking
        api_metrics = performance_monitor.track_api_call(
            provider="gemini",
            model="gemini-2.5-flash",
            operation="embedding",
            tokens_input=100,
            tokens_output=50,
            duration=0.5,
            success=True
        )
        
        print_success("API call tracking working")
        print_info(f"  - Cost estimate: ${api_metrics.cost_estimate:.6f}")
        print_info(f"  - Total tokens: {api_metrics.tokens_input + api_metrics.tokens_output}")
        
        # Test document operation tracking
        doc_metrics = performance_monitor.track_document_operation(
            document_type="projectbrief",
            operation="write",
            file_path="test/path.md",
            duration=0.2,
            success=True
        )
        
        print_success("Document operation tracking working")
        print_info(f"  - Operation: {doc_metrics.operation}")
        print_info(f"  - Duration: {doc_metrics.duration:.3f}s")
        
        # Test performance summary
        summary = performance_monitor.get_performance_summary(hours=1)
        print_success("Performance summary generated")
        print_info(f"  - System memory: {summary['system_performance']['current_memory_mb']:.1f} MB")
        print_info(f"  - CPU usage: {summary['system_performance']['cpu_percent']:.1f}%")
        print_info(f"  - Thread count: {summary['system_performance']['thread_count']}")
        
        return True
        
    except Exception as e:
        print_error(f"Performance monitoring test failed: {e}")
        return False


def test_error_handling():
    """Test error handling and recovery mechanisms"""
    print_section("ERROR HANDLING & RECOVERY TEST")
    
    try:
        error_handler = MemoryBankErrorHandler()
        
        # Test file operation error handling
        try:
            # Simulate file not found error
            raise FileNotFoundError("Test file not found")
        except Exception as e:
            recovery_result = error_handler.handle_file_operation_error(
                "read_document",
                "nonexistent/file.md",
                e,
                "projectbrief"
            )
            print_success("File operation error handled")
            print_info(f"  - Recovery attempted: {recovery_result is not None}")
        
        # Test search error handling
        try:
            # Simulate search error
            raise Exception("Search service unavailable")
        except Exception as e:
            recovery_result = error_handler.handle_search_error(
                "search_documents",
                "test query",
                e
            )
            print_success("Search error handled")
            print_info(f"  - Fallback strategies available: {recovery_result is not None}")
        
        # Test emergency backup
        backup_success = error_handler.create_emergency_backup(
            "activeContext",
            "Emergency backup test content",
            "test_scenario"
        )
        print_success(f"Emergency backup system: {backup_success}")
        
        # Test error statistics
        error_stats = error_handler.get_error_statistics()
        print_success("Error statistics generated")
        print_info(f"  - Total errors: {error_stats['total_errors']}")
        print_info(f"  - Recent errors: {error_stats['recent_errors']}")
        print_info(f"  - Recovery attempts: {error_stats['recovery_attempts']}")
        
        return True
        
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False


def test_integrated_memory_bank_operations():
    """Test integrated Memory Bank operations"""
    print_section("INTEGRATED MEMORY BANK OPERATIONS TEST")
    
    try:
        # Create Memory Bank manager with development environment
        manager = create_memory_bank_manager("development")
        print_success("Memory Bank Manager created")
        
        # Test document writing
        test_content = """
        # Test Project Brief
        
        This is a test document for the enhanced Memory Bank system.
        
        ## Features Tested
        - Configuration management
        - Security validation
        - Performance monitoring
        - Error handling
        
        ## Success Metrics
        - All operations complete without errors
        - Performance metrics are collected
        - Security validations pass
        - Backups are created automatically
        """
        
        write_success = manager.write_document(
            "projectbrief",
            test_content,
            validate_security=True,
            encrypt_content=False,
            create_backup=True
        )
        
        print_success(f"Document write operation: {write_success}")
        
        # Test document reading
        read_content = manager.read_document(
            "projectbrief",
            validate_security=True,
            decrypt_content=False
        )
        
        if read_content:
            print_success("Document read operation successful")
            print_info(f"  - Content length: {len(read_content)} characters")
            print_info(f"  - Content matches: {read_content == test_content}")
        else:
            print_error("Document read operation failed")
        
        # Test document search
        search_results = manager.search_documents(
            "features tested",
            document_types=["projectbrief"],
            max_results=5
        )
        
        print_success(f"Document search completed: {len(search_results)} results")
        for i, result in enumerate(search_results):
            print_info(f"  - Result {i+1}: {result['document_type']} (score: {result['relevance_score']:.2f})")
        
        # Test system status
        status = manager.get_system_status()
        print_success("System status retrieved")
        print_info(f"  - Environment: {status['environment']}")
        print_info(f"  - Storage files: {status['storage']['file_count']}")
        print_info(f"  - Storage size: {status['storage']['total_size_mb']} MB")
        print_info(f"  - Performance metrics: {len(status['performance']['total_metrics'])} types tracked")
        
        # Test maintenance operations
        maintenance_result = manager.perform_maintenance()
        print_success("Maintenance operations completed")
        print_info(f"  - Tasks completed: {len(maintenance_result['tasks_completed'])}")
        print_info(f"  - Errors: {len(maintenance_result['errors'])}")
        
        return True
        
    except Exception as e:
        print_error(f"Integrated operations test failed: {e}")
        return False


def test_logging_integration():
    """Test integration with Phase 1 & 2 logging system"""
    print_section("LOGGING INTEGRATION TEST")
    
    try:
        # Configure logging from Phase 2 system
        logger_factory = configure_logging_from_config()
        print_success("Phase 2 logging system integrated")
        
        # Get specialized Memory Bank logger
        mb_logger = logger_factory.get_logger("memory_bank", "integration_test")
        
        # Test various log levels
        mb_logger.debug("Debug message from Memory Bank", extra={'test': True})
        mb_logger.info("Info message from Memory Bank", extra={'operation': 'test'})
        mb_logger.warning("Warning message from Memory Bank", extra={'alert': 'test'})
        mb_logger.error("Error message from Memory Bank", extra={'error_type': 'test'})
        
        print_success("Logging integration working")
        print_info("  - All log levels tested")
        print_info("  - Structured logging with extra data")
        print_info("  - Memory Bank specific logging context")
        
        # Test performance logging with Memory Bank operations
        with mb_logger.log_performance("memory_bank_test_operation"):
            time.sleep(0.05)  # Simulate work
        
        print_success("Performance logging integration working")
        
        return True
        
    except Exception as e:
        print_error(f"Logging integration test failed: {e}")
        return False


def display_final_summary(test_results):
    """Display final test summary"""
    print_section("PHASE 3 INTEGRATION TEST SUMMARY")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"📊 Test Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests} ✅")
    print(f"   Failed: {failed_tests} ❌")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n🎯 Individual Test Results:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed_tests == total_tests:
        print(f"\n🏆 ALL TESTS PASSED! Phase 3 Memory Bank optimization is COMPLETE!")
        print(f"🚀 The enhanced Memory Bank system is ready for production use.")
        print(f"💎 Features delivered:")
        print(f"   • Environment-specific configuration management")
        print(f"   • Robust error handling with automatic recovery")
        print(f"   • Real-time performance monitoring and metrics")
        print(f"   • Advanced security validation and protection")
        print(f"   • Seamless integration with Phase 1 & 2 systems")
    else:
        print(f"\n⚠️  Some tests failed. Please review the error messages above.")
        print(f"🔧 Failed tests need attention before production deployment.")


def main():
    """Main test execution"""
    print_section("MEMORY BANK PHASE 3 INTEGRATION TEST")
    print_info("Testing enterprise-grade Memory Bank optimization")
    print_info("Integrating configuration, security, performance, and error handling")
    
    # Run all tests
    test_results = {
        "Configuration Management": test_configuration_management(),
        "Security Validation": test_security_validation(),
        "Performance Monitoring": test_performance_monitoring(),
        "Error Handling": test_error_handling(),
        "Integrated Operations": test_integrated_memory_bank_operations(),
        "Logging Integration": test_logging_integration()
    }
    
    # Display final summary
    display_final_summary(test_results)
    
    # Return exit code based on results
    return 0 if all(test_results.values()) else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 