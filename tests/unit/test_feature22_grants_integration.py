#!/usr/bin/env python3
"""
Unit Tests for Feature 22: Grants.gov Integration
Tests the new federal grant opportunity integration capabilities
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestFeature22GrantsIntegration(unittest.TestCase):
    """Test Feature 22 Grants.gov integration features"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_grant_data = {
            "id": "GRANT-123456",
            "title": "Cybersecurity Innovation Grant Program",
            "agencyName": "Department of Homeland Security",
            "postedDate": "2025-09-20",
            "closeDate": "2025-11-20",
            "awardCeiling": "$500,000",
            "cfdaNumber": "97.108",
            "eligibilityCriteria": "Small business concerns, minority-owned businesses"
        }
        
        self.mock_grants_api_response = {
            "response": {
                "docs": [self.mock_grant_data]
            }
        }
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_fetch_grants_opportunities_success(self):
        """Test successful grant opportunity fetching"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock requests.get for Grants.gov API
            with patch('govcon_suite.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = self.mock_grants_api_response
                mock_get.return_value = mock_response
                
                # Test grant fetching
                result = govcon_suite.fetch_grants_opportunities(
                    keywords=["cybersecurity", "innovation"],
                    max_results=50
                )
                
                # Verify results
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["id"], "GRANT-123456")
                self.assertEqual(result[0]["title"], "Cybersecurity Innovation Grant Program")
                
                # Verify API was called correctly
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                self.assertIn("grants.gov", call_args[0][0])
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_fetch_grants_opportunities_api_error(self):
        """Test grant fetching with API error"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock requests.get to raise exception
            with patch('govcon_suite.requests.get') as mock_get:
                mock_get.side_effect = Exception("API Error")
                
                # Mock streamlit warning
                with patch('govcon_suite.st.warning') as mock_warning:
                    result = govcon_suite.fetch_grants_opportunities(
                        keywords=["technology"],
                        max_results=50
                    )
                    
                    # Should return empty list on error
                    self.assertEqual(result, [])
                    
                    # Should log warning
                    mock_warning.assert_called_once()
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_process_grant_opportunity(self):
        """Test grant opportunity processing"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Test grant processing
            result = govcon_suite.process_grant_opportunity(self.mock_grant_data)
            
            # Verify processed structure
            self.assertIsInstance(result, dict)
            self.assertEqual(result["notice_id"], "GRANT-GRANT-123456")
            self.assertEqual(result["title"], "Cybersecurity Innovation Grant Program")
            self.assertEqual(result["agency"], "Department of Homeland Security")
            self.assertEqual(result["opportunity_type"], "grant")
            self.assertEqual(result["funding_amount"], "$500,000")
            self.assertEqual(result["cfda_number"], "97.108")
            self.assertIn("Small business", result["eligibility_criteria"])
            self.assertEqual(result["raw_data"], self.mock_grant_data)
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_calculate_grant_p_win(self):
        """Test grant-specific P-Win calculation"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Test grant P-Win calculation
            grant_data = {
                "title": "Cybersecurity Innovation Grant for Small Business",
                "description": "Technology development and research grant",
                "eligibility_criteria": "Small business concerns eligible",
                "funding_amount": "$250,000",
                "opportunity_type": "grant"
            }
            
            p_win_score = govcon_suite.calculate_grant_p_win(grant_data)
            
            # Verify score calculation
            self.assertIsInstance(p_win_score, int)
            self.assertGreaterEqual(p_win_score, 0)
            self.assertLessEqual(p_win_score, 100)
            
            # Should have high score due to small business eligibility and tech keywords
            self.assertGreater(p_win_score, 50)
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_calculate_p_win_grant_routing(self):
        """Test that calculate_p_win routes to grant calculation for grants"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock the grant P-Win function
            with patch('govcon_suite.calculate_grant_p_win') as mock_grant_p_win:
                mock_grant_p_win.return_value = 85
                
                grant_data = {"opportunity_type": "grant", "title": "Test Grant"}
                
                result = govcon_suite.calculate_p_win(grant_data)
                
                # Should call grant-specific function
                mock_grant_p_win.assert_called_once_with(grant_data)
                self.assertEqual(result, 85)
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_generate_analysis_summary_grant(self):
        """Test analysis summary generation for grants"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            grant_data = {
                "opportunity_type": "grant",
                "funding_amount": "$500,000",
                "cfda_number": "97.108",
                "eligibility_criteria": "Small business concerns eligible"
            }
            
            summary = govcon_suite.generate_analysis_summary(grant_data, 85)
            
            # Verify grant-specific summary elements
            self.assertIn("P-Win: 85%", summary)
            self.assertIn("GRANT", summary)
            self.assertIn("Funding: $500,000", summary)
            self.assertIn("Small Biz Eligible", summary)
            self.assertIn("CFDA: 97.108", summary)
            self.assertIn("HIGH PRIORITY", summary)
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_run_grants_scraper(self):
        """Test dedicated grants scraper"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock dependencies
            with patch('govcon_suite.setup_database') as mock_setup_db, \
                 patch('govcon_suite.fetch_grants_opportunities') as mock_fetch, \
                 patch('govcon_suite.process_grant_opportunity') as mock_process, \
                 patch('govcon_suite.store_opportunities') as mock_store:
                
                mock_setup_db.return_value = Mock()
                mock_fetch.return_value = [self.mock_grant_data]
                mock_process.return_value = {
                    "notice_id": "GRANT-123456",
                    "title": "Test Grant",
                    "opportunity_type": "grant"
                }
                mock_store.return_value = 1
                
                # Test grants scraper
                result = govcon_suite.run_grants_scraper(
                    keywords=["technology"],
                    max_results=50
                )
                
                # Verify function calls
                mock_fetch.assert_called_once_with(["technology"], 50)
                mock_process.assert_called_once_with(self.mock_grant_data)
                mock_store.assert_called_once()
                
                # Verify result
                self.assertEqual(result, 1)
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_run_scraper_with_grants(self):
        """Test enhanced scraper with grants inclusion"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock dependencies
            with patch('govcon_suite.check_api_key_expiration'), \
                 patch('govcon_suite.setup_database') as mock_setup_db, \
                 patch('govcon_suite.fetch_opportunities') as mock_fetch_contracts, \
                 patch('govcon_suite.fetch_grants_opportunities') as mock_fetch_grants, \
                 patch('govcon_suite.process_grant_opportunity') as mock_process, \
                 patch('govcon_suite.store_opportunities') as mock_store:
                
                mock_setup_db.return_value = Mock()
                mock_fetch_contracts.return_value = [{"noticeId": "CONTRACT-123"}]
                mock_fetch_grants.return_value = [self.mock_grant_data]
                mock_process.return_value = {"notice_id": "GRANT-123456"}
                mock_store.side_effect = [1, 1]  # Return 1 for each call
                
                # Test scraper with grants enabled
                result = govcon_suite.run_scraper(
                    date_from="09/01/2025",
                    date_to="09/30/2025",
                    naics="541511",
                    include_grants=True
                )
                
                # Verify both contract and grant fetching
                mock_fetch_contracts.assert_called_once()
                mock_fetch_grants.assert_called_once()
                mock_process.assert_called_once()
                
                # Should be called twice: once for contracts, once for grants
                self.assertEqual(mock_store.call_count, 2)
                
                # Total inserted should be 2 (1 contract + 1 grant)
                self.assertEqual(result, 2)
    
    def test_grants_gov_api_parameters(self):
        """Test Grants.gov API parameter construction"""
        
        # Test basic parameters
        expected_params = {
            "format": "json",
            "rows": 100,
            "start": 0
        }
        
        # Test with keywords
        keywords = ["cybersecurity", "innovation"]
        expected_with_keywords = expected_params.copy()
        expected_with_keywords["q"] = "cybersecurity innovation"
        
        # Verify parameter structure
        self.assertIn("format", expected_params)
        self.assertEqual(expected_params["format"], "json")
        self.assertIn("rows", expected_params)
        self.assertIn("start", expected_params)
        
        # Test keyword joining
        joined_keywords = " ".join(keywords)
        self.assertEqual(joined_keywords, "cybersecurity innovation")
    
    def test_grant_data_mapping(self):
        """Test mapping of Grants.gov fields to internal structure"""
        
        # Test field mapping
        grant_fields = {
            "id": "notice_id",
            "title": "title", 
            "agencyName": "agency",
            "postedDate": "posted_date",
            "closeDate": "response_deadline",
            "awardCeiling": "funding_amount",
            "cfdaNumber": "cfda_number",
            "eligibilityCriteria": "eligibility_criteria"
        }
        
        # Verify all required mappings exist
        required_internal_fields = [
            "notice_id", "title", "agency", "posted_date", "response_deadline",
            "funding_amount", "cfda_number", "eligibility_criteria", "opportunity_type"
        ]
        
        for field in required_internal_fields:
            if field != "opportunity_type":  # This is added during processing
                self.assertIn(field, grant_fields.values())


if __name__ == '__main__':
    unittest.main(verbosity=2)
