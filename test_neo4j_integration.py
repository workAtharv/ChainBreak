#!/usr/bin/env python3
"""
ChainBreak Neo4j Integration Test Script

This script tests the Neo4j integration and all ChainBreak components
to ensure they work properly together.
"""

import os
import sys
import time
import logging
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chainbreak import ChainBreak
from src.utils import DataValidator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jIntegrationTester:
    """Test Neo4j integration and ChainBreak components"""
    
    def __init__(self):
        self.test_addresses = [
            "13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94",  # WannaCry ransomware
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block
            "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",  # Common test address
        ]
        self.chainbreak = None
        
    def test_neo4j_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            logger.info("Testing Neo4j connection...")
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record and record["test"] == 1:
                    logger.info("✅ Neo4j connection successful!")
                    driver.close()
                    return True
            
            driver.close()
            return False
            
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            return False
    
    def test_chainbreak_initialization(self) -> bool:
        """Test ChainBreak initialization"""
        try:
            logger.info("Testing ChainBreak initialization...")
            self.chainbreak = ChainBreak()
            
            if self.chainbreak.is_neo4j_available():
                logger.info("✅ ChainBreak initialized with Neo4j backend")
                return True
            else:
                logger.warning("⚠️ ChainBreak initialized with JSON backend")
                return False
                
        except Exception as e:
            logger.error(f"❌ ChainBreak initialization failed: {e}")
            return False
    
    def test_data_ingestion(self) -> bool:
        """Test data ingestion"""
        try:
            logger.info("Testing data ingestion...")
            
            if not self.chainbreak:
                logger.error("ChainBreak not initialized")
                return False
            
            # Test with a simple address
            test_address = self.test_addresses[0]
            logger.info(f"Testing data ingestion for address: {test_address}")
            
            success = self.chainbreak.data_ingestor.ingest_address_data(test_address)
            
            if success:
                logger.info("✅ Data ingestion successful!")
                return True
            else:
                logger.warning("⚠️ Data ingestion failed or returned no data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Data ingestion test failed: {e}")
            return False
    
    def test_threat_intelligence(self) -> bool:
        """Test threat intelligence integration"""
        try:
            logger.info("Testing threat intelligence integration...")
            
            if not self.chainbreak:
                logger.error("ChainBreak not initialized")
                return False
            
            # Test threat intelligence status
            status = self.chainbreak.get_threat_intelligence_status()
            logger.info(f"Threat intelligence status: {status}")
            
            # Test with WannaCry address
            test_address = self.test_addresses[0]  # WannaCry address
            logger.info(f"Testing threat intelligence for address: {test_address}")
            
            threat_result = self.chainbreak.threat_intel_manager.check_address(test_address)
            logger.info(f"Threat intelligence result: {threat_result}")
            
            if threat_result.get("available", False):
                logger.info("✅ Threat intelligence integration working!")
                return True
            else:
                logger.warning("⚠️ Threat intelligence not available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Threat intelligence test failed: {e}")
            return False
    
    def test_analysis_pipeline(self) -> bool:
        """Test complete analysis pipeline"""
        try:
            logger.info("Testing complete analysis pipeline...")
            
            if not self.chainbreak:
                logger.error("ChainBreak not initialized")
                return False
            
            # Test with WannaCry address
            test_address = self.test_addresses[0]
            logger.info(f"Running complete analysis for address: {test_address}")
            
            results = self.chainbreak.analyze_address(test_address, generate_visualizations=False)
            
            if 'error' in results:
                logger.error(f"❌ Analysis failed: {results['error']}")
                return False
            
            logger.info("✅ Analysis pipeline completed successfully!")
            logger.info(f"Backend mode: {results.get('backend_mode', 'unknown')}")
            logger.info(f"Risk level: {results.get('risk_score', {}).get('risk_level', 'unknown')}")
            logger.info(f"Threat intelligence enhanced: {results.get('risk_score', {}).get('threat_intel_enhanced', False)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Analysis pipeline test failed: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        try:
            logger.info("Testing API endpoints...")
            
            # Test status endpoint
            try:
                response = requests.get("http://localhost:5001/api/status", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ API status endpoint working!")
                else:
                    logger.warning(f"⚠️ API status endpoint returned {response.status_code}")
            except requests.exceptions.RequestException:
                logger.warning("⚠️ API not running or not accessible")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ API endpoints test failed: {e}")
            return False
    
    def test_database_operations(self) -> bool:
        """Test database operations"""
        try:
            logger.info("Testing database operations...")
            
            if not self.chainbreak or not self.chainbreak.is_neo4j_available():
                logger.warning("⚠️ Neo4j not available, skipping database operations test")
                return True
            
            # Test getting system status
            status = self.chainbreak.get_system_status()
            logger.info(f"System status: {status}")
            
            # Test database statistics
            if 'database_statistics' in status:
                db_stats = status['database_statistics']
                logger.info(f"Database statistics: {db_stats}")
            
            logger.info("✅ Database operations test completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database operations test failed: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run all tests and return results"""
        logger.info("🔗 Starting ChainBreak Neo4j Integration Tests")
        logger.info("="*60)
        
        test_results = {}
        
        # Test 1: Neo4j Connection
        test_results['neo4j_connection'] = self.test_neo4j_connection()
        
        # Test 2: ChainBreak Initialization
        test_results['chainbreak_init'] = self.test_chainbreak_initialization()
        
        # Test 3: Data Ingestion
        test_results['data_ingestion'] = self.test_data_ingestion()
        
        # Test 4: Threat Intelligence
        test_results['threat_intelligence'] = self.test_threat_intelligence()
        
        # Test 5: Analysis Pipeline
        test_results['analysis_pipeline'] = self.test_analysis_pipeline()
        
        # Test 6: API Endpoints
        test_results['api_endpoints'] = self.test_api_endpoints()
        
        # Test 7: Database Operations
        test_results['database_operations'] = self.test_database_operations()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
            if result:
                passed_tests += 1
        
        logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! Neo4j integration is working correctly.")
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Check the logs above for details.")
        
        return test_results
    
    def cleanup(self):
        """Cleanup resources"""
        if self.chainbreak:
            try:
                self.chainbreak.close()
                logger.info("ChainBreak resources cleaned up")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")


def main():
    """Main function"""
    tester = Neo4jIntegrationTester()
    
    try:
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during testing: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
