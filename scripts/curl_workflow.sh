#!/bin/bash
# CrewAI Content Orchestrator API - curl workflow example
# This script demonstrates a complete workflow using curl

# Configuration
API_URL="https://flask-550.hub.canary-orion.keboola.dev"
TOPIC="Renewable Energy"
REQUIRE_APPROVAL=true
USE_WEBHOOK=false
WEBHOOK_URL="http://localhost:8889/webhook"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}CrewAI Content Orchestrator API - curl workflow example${NC}"
echo "========================================================"
echo ""

# Check if API is running
echo -e "${YELLOW}Checking if API is running...${NC}"
HEALTH_CHECK=$(curl -s $API_URL/health)
if [[ $HEALTH_CHECK == *"healthy"* ]]; then
  echo -e "${GREEN}API is running!${NC}"
else
  echo -e "${RED}API is not running or not accessible. Response: ${HEALTH_CHECK}${NC}"
  exit 1
fi

echo ""
echo -e "${YELLOW}Starting a new content generation job...${NC}"

# Prepare the payload
if [ "$USE_WEBHOOK" = true ]; then
  PAYLOAD="{\"crew\":\"ContentCreationCrew\",\"inputs\":{\"topic\":\"$TOPIC\",\"require_approval\":$REQUIRE_APPROVAL},\"webhook_url\":\"$WEBHOOK_URL\"}"
  echo "Using webhook for notifications: $WEBHOOK_URL"
else
  PAYLOAD="{\"crew\":\"ContentCreationCrew\",\"inputs\":{\"topic\":\"$TOPIC\",\"require_approval\":$REQUIRE_APPROVAL}}"
fi

# Start a job
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

# Poll for job status
echo -e "${YELLOW}Polling for job status...${NC}"
MAX_POLLS=30
POLL_COUNT=0
STATUS="unknown"

while [ $POLL_COUNT -lt $MAX_POLLS ]; do
  POLL_COUNT=$((POLL_COUNT+1))
  echo "Poll attempt $POLL_COUNT/$MAX_POLLS..."
  
  JOB_STATUS=$(curl -s $API_URL/job/$JOB_ID)
  STATUS=$(echo $JOB_STATUS | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  
  echo "Current status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo -e "${GREEN}Job completed successfully!${NC}"
    CONTENT=$(echo $JOB_STATUS | grep -o '"content":"[^"]*' | cut -d'"' -f4)
    echo "Content: ${CONTENT:0:100}..." # Show first 100 chars
    break
  elif [ "$STATUS" = "error" ]; then
    echo -e "${RED}Job failed with error.${NC}"
    break
  elif [ "$STATUS" = "pending_approval" ]; then
    echo -e "${BLUE}Job is waiting for human approval.${NC}"
    
    # If require_approval is true, provide feedback or approve
    if [ "$REQUIRE_APPROVAL" = true ]; then
      echo ""
      echo -e "${YELLOW}Providing feedback...${NC}"
      
      # You can change this to approved: true to approve instead
      FEEDBACK_PAYLOAD="{\"feedback\":\"Please add more examples about solar power.\",\"approved\":false}"
      
      FEEDBACK_RESPONSE=$(curl -s -X POST $API_URL/job/$JOB_ID/feedback \
        -H "Content-Type: application/json" \
        -d "$FEEDBACK_PAYLOAD")
      
      echo "Feedback response: $FEEDBACK_RESPONSE"
      echo ""
      echo -e "${YELLOW}Continuing to poll for updated content...${NC}"
      
      # Reset poll count to continue monitoring
      POLL_COUNT=0
      MAX_POLLS=15
    fi
  fi
  
  # Wait before polling again
  sleep 5
done

if [ $POLL_COUNT -ge $MAX_POLLS ]; then
  echo -e "${RED}Reached maximum number of polling attempts. Job may still be processing.${NC}"
  echo -e "${YELLOW}You can check the job status manually:${NC}"
  echo "curl $API_URL/job/$JOB_ID"
fi

echo ""
echo -e "${BLUE}Workflow completed!${NC}"
echo "========================================================" 