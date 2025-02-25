#!/bin/bash
# Script to check the status of multiple jobs

# Configuration
API_URL="https://flask-550.hub.canary-orion.keboola.dev"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Job IDs to check
DIRECT_JOB_ID="987ca65a-62cf-4c48-850b-ad0eb3e37393"
HITL_JOB_ID="d7337f89-5508-43e5-b465-5fd3c1452cfa"

echo -e "${BLUE}CrewAI Content Orchestrator - Job Status Checker${NC}"
echo "=================================================="
echo ""

# Function to check job status
check_job() {
  local job_id=$1
  local job_type=$2
  
  echo -e "${YELLOW}Checking $job_type job status (ID: $job_id):${NC}"
  local response=$(curl -s $API_URL/job/$job_id)
  local status=$(echo $response | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  
  echo -e "Status: ${GREEN}$status${NC}"
  
  # If job is completed, show content
  if [[ "$status" == "completed" ]]; then
    local content=$(echo $response | grep -o '"content":"[^"]*' | cut -d'"' -f4)
    if [[ ! -z "$content" ]]; then
      echo -e "${BLUE}Content preview:${NC}"
      echo "${content:0:200}..." # Show first 200 chars
    fi
  fi
  
  # If job is pending approval, show instructions
  if [[ "$status" == "pending_approval" ]]; then
    echo -e "${YELLOW}This job is waiting for approval. You can:${NC}"
    echo "1. Approve the content:"
    echo "   curl -X POST $API_URL/job/$job_id/feedback -H \"Content-Type: application/json\" -d '{\"feedback\":\"Content approved as is.\",\"approved\":true}'"
    echo ""
    echo "2. Provide feedback:"
    echo "   curl -X POST $API_URL/job/$job_id/feedback -H \"Content-Type: application/json\" -d '{\"feedback\":\"Please improve this content by...\",\"approved\":false}'"
  fi
  
  echo ""
}

# Check both jobs
check_job $DIRECT_JOB_ID "Direct mode"
check_job $HITL_JOB_ID "HITL mode"

echo -e "${BLUE}To run this check again:${NC}"
echo "./check_jobs.sh"
echo ""
echo "==================================================" 