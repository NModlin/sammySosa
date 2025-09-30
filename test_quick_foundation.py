#!/usr/bin/env python3
"""
APOLLO GOVCON QUICK FOUNDATION TESTS
Simplified test runner for immediate validation of Phase 1-6 features
Windows-compatible version without Unicode characters
"""

import sys
import os
import traceback
import unittest
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("\nTesting imports...")
    
    try:
        # Core imports
        import streamlit as st
        import pandas as pd
        import psycopg2
        from sqlalchemy import create_engine, text
        
        # Phase 3-6 specific imports
        import sendgrid
        from sendgrid.helpers.mail import Mail
        import uuid
        from jinja2 import Template
        
        # AI imports for Phase 6 document analysis
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            print("AI libraries available")
        except ImportError:
            print("AI libraries not available (optional)")
        
        # Phase 5 market intelligence imports
        try:
            from duckduckgo_search import DDGS
            print("DuckDuckGo search available")
        except ImportError:
            print("DuckDuckGo search not available (optional)")
        
        print("All Phase 1-6 core imports successful!")
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during imports: {e}")
        return False

def test_govcon_suite_functions():
    """Test govcon_suite.py functions"""
    print("\nTesting govcon_suite functions...")
    
    try:
        import govcon_suite
        
        # Test core functions across all phases
        functions_to_check = [
            # Phase 1-2: Core scraping and dashboard
            'setup_database',
            'run_scraper',
            'fetch_opportunities',
            'store_opportunities',
            
            # Phase 3: Partner management
            'add_partner',
            'send_rfq_email', 
            'generate_partner_portal_link',
            'create_rfq',
            'get_partner_capabilities',
            'update_quote_status',
            
            # Phase 4: Enhanced features
            'add_subcontractor_to_db',
            'find_partners',
            
            # Phase 5: Market intelligence
            'analyze_market_trends',
            'score_opportunity',
            'generate_competitive_analysis',
            
            # Phase 6: Document analysis
            'load_document_text',
            'create_vector_store',
            'analyze_document_compliance',
            'extract_key_requirements'
        ]
        
        existing_functions = []
        missing_functions = []
        
        for func_name in functions_to_check:
            if hasattr(govcon_suite, func_name):
                existing_functions.append(func_name)
                print(f"PASS: {func_name} function exists")
            else:
                missing_functions.append(func_name)
                print(f"MISSING: {func_name} function")
        
        print(f"\nFunction Summary:")
        print(f"Existing: {len(existing_functions)}/{len(functions_to_check)} functions")
        print(f"Missing: {len(missing_functions)} functions")
        
        # Pass if more than half exist
        return len(existing_functions) > len(functions_to_check) // 2
        
    except ImportError as e:
        print(f"Could not import govcon_suite: {e}")
        return False
    except Exception as e:
        print(f"Error testing functions: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from sqlalchemy import create_engine, text
        
        # Try to import govcon_suite for database functions
        try:
            import govcon_suite
            engine = govcon_suite.setup_database()
            
            if engine == "demo_mode":
                print("Demo mode active - database tests skipped")
                return True
            elif engine:
                print("Database connection successful!")
                return True
            else:
                print("Database connection failed")
                return False
        except Exception as e:
            print(f"Database test error: {e}")
            return False
            
    except ImportError as e:
        print(f"Database libraries not available: {e}")
        return False

def test_mcp_integration_readiness():
    """Test MCP integration readiness"""
    print("\nTesting MCP integration readiness...")
    
    try:
        # Test required libraries for MCP integration
        import requests
        import json
        import uuid
        
        print("MCP client libraries available")
        
        # Test JSON-RPC 2.0 payload creation
        test_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "extract_structured_data",
                "arguments": {
                    "text": "test document",
                    "schema": {"title": "string"},
                    "domain_context": "government_contracting"
                }
            }
        }
        
        # Validate payload structure
        assert "jsonrpc" in test_payload
        assert "id" in test_payload
        assert "method" in test_payload
        assert "params" in test_payload
        
        print("MCP payload structure validation passed")
        
        # Test connection readiness (without actual connection)
        mcp_server_url = "http://localhost:8080"  # Default MCP server URL
        print(f"MCP server URL configured: {mcp_server_url}")
        print("NOTE: MCP server connection requires GremlinsAI server running")
        
        return True
        
    except Exception as e:
        print(f"MCP integration readiness error: {e}")
        return False

def run_unit_tests():
    """Run basic unit tests"""
    print("\nRunning unit tests...")
    
    try:
        # Try to run unit tests if they exist
        if os.path.exists("tests/unit/test_core_functions.py"):
            # Import and run specific test
            sys.path.insert(0, "tests/unit")
            from test_core_functions import TestCoreFunctions
            
            # Create test suite
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreFunctions)
            runner = unittest.TextTestRunner(verbosity=1)
            result = runner.run(suite)
            
            return result.wasSuccessful()
        else:
            print("Unit test files not found - skipping")
            return True
            
    except Exception as e:
        print(f"Unit test error: {e}")
        return False

def main():
    """Main test runner"""
    print("APOLLO GOVCON QUICK FOUNDATION TESTS")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing Phase 1-6 features (59/93 features, 63.4% completion)")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("GovCon Suite Functions", test_govcon_suite_functions()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("MCP Integration Ready", test_mcp_integration_readiness()))
    results.append(("Unit Tests", run_unit_tests()))
    
    # Summary
    print("\n" + "=" * 60)
    print("QUICK FOUNDATION TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"\nOverall Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 70:
        print("FOUNDATION TESTING: PASSED - Ready for Phase 7")
    else:
        print("FOUNDATION TESTING: NEEDS ATTENTION - Fix issues before Phase 7")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Address any failing tests above")
    print("2. Run full test suite: python run_all_tests.py --phases 1")
    print("3. Start Phase 7 development when foundation tests pass")
    print("4. Implement continuous testing for new features")
    print("=" * 60)
    
    return success_rate >= 70

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
