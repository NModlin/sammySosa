#!/usr/bin/env python3
"""
Performance Benchmarks for Apollo GovCon Suite
Tests performance characteristics of key operations across Phase 1-6 features
"""

import unittest
import sys
import os
import time
import threading
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmark tests for Apollo GovCon Suite"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.performance_results = {}
        self.max_acceptable_time = {
            'database_operation': 2.0,  # seconds
            'document_processing': 5.0,  # seconds
            'partner_search': 3.0,      # seconds
            'mcp_call': 1.0,            # seconds
            'bulk_operation': 10.0      # seconds
        }
    
    def measure_time(self, operation_name, func, *args, **kwargs):
        """Measure execution time of an operation"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.performance_results[operation_name] = {
                'execution_time': execution_time,
                'success': True,
                'result': result
            }
            
            return result, execution_time
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.performance_results[operation_name] = {
                'execution_time': execution_time,
                'success': False,
                'error': str(e)
            }
            
            raise e
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_database_setup_performance(self):
        """Test database setup operation performance"""
        with patch('streamlit.session_state') as mock_session_state:
            mock_session_state._govcon_engine = None
            
            import govcon_suite
            
            with patch('govcon_suite.create_engine') as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                
                # Measure database setup time
                result, exec_time = self.measure_time(
                    'database_setup',
                    govcon_suite.setup_database
                )
                
                # Assert performance benchmark
                self.assertLess(exec_time, self.max_acceptable_time['database_operation'])
                print(f"Database setup time: {exec_time:.3f}s")
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_partner_search_performance(self):
        """Test partner search operation performance"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Mock DDGS for consistent performance testing
            with patch('govcon_suite.DDGS') as mock_ddgs:
                mock_ddgs_instance = Mock()
                mock_ddgs_instance.text.return_value = [
                    {
                        'title': f'Test Company {i}',
                        'href': f'https://test{i}.com',
                        'body': f'Test description {i}'
                    } for i in range(10)
                ]
                mock_ddgs.return_value.__enter__.return_value = mock_ddgs_instance
                
                # Measure partner search time
                result, exec_time = self.measure_time(
                    'partner_search',
                    govcon_suite.find_partners,
                    ['software', 'development'],
                    'Virginia',
                    max_results=10
                )
                
                # Assert performance benchmark
                self.assertLess(exec_time, self.max_acceptable_time['partner_search'])
                print(f"Partner search time: {exec_time:.3f}s")
    
    @unittest.skipIf(not os.path.exists("govcon_suite.py"), "govcon_suite module not available")
    def test_document_processing_performance(self):
        """Test document processing performance"""
        with patch('streamlit.session_state'):
            import govcon_suite
            
            # Create mock document
            mock_file = Mock()
            mock_file.name = "test_document.pdf"
            mock_file.read.return_value = b"Test document content " * 1000  # Larger document
            
            # Measure document loading time
            result, exec_time = self.measure_time(
                'document_loading',
                govcon_suite.load_document_text,
                mock_file
            )
            
            # Assert performance benchmark
            self.assertLess(exec_time, self.max_acceptable_time['document_processing'])
            print(f"Document loading time: {exec_time:.3f}s")
    
    def test_mcp_payload_creation_performance(self):
        """Test MCP payload creation performance"""
        import json
        import uuid
        
        def create_mcp_payload():
            return {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "extract_structured_data",
                    "arguments": {
                        "text": "Test document content " * 100,
                        "schema": {
                            "title": "string",
                            "requirements": "array",
                            "deadline": "string"
                        },
                        "domain_context": "government_contracting"
                    }
                }
            }
        
        # Measure payload creation time
        result, exec_time = self.measure_time(
            'mcp_payload_creation',
            create_mcp_payload
        )
        
        # Assert performance benchmark
        self.assertLess(exec_time, self.max_acceptable_time['mcp_call'])
        print(f"MCP payload creation time: {exec_time:.3f}s")
        
        # Validate payload structure
        self.assertIn("jsonrpc", result)
        self.assertIn("id", result)
        self.assertIn("method", result)
        self.assertIn("params", result)
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent load"""
        
        def mock_database_operation(operation_id):
            """Mock database operation"""
            time.sleep(0.1)  # Simulate database work
            return f"Operation {operation_id} completed"
        
        # Test concurrent database operations
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(mock_database_operation, i)
                for i in range(10)
            ]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Should complete faster than sequential execution
        sequential_time_estimate = 10 * 0.1  # 10 operations * 0.1s each
        self.assertLess(concurrent_time, sequential_time_estimate)
        
        print(f"Concurrent operations time: {concurrent_time:.3f}s")
        print(f"Sequential estimate: {sequential_time_estimate:.3f}s")
        print(f"Speedup: {sequential_time_estimate/concurrent_time:.2f}x")
    
    def test_memory_usage_patterns(self):
        """Test memory usage patterns for large operations"""
        import gc
        
        # Test large data structure creation
        start_time = time.time()
        
        # Simulate processing large opportunity dataset
        large_dataset = [
            {
                'id': i,
                'title': f'Opportunity {i}',
                'description': 'Large description ' * 100,
                'requirements': ['req1', 'req2', 'req3'] * 10
            }
            for i in range(1000)
        ]
        
        # Process dataset
        processed_data = []
        for item in large_dataset:
            processed_item = {
                'id': item['id'],
                'title': item['title'].upper(),
                'word_count': len(item['description'].split()),
                'req_count': len(item['requirements'])
            }
            processed_data.append(processed_item)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Clean up
        del large_dataset
        del processed_data
        gc.collect()
        
        # Assert reasonable processing time
        self.assertLess(processing_time, self.max_acceptable_time['bulk_operation'])
        print(f"Large dataset processing time: {processing_time:.3f}s")
    
    def test_api_response_time_simulation(self):
        """Test simulated API response times"""
        
        def simulate_api_call(delay=0.1):
            """Simulate external API call"""
            time.sleep(delay)
            return {
                'status': 'success',
                'data': {'result': 'API response data'},
                'timestamp': time.time()
            }
        
        # Test various API call scenarios
        api_scenarios = [
            ('fast_api', 0.05),
            ('normal_api', 0.1),
            ('slow_api', 0.3)
        ]
        
        for scenario_name, delay in api_scenarios:
            result, exec_time = self.measure_time(
                f'api_call_{scenario_name}',
                simulate_api_call,
                delay
            )
            
            # Verify response structure
            self.assertIn('status', result)
            self.assertIn('data', result)
            self.assertEqual(result['status'], 'success')
            
            print(f"{scenario_name} response time: {exec_time:.3f}s")
    
    def test_search_algorithm_performance(self):
        """Test search algorithm performance"""
        
        # Create test dataset
        test_opportunities = [
            {
                'id': i,
                'title': f'Software Development Contract {i}',
                'agency': f'Agency {i % 10}',
                'keywords': ['software', 'development', 'programming'],
                'location': 'Virginia' if i % 2 == 0 else 'Maryland'
            }
            for i in range(1000)
        ]
        
        def search_opportunities(query, location=None):
            """Simple search algorithm"""
            results = []
            for opp in test_opportunities:
                # Title search
                if query.lower() in opp['title'].lower():
                    if location is None or opp['location'] == location:
                        results.append(opp)
            return results
        
        # Test search performance
        result, exec_time = self.measure_time(
            'opportunity_search',
            search_opportunities,
            'Software Development',
            'Virginia'
        )
        
        # Assert reasonable search time
        self.assertLess(exec_time, 1.0)  # Should be very fast for 1000 records
        self.assertGreater(len(result), 0)  # Should find matches
        
        print(f"Search algorithm time: {exec_time:.3f}s")
        print(f"Results found: {len(result)}")
    
    def tearDown(self):
        """Print performance summary"""
        if hasattr(self, 'performance_results') and self.performance_results:
            print("\n" + "="*60)
            print("PERFORMANCE BENCHMARK SUMMARY")
            print("="*60)
            
            for operation, metrics in self.performance_results.items():
                if metrics['success']:
                    print(f"✅ {operation}: {metrics['execution_time']:.3f}s")
                else:
                    print(f"❌ {operation}: FAILED - {metrics.get('error', 'Unknown error')}")
            
            print("="*60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
