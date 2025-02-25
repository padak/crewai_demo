#!/bin/bash
# HITL mode content generation example

# Configuration
API_URL="https://flask-550.hub.canary-orion.keboola.dev"
TOPIC="Climate Change"
USE_WEBHOOK=false
WEBHOOK_URL="http://localhost:8889/webhook"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}CrewAI Content Orchestrator - HITL Mode Example${NC}"
echo "=================================================="
echo ""
echo -e "Generating content on topic: ${GREEN}$TOPIC${NC}"
echo "API URL: $API_URL"
echo ""

# Prepare the payload
if [ "$USE_WEBHOOK" = true ]; then
  PAYLOAD="{\"crew\":\"ContentCreationCrew\",\"inputs\":{\"topic\":\"$TOPIC\",\"require_approval\":true},\"webhook_url\":\"$WEBHOOK_URL\"}"
  echo -e "${YELLOW}Using webhook for notifications: $WEBHOOK_URL${NC}"
else
  PAYLOAD="{\"crew\":\"ContentCreationCrew\",\"inputs\":{\"topic\":\"$TOPIC\",\"require_approval\":true}}"
fi

# Start a job
echo -e "${YELLOW}Sending request...${NC}"
RESPONSE=$(curl -s -X POST $API_URL/kickoff \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "Response: $RESPONSE"

# Extract job ID
JOB_ID=$(echo $RESPONSE | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
  echo -e "${RED}Failed to get job ID. Exiting.${NC}"
  exit 1
fi

echo -e "${GREEN}Job started with ID: $JOB_ID${NC}"
echo ""

# Check job status immediately
echo -e "${YELLOW}Checking initial job status:${NC}"
curl -s $API_URL/job/$JOB_ID
echo ""
echo ""

echo -e "${YELLOW}To check job status again:${NC}"
echo "curl $API_URL/job/$JOB_ID"
echo ""
echo -e "${YELLOW}To approve content when status is 'pending_approval':${NC}"
echo "curl -X POST $API_URL/job/$JOB_ID/feedback -H \"Content-Type: application/json\" -d '{\"feedback\":\"Content approved as is.\",\"approved\":true}'"
echo ""
echo -e "${YELLOW}To provide feedback when status is 'pending_approval':${NC}"
echo "curl -X POST $API_URL/job/$JOB_ID/feedback -H \"Content-Type: application/json\" -d '{\"feedback\":\"Please improve this content by...\",\"approved\":false}'"
echo ""
echo "==================================================" 