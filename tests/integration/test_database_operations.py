#!/usr/bin/env python3
"""
APOLLO GOVCON INTEGRATION TESTS - DATABASE OPERATIONS
Phase 1 Foundation Testing: Integration tests for database operations
Tests database interactions for Phase 1-6 features
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import govcon_suite
    from govcon_suite import setup_database, get_engine, store_opportunities
except ImportError as e:
    print(f"Warning: Could not import govcon_suite: {e}")
    govcon_suite = None


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations for Apollo GovCon Suite"""
    
    def setUp(self):
        """Set up test database for each test"""
        # Use in-memory SQLite for testing
        self.test_db_url = "sqlite:///:memory:"
        self.original_db_url = os.environ.get('GOVCON_DB_URL')
        os.environ['GOVCON_DB_URL'] = self.test_db_url
        
        # Create test engine
        self.test_engine = create_engine(self.test_db_url)
        
    def tearDown(self):
        """Clean up after each test"""
        if self.original_db_url:
            os.environ['GOVCON_DB_URL'] = self.original_db_url
        elif 'GOVCON_DB_URL' in os.environ:
            del os.environ['GOVCON_DB_URL']
            
        # Close test engine
        if hasattr(self, 'test_engine'):
            self.test_engine.dispose()

    def create_test_tables(self):
        """Create test tables for testing"""
        metadata = MetaData()
        
        # Create opportunities table
        opportunities_table = Table(
            'opportunities', metadata,
            Column('id', Integer, primary_key=True),
            Column('notice_id', String(50), unique=True),
            Column('title', String(500)),
            Column('agency', String(200)),
            Column('posted_date', String(20)),
            Column('response_deadline', String(20)),
            Column('description', String),
            Column('naics_code', String(10)),
            Column('set_aside', String(100)),
            Column('place_of_performance', String(200))
        )
        
        # Create partners table
        partners_table = Table(
            'partners', metadata,
            Column('id', Integer, primary_key=True),
            Column('company_name', String(200)),
            Column('contact_email', String(100)),
            Column('contact_phone', String(20)),
            Column('website', String(200)),
            Column('location', String(100)),
            Column('trust_score', Integer),
            Column('vetting_notes', String)
        )
        
        metadata.create_all(self.test_engine)
        return opportunities_table, partners_table

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_database_connection_success(self):
        """Test successful database connection"""
        with patch('govcon_suite.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            engine = get_engine()
            
            self.assertIsNotNone(engine)
            mock_create_engine.assert_called_once()

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_database_connection_failure(self):
        """Test database connection failure"""
        with patch('govcon_suite.create_engine') as mock_create_engine:
            mock_create_engine.side_effect = SQLAlchemyError("Connection failed")
            
            engine = get_engine()
            
            # Should return demo_mode on connection failure
            self.assertEqual(engine, "demo_mode")

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_store_opportunities_success(self):
        """Test successful opportunity storage"""
        # Create test tables
        opportunities_table, _ = self.create_test_tables()
        
        # Test data
        test_opportunities = [
            {
                'notice_id': 'TEST-001',
                'title': 'Software Development Services',
                'agency': 'Department of Defense',
                'posted_date': '2024-01-15',
                'response_deadline': '2024-02-15',
                'description': 'Develop custom software solutions',
                'naics_code': '541511',
                'set_aside': 'Small Business',
                'place_of_performance': 'Virginia'
            },
            {
                'notice_id': 'TEST-002',
                'title': 'Cybersecurity Assessment',
                'agency': 'Department of Homeland Security',
                'posted_date': '2024-01-16',
                'response_deadline': '2024-02-16',
                'description': 'Conduct security assessments',
                'naics_code': '541512',
                'set_aside': 'Unrestricted',
                'place_of_performance': 'Maryland'
            }
        ]
        
        # Store opportunities
        stored_count = store_opportunities(self.test_engine, test_opportunities)
        
        # Verify storage
        self.assertEqual(stored_count, 2)
        
        # Verify data in database
        with self.test_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM opportunities"))
            count = result.fetchone()[0]
            self.assertEqual(count, 2)
            
            # Check specific record
            result = conn.execute(text("SELECT title FROM opportunities WHERE notice_id = 'TEST-001'"))
            title = result.fetchone()[0]
            self.assertEqual(title, 'Software Development Services')

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_store_opportunities_duplicate_handling(self):
        """Test handling of duplicate opportunities"""
        # Create test tables
        opportunities_table, _ = self.create_test_tables()
        
        # Test data with duplicate notice_id
        test_opportunities = [
            {
                'notice_id': 'TEST-001',
                'title': 'Original Title',
                'agency': 'DOD',
                'posted_date': '2024-01-15',
                'response_deadline': '2024-02-15',
                'description': 'Original description',
                'naics_code': '541511',
                'set_aside': 'Small Business',
                'place_of_performance': 'Virginia'
            }
        ]
        
        # Store first time
        stored_count_1 = store_opportunities(self.test_engine, test_opportunities)
        self.assertEqual(stored_count_1, 1)
        
        # Try to store duplicate
        duplicate_opportunities = [
            {
                'notice_id': 'TEST-001',  # Same notice_id
                'title': 'Updated Title',
                'agency': 'DOD',
                'posted_date': '2024-01-15',
                'response_deadline': '2024-02-15',
                'description': 'Updated description',
                'naics_code': '541511',
                'set_aside': 'Small Business',
                'place_of_performance': 'Virginia'
            }
        ]
        
        stored_count_2 = store_opportunities(self.test_engine, duplicate_opportunities)
        
        # Should handle duplicates gracefully (implementation dependent)
        # Verify total count is still 1
        with self.test_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM opportunities"))
            count = result.fetchone()[0]
            self.assertEqual(count, 1)

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_store_opportunities_empty_list(self):
        """Test storing empty opportunities list"""
        # Create test tables
        opportunities_table, _ = self.create_test_tables()
        
        # Store empty list
        stored_count = store_opportunities(self.test_engine, [])
        
        self.assertEqual(stored_count, 0)
        
        # Verify database is empty
        with self.test_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM opportunities"))
            count = result.fetchone()[0]
            self.assertEqual(count, 0)

    @unittest.skipIf(govcon_suite is None, "govcon_suite module not available")
    def test_partner_database_operations(self):
        """Test partner-related database operations"""
        # Create test tables
        _, partners_table = self.create_test_tables()
        
        # Test partner data
        partner_data = {
            'company_name': 'Test Partner Corp',
            'contact_email': 'contact@testpartner.com',
            'contact_phone': '555-0123',
            'website': 'https://testpartner.com',
            'location': 'Virginia',
            'trust_score': 85,
            'vetting_notes': 'Reliable partner with good track record'
        }
        
        # Insert partner
        with self.test_engine.connect() as conn:
            insert_stmt = partners_table.insert().values(**partner_data)
            result = conn.execute(insert_stmt)
            conn.commit()
            
            # Verify insertion
            select_stmt = text("SELECT company_name, trust_score FROM partners WHERE company_name = :name")
            result = conn.execute(select_stmt, {"name": "Test Partner Corp"})
            row = result.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Test Partner Corp')
            self.assertEqual(row[1], 85)

    def test_database_migration_simulation(self):
        """Test database migration patterns"""
        # Create initial schema
        metadata_v1 = MetaData()
        
        # Version 1 table
        opportunities_v1 = Table(
            'opportunities', metadata_v1,
            Column('id', Integer, primary_key=True),
            Column('notice_id', String(50)),
            Column('title', String(500))
        )
        
        metadata_v1.create_all(self.test_engine)
        
        # Insert test data
        with self.test_engine.connect() as conn:
            conn.execute(opportunities_v1.insert().values(
                notice_id='TEST-001',
                title='Test Opportunity'
            ))
            conn.commit()
            
            # Verify initial data
            result = conn.execute(text("SELECT COUNT(*) FROM opportunities"))
            count = result.fetchone()[0]
            self.assertEqual(count, 1)
            
            # Simulate adding new column (migration)
            conn.execute(text("ALTER TABLE opportunities ADD COLUMN agency VARCHAR(200)"))
            conn.commit()
            
            # Update existing record
            conn.execute(text("UPDATE opportunities SET agency = 'DOD' WHERE notice_id = 'TEST-001'"))
            conn.commit()
            
            # Verify migration
            result = conn.execute(text("SELECT agency FROM opportunities WHERE notice_id = 'TEST-001'"))
            agency = result.fetchone()[0]
            self.assertEqual(agency, 'DOD')

    def test_database_performance_patterns(self):
        """Test database performance patterns"""
        # Create test table
        opportunities_table, _ = self.create_test_tables()
        
        # Insert multiple records to test bulk operations
        bulk_data = []
        for i in range(100):
            bulk_data.append({
                'notice_id': f'BULK-{i:03d}',
                'title': f'Bulk Opportunity {i}',
                'agency': 'Test Agency',
                'posted_date': '2024-01-15',
                'response_deadline': '2024-02-15',
                'description': f'Bulk test opportunity {i}',
                'naics_code': '541511',
                'set_aside': 'Small Business',
                'place_of_performance': 'Virginia'
            })
        
        # Time the bulk insert (in real implementation)
        start_time = datetime.now()
        
        with self.test_engine.connect() as conn:
            conn.execute(opportunities_table.insert(), bulk_data)
            conn.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Verify all records inserted
        with self.test_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM opportunities"))
            count = result.fetchone()[0]
            self.assertEqual(count, 100)
        
        # Performance should be reasonable (less than 5 seconds for 100 records)
        self.assertLess(duration, 5.0)

    def test_database_error_handling(self):
        """Test database error handling"""
        # Test with invalid SQL
        with self.test_engine.connect() as conn:
            with self.assertRaises(SQLAlchemyError):
                conn.execute(text("SELECT * FROM nonexistent_table"))
        
        # Test with invalid data types
        opportunities_table, _ = self.create_test_tables()
        
        with self.test_engine.connect() as conn:
            # This should handle gracefully or raise appropriate error
            try:
                conn.execute(opportunities_table.insert().values(
                    notice_id='TEST-001',
                    title='Test',
                    # Missing required fields - should be handled
                ))
                conn.commit()
            except SQLAlchemyError:
                # Expected behavior for invalid data
                pass


if __name__ == '__main__':
    print("🚀 APOLLO GOVCON INTEGRATION TESTS - DATABASE OPERATIONS")
    print("=" * 60)
    print("Testing database operations for Phase 1-6 features")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2)
