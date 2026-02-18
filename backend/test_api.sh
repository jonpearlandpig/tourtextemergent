#!/bin/bash

# TourText API Testing Script
API="http://localhost:8001/api"

echo "========================================="
echo "TourText API v4.1 - Test Suite"
echo "========================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
curl -s "$API/" | jq .
echo ""

# Test 2: Create Tour
echo "Test 2: Create Tour"
TOUR_RESPONSE=$(curl -s -X POST "$API/tours" \
  -H "Content-Type: application/json" \
  -d '{
    "tour_name": "Test Tour 2026",
    "tour_code": "TEST26",
    "start_date": "2026-03-01T00:00:00Z",
    "multi_tour_access": false
  }')

echo "$TOUR_RESPONSE" | jq .
TOUR_ID=$(echo "$TOUR_RESPONSE" | jq -r '.id')
echo "Tour ID: $TOUR_ID"
echo ""

# Test 3: List Tours
echo "Test 3: List Tours"
curl -s "$API/tours" | jq .
echo ""

# Test 4: Get Specific Tour
echo "Test 4: Get Tour by ID"
curl -s "$API/tours/$TOUR_ID" | jq .
echo ""

# Test 5: Test Query (will fail due to no truth records, but tests pipeline)
echo "Test 5: Test Query Processing"
curl -s -X POST "$API/query" \
  -H "Content-Type: application/json" \
  -d '{
    "tour_code": "TEST26",
    "query": "What time is load-in tomorrow?",
    "phone_number": "+1234567890"
  }' | jq .
echo ""

# Test 6: List Invocations
echo "Test 6: List Invocations"
curl -s "$API/tours/$TOUR_ID/invocations" | jq .
echo ""

# Test 7: List Escalations
echo "Test 7: List Escalations"
curl -s "$API/tours/$TOUR_ID/escalations" | jq .
echo ""

echo "========================================="
echo "Test Suite Complete!"
echo "========================================="
