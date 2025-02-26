#!/bin/bash
# Direct mode content generation example

# Configuration
API_URL="https://flask-550.hub.canary-orion.keboola.dev"
TOPIC="Artificial Intelligence"

echo "CrewAI Content Orchestrator - Direct Mode Example"
echo "=================================================="
echo ""
echo "Generating content on topic: $TOPIC"
echo "API URL: $API_URL"
echo ""

# Make the API call without wait=true for asynchronous execution
echo "Sending request..."
curl -X POST $API_URL/kickoff \
  -H "Content-Type: application/json" \
  -d "{
    \"crew\": \"ContentCreationCrew\",
    \"inputs\": {
      \"topic\": \"$TOPIC\",
      \"require_approval\": false
    }
  }"

echo ""
echo "=================================================="
echo "Request completed. The job is now running in the background."
echo "Use the job ID from the response to check status with:"
echo "curl $API_URL/job/YOUR_JOB_ID" 