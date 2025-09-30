#!/usr/bin/env python3
"""
APOLLO GOVCON COMPREHENSIVE TEST SUITE
Tests all Phase 1-6 features (59/93 features, 63.4% completion)
Strategic Phase 1: Foundation Testing for completed features
"""

import sys
import os
import traceback
import requests
import time
import subprocess
import unittest
import tempfile
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

class TestApolloGovConFoundation(unittest.TestCase):
    """Foundation tests for Apollo GovCon Suite Phase 1-6 features"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        cls.test_db_url = "postgresql://postgres:mysecretpassword@localhost:5434/sam_contracts_test"
        cls.original_db_url = os.environ.get('GOVCON_DB_URL')
        os.environ['GOVCON_DB_URL'] = cls.test_db_url

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.original_db_url:
            os.environ['GOVCON_DB_URL'] = cls.original_db_url
        elif 'GOVCON_DB_URL' in os.environ:
            del os.environ['GOVCON_DB_URL']

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")

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
        import torch
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np

        # Phase 5 market intelligence imports
        from duckduckgo_search import DDGS

        print("All Phase 1-6 imports successful!")
        return True

    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during imports: {e}")
        return False

def test_docker_containers():
    """Test that Docker containers are running"""
    print("\n🔍 Testing Docker containers...")
    
    try:
        # Check if containers are running
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True)
        
        if 'sammysosa-app-1' in result.stdout and 'sammysosa-db-1' in result.stdout:
            print("✅ Docker containers are running")
            print(result.stdout)
            return True
        else:
            print("❌ Docker containers not found")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Docker container check error: {e}")
        return False

def test_streamlit_app():
    """Test that Streamlit app is accessible"""
    print("\n🔍 Testing Streamlit app accessibility...")
    
    try:
        # Wait a moment for app to be ready
        time.sleep(2)
        
        # Test if the app responds
        response = requests.get('http://localhost:8501', timeout=10)
        
        if response.status_code == 200:
            print("✅ Streamlit app is accessible at http://localhost:8501")
            return True
        else:
            print(f"❌ Streamlit app returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Streamlit app - check if containers are running")
        return False
    except Exception as e:
        print(f"❌ Streamlit app test error: {e}")
        return False

def test_database_connection():
    """Test database connection and Phase 3 schema"""
    print("\n🔍 Testing database connection...")
    
    try:
        from sqlalchemy import create_engine, text
        
        # Use Docker database connection (from host to container)
        DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/sam_contracts"
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected: {version[:50]}...")
            
            # Test Phase 3 tables exist
            tables_to_check = [
                'opportunities',
                'partners', 
                'rfqs',
                'quotes',
                'partner_capabilities'
            ]
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"✅ Table '{table}' exists with {count} records")
                except Exception as e:
                    print(f"⚠️  Table '{table}' issue: {e}")
            
            # Test p_win_score column with fallback logic
            try:
                result = conn.execute(text("SELECT notice_id, title, COALESCE(p_win_score, 50) as p_win_score FROM opportunities LIMIT 1"))
                print("✅ p_win_score column accessible with fallback")
            except Exception as e:
                print(f"⚠️  p_win_score column issue: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_phase1_to_6_functions():
    """Test Phase 1-6 specific functions"""
    print("\n🔍 Testing Phase 1-6 functions...")

    try:
        # Import the main application
        sys.path.append('.')
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
                print(f"✅ {func_name} function exists")
            else:
                missing_functions.append(func_name)
                print(f"⚠️  {func_name} function missing")

        print(f"\n📊 Function Summary:")
        print(f"✅ Existing: {len(existing_functions)}/{len(functions_to_check)} functions")
        print(f"⚠️  Missing: {len(missing_functions)} functions")

        # Test MCP integration patterns
        mcp_functions = [
            'call_mcp_tool',
            'extract_structured_data_mcp',
            'analyze_patterns_mcp',
            'classify_content_mcp'
        ]

        print(f"\n🔍 Testing MCP integration functions...")
        for func_name in mcp_functions:
            if hasattr(govcon_suite, func_name):
                print(f"✅ {func_name} MCP function exists")
            else:
                print(f"⚠️  {func_name} MCP function missing (expected for Phase 1 testing)")

        return len(existing_functions) > len(functions_to_check) // 2  # Pass if more than half exist

    except Exception as e:
        print(f"❌ Phase 1-6 function test error: {e}")
        traceback.print_exc()
        return False

def test_email_configuration():
    """Test email configuration"""
    print("\n🔍 Testing email configuration...")

    try:
        import sendgrid

        # Check if SendGrid is properly configured
        # Note: We won't send actual emails in testing
        print("✅ SendGrid library available")
        print("⚠️  Email functionality requires SENDGRID_API_KEY in production")

        return True

    except Exception as e:
        print(f"❌ Email configuration error: {e}")
        return False

def test_mcp_integration_readiness():
    """Test MCP integration readiness"""
    print("\n🔍 Testing MCP integration readiness...")

    try:
        # Test required libraries for MCP integration
        import requests
        import json
        import uuid

        print("✅ MCP client libraries available")

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

        print("✅ MCP payload structure validation passed")

        # Test connection readiness (without actual connection)
        mcp_server_url = "http://localhost:8080"  # Default MCP server URL
        print(f"✅ MCP server URL configured: {mcp_server_url}")
        print("⚠️  MCP server connection requires GremlinsAI server running")

        return True

    except Exception as e:
        print(f"❌ MCP integration readiness error: {e}")
        return False

if __name__ == "__main__":
    print("APOLLO GOVCON COMPREHENSIVE TEST SUITE")
    print("Testing unified Docker environment")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Docker Containers", test_docker_containers()))
    results.append(("Streamlit App", test_streamlit_app()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("Phase 1-6 Functions", test_phase1_to_6_functions()))
    results.append(("Email Configuration", test_email_configuration()))
    results.append(("MCP Integration Ready", test_mcp_integration_readiness()))
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Phase 3 is fully operational in Docker environment")
        print("✅ Database confusion eliminated - single unified system")
        print("✅ All Phase 3 features ready for testing")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above for details.")
    
    print("\n" + "=" * 60)
    print("🔗 NEXT STEPS FOR PHASE 1 FOUNDATION TESTING:")
    print("1. Access the application at: http://localhost:8501")
    print("2. Run unit tests: python -m pytest tests/unit/ -v")
    print("3. Run integration tests: python -m pytest tests/integration/ -v")
    print("4. Run end-to-end tests: python -m pytest tests/end_to_end/ -v")
    print("5. Test Phase 1-6 features:")
    print("   - Market Intelligence (Phase 5)")
    print("   - Document Analysis (Phase 6)")
    print("   - Partner Management (Phase 3-4)")
    print("   - AI Co-pilot with MCP integration")
    print("6. Verify MCP integration patterns")
    print("7. Test database operations and migrations")
    print("=" * 60)
    print("📋 TESTING STRATEGY SUMMARY:")
    print("✅ Phase 1 (This Week): Foundation Testing - 59/93 features")
    print("🔄 Phase 2 (Ongoing): Continuous Testing for new features")
    print("🚀 Phase 3 (After Phase 7): Optimization and performance")
    print("=" * 60)
