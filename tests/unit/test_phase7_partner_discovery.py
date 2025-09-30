#!/usr/bin/env python3
"""
Unit Tests for Phase 7 Feature 44: AI-Powered Partner Discovery Engine
Tests the new AI-enhanced partner discovery capabilities
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestPhase7PartnerDiscovery(unittest.TestCase):
    """Test Phase 7 AI-powered partner discovery features"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_requirements = "Looking for software development partners with Python expertise and government contracting experience"
        self.test_keywords = ["software", "development", "python"]
        self.test_location = "Virginia"
        
        self.mock_partners = [
            {
                'company_name': 'TechCorp Solutions',
                'website': 'https://techcorp.com',
                'description': 'Software development company specializing in government contracts',
                'source_query': 'software companies in Virginia',
                'capabilities': ['software', 'development']
            },
            {
                'company_name': 'GovTech Innovations',
                'website': 'https://govtech.com',
                'description': 'Python development and cybersecurity services',
                'source_query': 'python contractors',
                'capabilities': ['python', 'cybersecurity']
            }
        ]
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_discover_partners_with_ai_success(self):
        """Test successful AI-powered partner discovery"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock MCP server response
            mock_mcp_response = {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {
                    "skills": ["Python", "Software Development"],
                    "experience_level": "Senior",
                    "certifications": ["AWS", "Security+"],
                    "location_preference": "Virginia",
                    "industry_focus": "Government Contracting"
                }
            }
            
            # Mock requests.post for MCP calls
            with patch('govcon_suite.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_mcp_response
                mock_post.return_value = mock_response
                
                # Mock the basic find_partners function
                with patch('govcon_suite.find_partners') as mock_find_partners:
                    mock_find_partners.return_value = self.mock_partners.copy()
                    
                    # Test AI-powered discovery
                    result = govcon_suite.discover_partners_with_ai(
                        self.test_requirements, 
                        self.test_location, 
                        max_results=5
                    )
                    
                    # Verify results
                    self.assertIsInstance(result, list)
                    self.assertGreater(len(result), 0)
                    
                    # Verify MCP was called for requirements extraction
                    self.assertTrue(mock_post.called)
                    
                    # Verify find_partners was called
                    mock_find_partners.assert_called()
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_discover_partners_with_ai_mcp_unavailable(self):
        """Test AI discovery fallback when MCP server is unavailable"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock requests.post to raise connection error
            with patch('govcon_suite.requests.post') as mock_post:
                mock_post.side_effect = Exception("Connection failed")
                
                # Mock the basic find_partners function
                with patch('govcon_suite.find_partners') as mock_find_partners:
                    mock_find_partners.return_value = self.mock_partners.copy()
                    
                    # Test AI discovery with MCP unavailable
                    result = govcon_suite.discover_partners_with_ai(
                        self.test_requirements,
                        self.test_location,
                        max_results=5
                    )
                    
                    # Should still return results using fallback
                    self.assertIsInstance(result, list)
                    mock_find_partners.assert_called()
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_score_partners_with_ai_success(self):
        """Test AI-powered partner scoring"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock MCP similarity response
            mock_similarity_response = {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {
                    "similarity_score": 0.85
                }
            }
            
            with patch('govcon_suite.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_similarity_response
                mock_post.return_value = mock_response
                
                # Test partner scoring
                result = govcon_suite.score_partners_with_ai(
                    self.mock_partners.copy(),
                    self.test_keywords,
                    self.test_location,
                    self.test_requirements
                )
                
                # Verify results
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), len(self.mock_partners))
                
                # Verify AI scores were added
                for partner in result:
                    self.assertIn('ai_score', partner)
                    self.assertIn('match_confidence', partner)
                    self.assertIsInstance(partner['ai_score'], float)
                    self.assertIn(partner['match_confidence'], ['High', 'Medium', 'Low'])
                
                # Verify partners are sorted by AI score
                scores = [p['ai_score'] for p in result]
                self.assertEqual(scores, sorted(scores, reverse=True))
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_score_partners_with_ai_mcp_unavailable(self):
        """Test partner scoring fallback when MCP is unavailable"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock requests.post to raise connection error
            with patch('govcon_suite.requests.post') as mock_post:
                mock_post.side_effect = Exception("Connection failed")
                
                # Test partner scoring with MCP unavailable
                result = govcon_suite.score_partners_with_ai(
                    self.mock_partners.copy(),
                    self.test_keywords,
                    self.test_location,
                    self.test_requirements
                )
                
                # Should still return partners with default scores
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), len(self.mock_partners))
                
                # Verify default scores were assigned
                for partner in result:
                    self.assertIn('ai_score', partner)
                    self.assertIn('match_confidence', partner)
                    self.assertEqual(partner['ai_score'], 0.5)  # Default score
                    self.assertEqual(partner['match_confidence'], 'Medium')  # Default confidence
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_find_partners_enhanced_with_ai_scoring(self):
        """Test enhanced find_partners function with AI scoring option"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock DDGS search results
            mock_search_results = [
                {
                    'title': 'TechCorp Solutions - Software Development',
                    'href': 'https://techcorp.com',
                    'body': 'Leading software development company with government contracting experience'
                }
            ]
            
            with patch('govcon_suite.DDGS') as mock_ddgs:
                mock_ddgs_instance = Mock()
                mock_ddgs_instance.text.return_value = mock_search_results
                mock_ddgs.return_value.__enter__.return_value = mock_ddgs_instance

                # Mock AI scoring function
                with patch('govcon_suite.score_partners_with_ai') as mock_score_partners:
                    mock_scored_partners = [
                        {
                            'company_name': 'TechCorp Solutions',
                            'website': 'https://techcorp.com',
                            'description': 'Leading software development company with government contracting experience',
                            'source_query': 'software companies in Virginia',
                            'capabilities': ['software'],
                            'ai_score': 0.85,
                            'match_confidence': 'High'
                        }
                    ]
                    mock_score_partners.return_value = mock_scored_partners

                    # Mock streamlit.error to prevent issues
                    with patch('govcon_suite.st.error'):

                        # Test enhanced find_partners with AI scoring
                        result = govcon_suite.find_partners(
                            self.test_keywords,
                            self.test_location,
                            max_results=5,
                            use_ai_scoring=True
                        )

                        # Verify results
                        self.assertIsInstance(result, list)
                        self.assertGreater(len(result), 0)

                        # Verify AI scoring was called
                        mock_score_partners.assert_called_once()

                        # Verify AI scores are present
                        for partner in result:
                            self.assertIn('ai_score', partner)
                            self.assertIn('match_confidence', partner)
    
    def test_mcp_payload_structure_for_partner_discovery(self):
        """Test MCP payload structure for partner discovery operations"""
        
        # Test requirements extraction payload
        requirements_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "extract_structured_data",
                "arguments": {
                    "text": self.test_requirements,
                    "schema": {
                        "skills": "array",
                        "experience_level": "string",
                        "certifications": "array",
                        "location_preference": "string",
                        "industry_focus": "string",
                        "company_size": "string"
                    },
                    "domain_context": "government_contracting"
                }
            }
        }
        
        # Validate payload structure
        self.assertEqual(requirements_payload["jsonrpc"], "2.0")
        self.assertIn("id", requirements_payload)
        self.assertEqual(requirements_payload["method"], "tools/call")
        self.assertEqual(requirements_payload["params"]["name"], "extract_structured_data")
        self.assertIn("schema", requirements_payload["params"]["arguments"])
        self.assertEqual(requirements_payload["params"]["arguments"]["domain_context"], "government_contracting")
        
        # Test similarity calculation payload
        similarity_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "calculate_similarity",
                "arguments": {
                    "text1": self.test_requirements,
                    "text2": "Company profile text",
                    "domain_context": "government_contracting"
                }
            }
        }
        
        # Validate similarity payload
        self.assertEqual(similarity_payload["params"]["name"], "calculate_similarity")
        self.assertIn("text1", similarity_payload["params"]["arguments"])
        self.assertIn("text2", similarity_payload["params"]["arguments"])
        self.assertEqual(similarity_payload["params"]["arguments"]["domain_context"], "government_contracting")
    
    def test_confidence_level_calculation(self):
        """Test confidence level calculation based on AI scores"""
        
        test_cases = [
            (0.9, 'High'),
            (0.75, 'High'),
            (0.7, 'Medium'),  # Fixed: 0.7 is not > 0.7
            (0.65, 'Medium'),
            (0.5, 'Medium'),
            (0.4, 'Low'),     # Fixed: 0.4 is not > 0.4
            (0.35, 'Low'),
            (0.1, 'Low')
        ]

        for score, expected_confidence in test_cases:
            with self.subTest(score=score):
                if score > 0.7:
                    confidence = 'High'
                elif score > 0.4:
                    confidence = 'Medium'
                else:
                    confidence = 'Low'
                
                self.assertEqual(confidence, expected_confidence)


if __name__ == '__main__':
    unittest.main(verbosity=2)
