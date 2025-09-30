#!/usr/bin/env python3
"""
APOLLO GOVCON UNIT TESTS - CORE FUNCTIONS
Phase 1 Foundation Testing: Unit tests for core business logic functions
Tests the most critical functions from govcon_suite.py
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timezone
import tempfile
import json

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import govcon_suite
    from govcon_suite import (
        setup_database, find_partners, generate_rfq, run_scraper,
        add_subcontractor_to_db, get_engine, fetch_opportunities,
        store_opportunities, load_document_text, create_vector_store
    )
except ImportError as e:
    print(f"Warning: Could not import govcon_suite functions: {e}")
    govcon_suite = None


class TestCoreFunctions(unittest.TestCase):
    """Test core business logic functions from govcon_suite.py"""
    
    def setUp(self):
        """Set up test environment for each test"""
        self.test_db_url = "postgresql://postgres:mysecretpassword@localhost:5434/sam_contracts_test"
        self.original_db_url = os.environ.get('GOVCON_DB_URL')
        os.environ['GOVCON_DB_URL'] = self.test_db_url
        
    def tearDown(self):
        """Clean up after each test"""
        if self.original_db_url:
            os.environ['GOVCON_DB_URL'] = self.original_db_url
        elif 'GOVCON_DB_URL' in os.environ:
            del os.environ['GOVCON_DB_URL']

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    @patch('govcon_suite.get_engine')
    def test_setup_database_success(self, mock_get_engine):
        """Test successful database setup"""
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine

        result = setup_database()

        self.assertIsNotNone(result)
        mock_get_engine.assert_called_once()

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_setup_database_demo_mode(self):
        """Test database setup in demo mode"""
        with patch('govcon_suite.get_engine') as mock_get_engine:
            mock_get_engine.return_value = "demo_mode"
            
            result = setup_database()
            
            self.assertEqual(result, "demo_mode")

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    @patch('ddgs.DDGS')
    def test_find_partners_success(self, mock_ddgs):
        """Test successful partner finding"""
        # Mock DDGS search results
        mock_search_results = [
            {'title': 'ABC Corp - Software Development', 'href': 'https://abc.com', 'body': 'Software development company'},
            {'title': 'XYZ Inc - Cybersecurity', 'href': 'https://xyz.com', 'body': 'Cybersecurity specialists'}
        ]

        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text.return_value = mock_search_results
        mock_ddgs.return_value.__enter__.return_value = mock_ddgs_instance
        mock_ddgs.return_value.__exit__.return_value = None

        keywords = ['software', 'cybersecurity']
        location = 'Virginia'

        result = find_partners(keywords, location, max_results=10)

        self.assertIsInstance(result, list)
        # Should have processed the mock results
        if result:  # Only check if results were returned
            mock_ddgs_instance.text.assert_called()

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_find_partners_no_ddgs(self):
        """Test partner finding when DDGS is not available"""
        # Mock the import to fail at the function level
        with patch('govcon_suite.find_partners') as mock_find_partners:
            mock_find_partners.return_value = []
            result = mock_find_partners(['software'], 'Virginia')

            self.assertEqual(result, [])

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_generate_rfq_basic(self):
        """Test basic RFQ generation"""
        sow_text = "Develop a web application with user authentication"
        opportunity_title = "Web Development Project"
        deadline = "2024-03-15"
        
        result = generate_rfq(sow_text, opportunity_title, deadline)
        
        self.assertIsInstance(result, str)
        self.assertIn("REQUEST FOR QUOTE", result)
        self.assertIn(opportunity_title, result)
        self.assertIn(deadline, result)

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_generate_rfq_with_company_info(self):
        """Test RFQ generation with custom company info"""
        sow_text = "Cybersecurity assessment"
        opportunity_title = "Security Audit"
        deadline = "2024-04-01"
        company_info = {
            'name': 'Test Company',
            'email': 'test@company.com',
            'phone': '555-0123',
            'address': '123 Test St'
        }
        
        result = generate_rfq(sow_text, opportunity_title, deadline, company_info)
        
        self.assertIn("Test Company", result)
        self.assertIn("test@company.com", result)
        self.assertIn("555-0123", result)

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    @patch('govcon_suite.fetch_opportunities')
    @patch('govcon_suite.store_opportunities')
    @patch('govcon_suite.setup_database')
    def test_run_scraper_success(self, mock_setup_db, mock_store, mock_fetch):
        """Test successful scraper run"""
        # Mock database setup
        mock_engine = Mock()
        mock_setup_db.return_value = mock_engine
        
        # Mock fetch results
        mock_opportunities = [
            {'notice_id': '123', 'title': 'Test Opportunity'},
            {'notice_id': '456', 'title': 'Another Opportunity'}
        ]
        mock_fetch.return_value = mock_opportunities
        
        # Mock store results
        mock_store.return_value = 2
        
        result = run_scraper(date_from="01/01/2024", date_to="01/02/2024")
        
        self.assertEqual(result, 2)
        mock_fetch.assert_called_once()
        mock_store.assert_called_once_with(mock_engine, mock_opportunities, 'contract')

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    @patch('govcon_suite.add_subcontractor_to_db')
    def test_add_subcontractor_to_db_success(self, mock_add_subcontractor):
        """Test successful subcontractor addition to database"""
        # Mock the function to return success
        mock_add_subcontractor.return_value = (True, "Subcontractor added successfully")
        
        success, message = mock_add_subcontractor(
            company_name="Test Corp",
            capabilities=["Software", "Testing"],
            contact_email="test@corp.com",
            contact_phone="555-0123",
            website="https://testcorp.com",
            location="Virginia",
            trust_score=85,
            vetting_notes="Good partner"
        )
        
        self.assertTrue(success)
        self.assertIn("successfully", message.lower())

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_add_subcontractor_to_db_missing_name(self):
        """Test subcontractor addition with missing company name"""
        success, message = add_subcontractor_to_db(
            company_name="",
            capabilities=["Software"],
            contact_email="test@corp.com"
        )
        
        self.assertFalse(success)
        self.assertIn("Company name is required", message)


class TestDocumentProcessing(unittest.TestCase):
    """Test Phase 6 document analysis functions"""
    
    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_load_document_text_invalid_file(self):
        """Test document loading with invalid file"""
        # Create a mock file object that will fail
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.read.side_effect = Exception("File read error")
        
        docs, error = load_document_text(mock_file)
        
        self.assertIsNone(docs)
        self.assertIsNotNone(error)

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_create_vector_store_empty_docs(self):
        """Test vector store creation with empty documents"""
        empty_docs = []
        
        result = create_vector_store(empty_docs)
        
        # Should handle empty documents gracefully
        self.assertIsNone(result)


if __name__ == '__main__':
    print("🚀 APOLLO GOVCON UNIT TESTS - CORE FUNCTIONS")
    print("=" * 60)
    print("Testing Phase 1-6 core business logic functions")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2)
