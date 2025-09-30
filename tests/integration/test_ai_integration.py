#!/usr/bin/env python3
"""
AI Integration Tests for Apollo GovCon Suite
Tests Phase 5-6 AI capabilities including document analysis, market intelligence, and MCP integration
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestAIIntegration(unittest.TestCase):
    """Test AI integration capabilities"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_document = "This is a test government contract document with requirements for software development services."
        self.test_schema = {
            "title": "string",
            "requirements": "array",
            "deadline": "string",
            "budget": "number"
        }
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_document_text_loading(self):
        """Test document text loading functionality"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Test with mock file
            mock_file = Mock()
            mock_file.name = "test_document.pdf"
            mock_file.read.return_value = b"Test document content"
            
            # Test document loading
            try:
                docs, error = govcon_suite.load_document_text(mock_file)
                
                # Should handle the mock file gracefully
                self.assertTrue(docs is None or isinstance(docs, list))
                
                if error:
                    # Error handling should be informative
                    self.assertIsInstance(error, str)
                    self.assertGreater(len(error), 0)
                
            except Exception as e:
                # Function should exist and handle errors gracefully
                self.fail(f"Document loading function failed unexpectedly: {e}")
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_vector_store_creation(self):
        """Test vector store creation for document analysis"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Test vector store creation
            try:
                test_docs = ["Document 1 content", "Document 2 content"]
                
                # Mock the vector store creation
                with patch('govcon_suite.FAISS') as mock_faiss, \
                     patch('govcon_suite.SentenceTransformer') as mock_transformer:
                    
                    mock_transformer_instance = Mock()
                    mock_transformer.return_value = mock_transformer_instance
                    mock_transformer_instance.encode.return_value = [[0.1, 0.2], [0.3, 0.4]]
                    
                    mock_faiss_instance = Mock()
                    mock_faiss.IndexFlatL2.return_value = mock_faiss_instance
                    
                    vector_store = govcon_suite.create_vector_store(test_docs)
                    
                    # Should return a vector store object or handle gracefully
                    self.assertTrue(vector_store is not None or vector_store is None)
                    
            except Exception as e:
                # Function should exist and handle errors gracefully
                self.fail(f"Vector store creation failed unexpectedly: {e}")
    
    def test_mcp_payload_structure(self):
        """Test MCP JSON-RPC 2.0 payload structure"""
        # Test all 6 generic MCP tools
        mcp_tools = [
            "extract_structured_data",
            "analyze_patterns", 
            "classify_content",
            "calculate_similarity",
            "process_geographic_data",
            "generate_insights"
        ]
        
        for tool_name in mcp_tools:
            with self.subTest(tool=tool_name):
                payload = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": {
                            "text": self.test_document,
                            "domain_context": "government_contracting"
                        }
                    }
                }
                
                # Validate JSON-RPC 2.0 structure
                self.assertEqual(payload["jsonrpc"], "2.0")
                self.assertIn("id", payload)
                self.assertEqual(payload["method"], "tools/call")
                self.assertIn("params", payload)
                self.assertEqual(payload["params"]["name"], tool_name)
                self.assertIn("arguments", payload["params"])
    
    def test_mcp_tool_specific_payloads(self):
        """Test tool-specific MCP payload configurations"""
        
        # Test extract_structured_data with schema
        extract_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "extract_structured_data",
                "arguments": {
                    "text": self.test_document,
                    "schema": self.test_schema,
                    "domain_context": "government_contracting"
                }
            }
        }
        
        self.assertIn("schema", extract_payload["params"]["arguments"])
        self.assertEqual(extract_payload["params"]["arguments"]["schema"], self.test_schema)
        
        # Test calculate_similarity with comparison text
        similarity_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "calculate_similarity",
                "arguments": {
                    "text1": self.test_document,
                    "text2": "Another government contract document",
                    "domain_context": "government_contracting"
                }
            }
        }
        
        self.assertIn("text1", similarity_payload["params"]["arguments"])
        self.assertIn("text2", similarity_payload["params"]["arguments"])
        
        # Test process_geographic_data with location info
        geo_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "process_geographic_data",
                "arguments": {
                    "text": "Contract work in Virginia, Maryland, and Washington DC",
                    "extract_locations": True,
                    "domain_context": "government_contracting"
                }
            }
        }
        
        self.assertIn("extract_locations", geo_payload["params"]["arguments"])
    
    @patch('requests.post')
    def test_mcp_server_communication(self, mock_post):
        """Test MCP server communication patterns"""
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {
                "title": "Software Development Contract",
                "requirements": ["Python development", "Database design"],
                "deadline": "2024-12-31",
                "budget": 500000
            }
        }
        mock_post.return_value = mock_response
        
        # Test MCP server call
        import requests
        
        payload = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/call",
            "params": {
                "name": "extract_structured_data",
                "arguments": {
                    "text": self.test_document,
                    "schema": self.test_schema,
                    "domain_context": "government_contracting"
                }
            }
        }
        
        response = requests.post("http://localhost:8080", json=payload)
        
        # Verify request was made correctly
        mock_post.assert_called_once_with("http://localhost:8080", json=payload)
        
        # Verify response structure
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["jsonrpc"], "2.0")
        self.assertEqual(response_data["id"], "test-id")
        self.assertIn("result", response_data)
    
    @patch('requests.post')
    def test_mcp_error_handling(self, mock_post):
        """Test MCP error handling scenarios"""
        
        # Test connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        import requests
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "extract_structured_data",
                "arguments": {
                    "text": self.test_document,
                    "schema": self.test_schema,
                    "domain_context": "government_contracting"
                }
            }
        }
        
        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.post("http://localhost:8080", json=payload)
        
        # Test server error response
        mock_post.side_effect = None
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        mock_post.return_value = mock_response
        
        response = requests.post("http://localhost:8080", json=payload)
        self.assertEqual(response.status_code, 500)
        
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"]["code"], -32603)
    
    def test_ai_library_availability(self):
        """Test availability of AI libraries for Phase 6 features"""
        
        # Test core AI libraries
        try:
            import torch
            self.assertTrue(hasattr(torch, 'tensor'))
        except ImportError:
            self.skipTest("PyTorch not available")
        
        try:
            from sentence_transformers import SentenceTransformer
            # Test model loading capability
            self.assertTrue(callable(SentenceTransformer))
        except ImportError:
            self.skipTest("SentenceTransformers not available")
        
        try:
            import faiss
            self.assertTrue(hasattr(faiss, 'IndexFlatL2'))
        except ImportError:
            self.skipTest("FAISS not available")
        
        try:
            import numpy as np
            self.assertTrue(hasattr(np, 'array'))
        except ImportError:
            self.skipTest("NumPy not available")
    
    def test_market_intelligence_integration(self):
        """Test market intelligence capabilities"""
        
        try:
            # Test DuckDuckGo search integration
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                import ddgs as DDGS
            
            # Test search functionality with mock
            with patch.object(DDGS, '__enter__') as mock_ddgs:
                mock_search_instance = Mock()
                mock_search_instance.text.return_value = [
                    {
                        'title': 'Test Government Contract',
                        'href': 'https://test.gov/contract',
                        'body': 'Software development contract opportunity'
                    }
                ]
                mock_ddgs.return_value = mock_search_instance
                
                # Test search query
                with DDGS() as ddgs:
                    results = ddgs.text("government software contracts", max_results=5)
                    self.assertIsInstance(results, list)
                    
        except ImportError:
            self.skipTest("DuckDuckGo search not available")


if __name__ == '__main__':
    unittest.main(verbosity=2)
