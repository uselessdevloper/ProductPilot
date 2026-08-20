#!/bin/bash

echo "=================================================="
echo "ProductPilot AI - Frontend Integration Test"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if pipeline report exists
echo -e "${YELLOW}Test 1: Checking if pipeline report exists...${NC}"
if [ -f "backend/agent/agent_observability_report.md" ]; then
    echo -e "${GREEN}✓ Pipeline report found${NC}"
else
    echo -e "${RED}✗ Pipeline report not found${NC}"
    echo "  Run: cd backend/agent && python run.py"
fi
echo ""

# Test 2: Check backend server availability
echo -e "${YELLOW}Test 2: Testing backend API endpoints...${NC}"
if command -v curl &> /dev/null; then
    # Test pipeline results endpoint
    echo "  Testing /api/productpilot/pipeline-results..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8787/api/productpilot/pipeline-results 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Pipeline results API working (HTTP 200)${NC}"
    else
        echo -e "${RED}✗ Pipeline results API not responding (HTTP $HTTP_CODE)${NC}"
        echo "  Start server: cd backend/productpilotai && python server.py"
    fi
    
    # Test logo mappings endpoint
    echo "  Testing /api/productpilot/source-logos..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8787/api/productpilot/source-logos 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Source logos API working (HTTP 200)${NC}"
    else
        echo -e "${RED}✗ Source logos API not responding (HTTP $HTTP_CODE)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ curl not available, skipping API tests${NC}"
fi
echo ""

# Test 3: Check frontend files
echo -e "${YELLOW}Test 3: Verifying frontend files...${NC}"
if grep -q "getSourceLogo" frontend/productpilotai/src/data.js; then
    echo -e "${GREEN}✓ Logo helper function found in data.js${NC}"
else
    echo -e "${RED}✗ Logo helper function missing${NC}"
fi

if grep -q "renderPipelineResults" frontend/productpilotai/src/main.js; then
    echo -e "${GREEN}✓ Pipeline results renderer found in main.js${NC}"
else
    echo -e "${RED}✗ Pipeline results renderer missing${NC}"
fi

if grep -q "pp-agent-trace-card" frontend/productpilotai/src/styles.css; then
    echo -e "${GREEN}✓ Pipeline results styles found in styles.css${NC}"
else
    echo -e "${RED}✗ Pipeline results styles missing${NC}"
fi
echo ""

# Test 4: Check backend endpoints
echo -e "${YELLOW}Test 4: Verifying backend endpoints...${NC}"
if grep -q "/api/productpilot/pipeline-results" backend/productpilotai/server.py; then
    echo -e "${GREEN}✓ Pipeline results endpoint found in server.py${NC}"
else
    echo -e "${RED}✗ Pipeline results endpoint missing${NC}"
fi

if grep -q "/api/productpilot/source-logos" backend/productpilotai/server.py; then
    echo -e "${GREEN}✓ Source logos endpoint found in server.py${NC}"
else
    echo -e "${RED}✗ Source logos endpoint missing${NC}"
fi
echo ""

# Test 5: Logo URLs validation
echo -e "${YELLOW}Test 5: Checking logo URL mappings...${NC}"
LOGO_COUNT=$(grep -c "https://upload.wikimedia.org" frontend/productpilotai/src/data.js)
if [ "$LOGO_COUNT" -gt 5 ]; then
    echo -e "${GREEN}✓ Found $LOGO_COUNT Wikipedia logo URLs${NC}"
else
    echo -e "${YELLOW}⚠ Only found $LOGO_COUNT logo URLs${NC}"
fi
echo ""

echo "=================================================="
echo "Integration Test Complete"
echo "=================================================="
echo ""
echo "To run the full system:"
echo "  1. Start backend: cd backend/productpilotai && python server.py"
echo "  2. Run pipeline: cd backend/agent && python run.py"
echo "  3. Open browser: http://localhost:8787"
echo "  4. Navigate to: '🔬 6. Pipeline Results' tab"
echo ""
