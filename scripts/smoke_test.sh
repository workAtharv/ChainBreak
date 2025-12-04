#!/bin/bash

# ChainBreak Smoke Test Script
# Tests all backend endpoints to ensure they're working correctly

set -e

BASE_URL="http://localhost:5001"
API_BASE="$BASE_URL/api"

echo "🔍 ChainBreak Smoke Test"
echo "========================"
echo "Testing backend at: $BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
run_test() {
    local test_name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="${4:-}"
    
    echo -n "Testing $test_name... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo "Connection failed")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$endpoint" 2>/dev/null || echo "Connection failed")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "Connection failed" ]; then
        echo -e "${RED}FAILED${NC}"
        echo "  Error: Could not connect to backend"
        echo "  Make sure the server is running on $BASE_URL"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}PASS${NC}"
        echo "  Status: $http_code"
        if [ -n "$body" ]; then
            echo "  Response: $(echo "$body" | head -c 100)..."
        fi
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Status: $http_code"
        if [ -n "$body" ]; then
            echo "  Response: $body"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 1: Backend mode
echo -e "${BLUE}1. Backend Mode Test${NC}"
run_test "GET /api/mode" "$API_BASE/mode"

# Test 2: System status
echo -e "${BLUE}2. System Status Test${NC}"
run_test "GET /api/status" "$API_BASE/status"

# Test 3: List graphs (should return empty list initially)
echo -e "${BLUE}3. List Graphs Test${NC}"
run_test "GET /api/graph/list" "$API_BASE/graph/list"

# Test 4: Graph list endpoint
echo -e "${BLUE}4. Graph List Test${NC}"
run_test "GET /api/graph/list" "$API_BASE/graph/list"

# Test 5: Fetch graph for address (should create a new graph)
echo -e "${BLUE}5. Fetch Graph Test${NC}"
test_address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
test_data="{\"address\": \"$test_address\", \"tx_limit\": 10}"
run_test "POST /api/graph/address" "$API_BASE/graph/address" "POST" "$test_data"

# Test 6: List graphs again (should now have at least one)
echo -e "${BLUE}6. List Graphs After Creation${NC}"
run_test "GET /api/graph/list" "$API_BASE/graph/list"

# Test 7: Get specific graph
echo -e "${BLUE}7. Get Specific Graph Test${NC}"
# First get the list to find a graph name
graph_list_response=$(curl -s "$API_BASE/graph/list")
if echo "$graph_list_response" | grep -q "graph_"; then
    graph_name=$(echo "$graph_list_response" | grep -o 'graph_[^"]*' | head -1)
    if [ -n "$graph_name" ]; then
        run_test "GET /api/graph/get?name=$graph_name" "$API_BASE/graph/get?name=$graph_name"
    else
        echo -e "${YELLOW}SKIP${NC} - No graph files found to test"
        echo ""
    fi
else
    echo -e "${YELLOW}SKIP${NC} - No graph files found to test"
    echo ""
fi

# Test 8: Analyze address
echo -e "${BLUE}8. Analyze Address Test${NC}"
analyze_data="{\"address\": \"$test_address\", \"blockchain\": \"btc\", \"generate_visualizations\": false}"
run_test "POST /api/analyze" "$API_BASE/analyze" "POST" "$analyze_data"

# Test 9: Batch analyze
echo -e "${BLUE}9. Batch Analyze Test${NC}"
batch_data="{\"addresses\": [\"$test_address\"], \"blockchain\": \"btc\"}"
run_test "POST /api/analyze/batch" "$API_BASE/analyze/batch" "POST" "$batch_data"

# Test 10: Export to Gephi
echo -e "${BLUE}10. Export to Gephi Test${NC}"
run_test "GET /api/export/gephi?address=$test_address" "$API_BASE/export/gephi?address=$test_address"

# Test 11: Risk report
echo -e "${BLUE}11. Risk Report Test${NC}"
risk_data="{\"addresses\": [\"$test_address\"]}"
run_test "POST /api/report/risk" "$API_BASE/report/risk" "POST" "$risk_data"

# Test 12: Get analyzed addresses
echo -e "${BLUE}12. Get Analyzed Addresses Test${NC}"
run_test "GET /api/addresses" "$API_BASE/addresses"

# Test 13: Get statistics
echo -e "${BLUE}13. Get Statistics Test${NC}"
run_test "GET /api/statistics" "$API_BASE/statistics"

# Test 14: Frontend serving
echo -e "${BLUE}14. Frontend Serving Test${NC}"
run_test "GET / (frontend)" "$BASE_URL/"

# Test 15: Static file serving
echo -e "${BLUE}15. Static File Serving Test${NC}"
run_test "GET /static (static files)" "$BASE_URL/static"

# Summary
echo "========================"
echo "Smoke Test Results:"
echo -e "✅ Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "❌ Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Backend is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    exit 1
fi
