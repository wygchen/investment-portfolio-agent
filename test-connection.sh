#!/bin/bash

# Frontend-Backend Connection Test Script
# This script helps verify the connection between frontend and backend

echo "🧪 Testing Frontend-Backend Connection"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if backend is running
echo "1️⃣ Testing Backend Health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null)

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ Backend is online and responding${NC}"
else
    echo -e "${RED}❌ Backend is offline or not responding${NC}"
    echo -e "${YELLOW}   Start backend with: cd backend && python main.py${NC}"
    exit 1
fi

# Test 2: Test process-assessment endpoint exists
echo ""
echo "2️⃣ Testing Process Assessment Endpoint..."
ASSESSMENT_TEST=$(curl -s -X POST http://127.0.0.1:8000/api/process-assessment \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null | grep -o "status" | head -1)

if [ ! -z "$ASSESSMENT_TEST" ]; then
    echo -e "${GREEN}✅ Process assessment endpoint is accessible${NC}"
else
    echo -e "${RED}❌ Process assessment endpoint not responding${NC}"
fi

# Test 3: Check frontend is running
echo ""
echo "3️⃣ Testing Frontend..."
FRONTEND_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)

if [ "$FRONTEND_CHECK" = "200" ] || [ "$FRONTEND_CHECK" = "304" ]; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend may not be running${NC}"
    echo -e "${YELLOW}   Start frontend with: cd frontend && pnpm dev${NC}"
fi

# Test 4: Check CORS
echo ""
echo "4️⃣ Testing CORS Configuration..."
CORS_CHECK=$(curl -s -X OPTIONS http://127.0.0.1:8000/api/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -I 2>/dev/null | grep -i "access-control-allow-origin")

if [ ! -z "$CORS_CHECK" ]; then
    echo -e "${GREEN}✅ CORS is properly configured${NC}"
else
    echo -e "${YELLOW}⚠️  CORS headers not detected (may still work)${NC}"
fi

# Summary
echo ""
echo "========================================"
echo "📊 Test Summary"
echo "========================================"
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Next steps:"
echo "1. Go to http://localhost:3000/assessment"
echo "2. Complete the assessment form"
echo "3. Click 'Generate Portfolio'"
echo "4. Check browser console (F12) for detailed logs"
echo ""
echo "Logs to watch for:"
echo "  🚀 Generating portfolio with assessment data"
echo "  📤 Transformed backend data"
echo "  📡 Response status: 200"
echo "  ✅ Backend response received"
echo "  📊 Portfolio data transformed"
echo "  💾 Portfolio saved to localStorage"
