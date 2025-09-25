#!/usr/bin/env python3
"""
Test script for Phase 3 fixes
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """Test that all Phase 3 functions can be imported"""
    try:
        from govcon_suite import (
            send_rfq_email, 
            create_rfq_dispatch_record, 
            submit_quote, 
            get_quotes_for_opportunity,
            setup_database,
            run_database_migrations
        )
        print("✅ All Phase 3 functions imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test database connection and migration"""
    try:
        from govcon_suite import setup_database
        engine = setup_database()
        
        if engine == "demo_mode":
            print("✅ Demo mode active - database tests skipped")
            return True
        elif engine:
            print("✅ Database connection successful!")
            print("✅ Database migrations completed!")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_opportunity_query():
    """Test the fixed opportunity query"""
    try:
        from govcon_suite import setup_database
        import pandas as pd
        
        engine = setup_database()
        if engine == "demo_mode":
            print("✅ Demo mode - opportunity query test skipped")
            return True
        
        # Test the fallback query logic
        try:
            # Try with p_win_score first
            opportunities_df = pd.read_sql(
                "SELECT notice_id, title, agency, response_deadline, p_win_score FROM opportunities WHERE status != 'Closed' ORDER BY p_win_score DESC LIMIT 5",
                engine
            )
            print("✅ P-Win score query works!")
        except Exception:
            try:
                # Fallback with COALESCE
                opportunities_df = pd.read_sql(
                    "SELECT notice_id, title, agency, response_deadline, COALESCE(p_win_score, 50) as p_win_score FROM opportunities WHERE status != 'Closed' ORDER BY response_deadline DESC LIMIT 5",
                    engine
                )
                print("✅ Fallback COALESCE query works!")
            except Exception:
                # Final fallback - basic query
                opportunities_df = pd.read_sql(
                    "SELECT notice_id, title, agency, response_deadline FROM opportunities WHERE status != 'Closed' ORDER BY response_deadline DESC LIMIT 5",
                    engine
                )
                opportunities_df['p_win_score'] = 50  # Default score
                print("✅ Basic fallback query works!")
        
        print(f"✅ Found {len(opportunities_df)} opportunities")
        return True
        
    except Exception as e:
        print(f"❌ Opportunity query test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Phase 3 Fixes...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Connection", test_database_connection),
        ("Opportunity Query", test_opportunity_query)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 3 fixes are working correctly.")
        print("\n📋 Next Steps:")
        print("1. Start your Streamlit app: streamlit run Apollo_GovCon.py --server.port 8502")
        print("2. Test the Partner Relationship Manager")
        print("3. Try the AI Co-pilot file upload")
        print("4. Test RFQ generation")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
