#!/usr/bin/env python3
"""
ChainBreak Comprehensive Endpoint Testing
Tests all endpoints and system components for deployment readiness
"""

import requests
import json
import sys
import time
from typing import Dict, List, Tuple
from datetime import datetime


class EndpointTester:
    """Comprehensive endpoint testing for ChainBreak"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        self.failed_checks = 0

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None,
                     expected_status: int = 200, description: str = "") -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"

        try:
            start_time = time.time()

            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            duration = time.time() - start_time

            success = response.status_code == expected_status

            result = {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "duration": duration,
                "response_size": len(response.content)
            }

            if success:
                print(f"✅ {method:4} {endpoint:40} - {description:30} ({duration:.2f}s)")
            else:
                print(f"❌ {method:4} {endpoint:40} - {description:30} (Expected {expected_status}, got {response.status_code})")
                self.failed_checks += 1

            self.results.append(result)
            return success

        except Exception as e:
            print(f"❌ {method:4} {endpoint:40} - {description:30} (Error: {str(e)})")
            self.failed_checks += 1
            self.results.append({
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "success": False,
                "error": str(e)
            })
            return False

    def test_backend_availability(self) -> bool:
        """Test if backend is running"""
        print("\n" + "="*80)
        print("BACKEND AVAILABILITY TEST")
        print("="*80)

        return self.test_endpoint(
            "GET", "/api/mode",
            description="Backend mode check"
        )

    def test_system_endpoints(self) -> bool:
        """Test system status endpoints"""
        print("\n" + "="*80)
        print("SYSTEM ENDPOINTS TEST")
        print("="*80)

        results = []

        results.append(self.test_endpoint(
            "GET", "/api/status",
            description="System status"
        ))

        results.append(self.test_endpoint(
            "GET", "/api/statistics",
            description="System statistics"
        ))

        return all(results)

    def test_graph_endpoints(self) -> bool:
        """Test graph-related endpoints"""
        print("\n" + "="*80)
        print("GRAPH ENDPOINTS TEST")
        print("="*80)

        results = []

        results.append(self.test_endpoint(
            "GET", "/api/graph/list",
            description="List available graphs"
        ))

        return all(results)

    def test_threat_intelligence_endpoints(self) -> bool:
        """Test threat intelligence endpoints"""
        print("\n" + "="*80)
        print("THREAT INTELLIGENCE ENDPOINTS TEST")
        print("="*80)

        results = []

        results.append(self.test_endpoint(
            "GET", "/api/threat-intelligence/status",
            description="Threat intel status"
        ))

        return all(results)

    def test_community_detection_endpoints(self) -> bool:
        """Test community detection endpoints"""
        print("\n" + "="*80)
        print("COMMUNITY DETECTION ENDPOINTS TEST")
        print("="*80)

        # Test with minimal graph data
        test_graph = {
            "nodes": [
                {"id": "node1", "label": "Node 1"},
                {"id": "node2", "label": "Node 2"},
                {"id": "node3", "label": "Node 3"}
            ],
            "edges": [
                {"source": "node1", "target": "node2", "weight": 1},
                {"source": "node2", "target": "node3", "weight": 1}
            ]
        }

        results = []

        results.append(self.test_endpoint(
            "POST", "/api/community-detection/detect",
            data={"graph_data": test_graph, "algorithm": "louvain"},
            description="Louvain detection"
        ))

        results.append(self.test_endpoint(
            "POST", "/api/community-detection/detect",
            data={"graph_data": test_graph, "algorithm": "leiden"},
            description="Leiden detection"
        ))

        results.append(self.test_endpoint(
            "POST", "/api/community-detection/detect",
            data={"graph_data": test_graph, "algorithm": "label_propagation"},
            description="Label propagation"
        ))

        return all(results)

    def test_error_handling(self) -> bool:
        """Test error handling"""
        print("\n" + "="*80)
        print("ERROR HANDLING TEST")
        print("="*80)

        results = []

        # Test 404 - should return 404
        results.append(self.test_endpoint(
            "GET", "/api/nonexistent",
            expected_status=404,
            description="404 handler"
        ))

        # Test invalid data - should return 400
        results.append(self.test_endpoint(
            "POST", "/api/graph/address",
            data={"invalid": "data"},
            expected_status=400,
            description="Invalid data handling"
        ))

        return all(results)

    def test_performance(self) -> bool:
        """Test response time performance"""
        print("\n" + "="*80)
        print("PERFORMANCE TEST")
        print("="*80)

        slow_endpoints = []

        for result in self.results:
            if result.get("duration", 0) > 2.0:  # More than 2 seconds
                slow_endpoints.append(result)

        if slow_endpoints:
            print(f"⚠️  Found {len(slow_endpoints)} slow endpoints (>2s):")
            for endpoint in slow_endpoints:
                print(f"   - {endpoint['method']} {endpoint['endpoint']}: {endpoint['duration']:.2f}s")
            return False
        else:
            print(f"✅ All endpoints respond in < 2s")
            return True

    def print_summary(self):
        """Print summary of test results"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        total_tests = len(self.results)
        passed_tests = total_tests - self.failed_checks

        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {self.failed_checks}")

        if self.failed_checks == 0:
            print("\n✅ ALL TESTS PASSED - System is deployment ready!")
            return True
        else:
            print(f"\n❌ {self.failed_checks} TESTS FAILED - Review issues before deployment")
            return False

    def export_report(self, filename: str = "endpoint_test_report.json"):
        """Export detailed report to JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": len(self.results),
                "passed": len(self.results) - self.failed_checks,
                "failed": self.failed_checks
            },
            "results": self.results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report exported to: {filename}")

    def run_all_tests(self) -> bool:
        """Run all endpoint tests"""
        print("\n" + "="*80)
        print("CHAINBREAK ENDPOINT TESTING")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*80)

        # Test backend availability first
        if not self.test_backend_availability():
            print("\n❌ Backend is not available. Cannot proceed with tests.")
            print("   Make sure the server is running: python app.py --api")
            return False

        # Run all tests
        self.test_system_endpoints()
        self.test_graph_endpoints()
        self.test_threat_intelligence_endpoints()
        self.test_community_detection_endpoints()
        self.test_error_handling()
        self.test_performance()

        # Print summary
        success = self.print_summary()

        # Export report
        self.export_report()

        return success


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ChainBreak Endpoint Testing")
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="Base URL of ChainBreak API (default: http://localhost:5000)"
    )
    parser.add_argument(
        "--output",
        default="endpoint_test_report.json",
        help="Output file for detailed report"
    )

    args = parser.parse_args()

    tester = EndpointTester(base_url=args.url)
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
