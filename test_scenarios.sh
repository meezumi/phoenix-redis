#!/bin/bash

echo "=== Project Phoenix Fraud Detection Test Scenarios ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000/transaction"

# Test 1: High Velocity Fraud
echo -e "${YELLOW}Test 1: High Velocity Fraud Detection${NC}"
echo "Sending 12 rapid transactions from the same user..."
for i in {1..12}; do
  curl -s -X POST -H "Content-Type: application/json" -d '{
    "user_id": "user-velocity-test",
    "card_id": "card-velocity",
    "device_id": "device-velocity",
    "amount": 10.00,
    "merchant": "Gas Station"
  }' $API_URL > /dev/null
  echo -n "."
done
echo ""
echo -e "${GREEN}✓ Sent 12 transactions. Check frontend for High Transaction Velocity alerts.${NC}"
echo ""
sleep 2

# Test 2: Fraud Ring Detection
echo -e "${YELLOW}Test 2: Fraud Ring Detection${NC}"
echo "Sending transaction from user 1 on shared device..."
curl -s -X POST -H "Content-Type: application/json" -d '{
  "user_id": "alice",
  "card_id": "card-alice",
  "device_id": "shared-device-999",
  "amount": 200.00,
  "merchant": "Electronics Store"
}' $API_URL > /dev/null
echo -e "${GREEN}✓ Transaction 1 sent (alice)${NC}"
sleep 1

echo "Sending transaction from user 2 on SAME device..."
curl -s -X POST -H "Content-Type: application/json" -d '{
  "user_id": "bob",
  "card_id": "card-bob",
  "device_id": "shared-device-999",
  "amount": 75.50,
  "merchant": "Restaurant"
}' $API_URL > /dev/null
echo -e "${GREEN}✓ Transaction 2 sent (bob)${NC}"
echo -e "${RED}✓ Fraud Ring should be detected! Check frontend.${NC}"
echo ""
sleep 1

echo "Sending transaction from user 3 on SAME device..."
curl -s -X POST -H "Content-Type: application/json" -d '{
  "user_id": "charlie",
  "card_id": "card-charlie",
  "device_id": "shared-device-999",
  "amount": 45.00,
  "merchant": "Coffee Shop"
}' $API_URL > /dev/null
echo -e "${GREEN}✓ Transaction 3 sent (charlie)${NC}"
echo -e "${RED}✓ Another Fraud Ring alert should appear!${NC}"
echo ""

# Test 3: Normal Transaction (No Fraud)
echo -e "${YELLOW}Test 3: Normal Transaction (No Fraud)${NC}"
echo "Sending a single transaction from a new user..."
curl -s -X POST -H "Content-Type: application/json" -d '{
  "user_id": "normal-user-123",
  "card_id": "card-normal",
  "device_id": "device-normal",
  "amount": 50.00,
  "merchant": "Grocery Store"
}' $API_URL > /dev/null
echo -e "${GREEN}✓ Normal transaction sent. No alerts should appear.${NC}"
echo ""

echo "=== All tests completed! ==="
echo -e "Open ${GREEN}http://localhost:3000${NC} to view the fraud detection dashboard."
echo -e "Redis Insight: ${GREEN}http://localhost:8001${NC}"
