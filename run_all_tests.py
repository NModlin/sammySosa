#!/usr/bin/env python3
"""
APOLLO GOVCON TEST RUNNER
Comprehensive test runner for all Phase 1-6 testing
Executes the strategic three-phase testing approach
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import argparse


class ApolloTestRunner:
    """Comprehensive test runner for Apollo GovCon Suite"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.test_results = {}
        
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"🚀 {title}")
        print("=" * 80)
        
    def print_section(self, title):
        """Print formatted section"""
        print(f"\n📋 {title}")
        print("-" * 60)
        
    def run_command(self, command, description):
        """Run a command and capture results"""
        print(f"\n🔍 {description}")
        print(f"Command: {command}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {description} - PASSED ({duration:.2f}s)")
                self.test_results[description] = {"status": "PASSED", "duration": duration}
                if result.stdout:
                    print("Output:", result.stdout[:500])  # First 500 chars
            else:
                print(f"❌ {description} - FAILED ({duration:.2f}s)")
                self.test_results[description] = {"status": "FAILED", "duration": duration}
                if result.stderr:
                    print("Error:", result.stderr[:500])
                    
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ {description} - ERROR: {e}")
            self.test_results[description] = {"status": "ERROR", "duration": 0}
            return False
    
    def check_prerequisites(self):
        """Check testing prerequisites"""
        self.print_section("Checking Prerequisites")
        
        # Check Python version
        python_version = sys.version_info
        print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version.major < 3 or python_version.minor < 8:
            print("❌ Python 3.8+ required")
            return False
        else:
            print("✅ Python version OK")
        
        # Check required packages
        required_packages = [
            'unittest', 'requests', 'pandas', 'sqlalchemy', 
            'streamlit', 'psycopg2', 'sendgrid'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} available")
            except ImportError:
                print(f"❌ {package} missing")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages: {missing_packages}")
            print("Install with: pip install -r requirements.txt")
            return False
        
        # Check test directories
        test_dirs = ['tests/unit', 'tests/integration', 'tests/end_to_end']
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                print(f"✅ {test_dir} directory exists")
            else:
                print(f"⚠️  {test_dir} directory missing")
        
        return True
    
    def run_phase1_foundation_tests(self):
        """Run Phase 1 Foundation Tests"""
        self.print_header("PHASE 1: FOUNDATION TESTING")
        print("Testing completed Phase 1-6 features (59/93 features, 63.4% completion)")
        
        # 1. Docker comprehensive tests
        self.print_section("Docker Environment Tests")
        self.run_command(
            "python test_docker_comprehensive.py",
            "Docker Comprehensive Test Suite"
        )
        
        # 2. Unit tests
        self.print_section("Unit Tests")
        if os.path.exists("tests/unit"):
            self.run_command(
                "python -m pytest tests/unit/ -v --tb=short",
                "Core Functions Unit Tests"
            )
        else:
            self.run_command(
                "python tests/unit/test_core_functions.py",
                "Core Functions Unit Tests"
            )
        
        # 3. Integration tests
        self.print_section("Integration Tests")
        if os.path.exists("tests/integration"):
            self.run_command(
                "python -m pytest tests/integration/ -v --tb=short",
                "Database & MCP Integration Tests"
            )
        else:
            self.run_command(
                "python tests/integration/test_database_operations.py",
                "Database Operations Tests"
            )
        
        # 4. AI Integration tests
        self.print_section("AI Integration Tests")
        if os.path.exists("tests/integration/test_ai_integration.py"):
            self.run_command(
                "python -m pytest tests/integration/test_ai_integration.py -v --tb=short",
                "AI Integration Tests"
            )

        # 5. Legacy Phase 3 tests
        self.print_section("Legacy Tests")
        if os.path.exists("test_phase3_fixes.py"):
            self.run_command(
                "python test_phase3_fixes.py",
                "Phase 3 Legacy Tests"
            )
    
    def run_phase2_continuous_tests(self):
        """Run Phase 2 Continuous Tests (placeholder for ongoing development)"""
        self.print_header("PHASE 2: CONTINUOUS TESTING")
        print("Continuous testing framework for new Phase 7+ features")
        
        self.print_section("End-to-End Tests")
        if os.path.exists("tests/end_to_end"):
            self.run_command(
                "python -m pytest tests/end_to_end/ -v --tb=short",
                "User Workflow End-to-End Tests"
            )
        else:
            print("⚠️  End-to-end tests require Streamlit app running at http://localhost:8501")
            print("Start with: streamlit run govcon_suite.py --server.port 8501")
    
    def run_phase3_optimization_tests(self):
        """Run Phase 3 Optimization Tests"""
        self.print_header("PHASE 3: OPTIMIZATION TESTING")
        print("Performance, security, and optimization testing")

        # Performance benchmarks
        self.print_section("Performance Benchmarks")
        if os.path.exists("tests/performance/test_performance_benchmarks.py"):
            self.run_command(
                "python -m pytest tests/performance/test_performance_benchmarks.py -v --tb=short",
                "Performance Benchmark Tests"
            )

        # Security validation
        self.print_section("Security Validation")
        if os.path.exists("tests/security/test_security_validation.py"):
            self.run_command(
                "python -m pytest tests/security/test_security_validation.py -v --tb=short",
                "Security Validation Tests"
            )

        # Additional optimization tests
        print("\n📋 Additional optimization areas:")
        print("- Database query optimization")
        print("- MCP integration latency")
        print("- Memory usage optimization")
        print("- Concurrent user handling")
        
    def generate_test_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST RESULTS SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r["status"] == "PASSED")
        failed_tests = sum(1 for r in self.test_results.values() if r["status"] == "FAILED")
        error_tests = sum(1 for r in self.test_results.values() if r["status"] == "ERROR")
        
        print(f"📊 OVERALL RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Errors: {error_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
            print(f"{status_icon} {test_name}: {result['status']} ({result['duration']:.2f}s)")
        
        # Apollo GovCon specific summary
        print(f"\n🎯 APOLLO GOVCON TESTING STATUS:")
        print(f"Phase 1-6 Features: 59/93 (63.4% complete)")
        print(f"Foundation Testing: {'✅ COMPLETE' if passed_tests > failed_tests else '⚠️ NEEDS ATTENTION'}")
        print(f"Ready for Phase 7: {'✅ YES' if success_rate > 70 else '❌ NO - Fix issues first'}")
        
        return success_rate > 70
    
    def run_all_tests(self, phases=None):
        """Run all test phases"""
        if phases is None:
            phases = [1, 2]  # Default to Phase 1 and 2
        
        self.print_header("APOLLO GOVCON COMPREHENSIVE TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Strategic three-phase testing approach for 59/93 completed features")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Please fix issues and try again.")
            return False
        
        # Run test phases
        if 1 in phases:
            self.run_phase1_foundation_tests()
        
        if 2 in phases:
            self.run_phase2_continuous_tests()
        
        if 3 in phases:
            self.run_phase3_optimization_tests()
        
        # Generate report
        success = self.generate_test_report()
        
        print(f"\n🏁 Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Apollo GovCon Test Runner")
    parser.add_argument(
        "--phases", 
        nargs="+", 
        type=int, 
        choices=[1, 2, 3],
        default=[1, 2],
        help="Test phases to run (1=Foundation, 2=Continuous, 3=Optimization)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only essential tests (Phase 1 foundation)"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        phases = [1]
    else:
        phases = args.phases
    
    runner = ApolloTestRunner()
    success = runner.run_all_tests(phases)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
