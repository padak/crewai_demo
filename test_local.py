#!/usr/bin/env python3
"""
Local test script for CrewAI Content Orchestrator
This script tests the create_content_with_hitl function directly without going through the API
"""

import os
import sys
import logging
from orchestrator_service import create_content_with_hitl

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    # Test topic
    topic = "Artificial Intelligence"
    
    print(f"\n{'='*50}")
    print(f"Testing create_content_with_hitl with topic: {topic}")
    print(f"{'='*50}\n")
    
    try:
        # Call the function directly
        result = create_content_with_hitl(
            topic=topic,
            feedback=None,
            require_approval=False
        )
        
        print(f"\n{'='*50}")
        print(f"Result status: {result.get('status', 'unknown')}")
        print(f"{'='*50}\n")
        
        # Print the content
        if 'content' in result:
            print(f"Content length: {result.get('length', 0)} characters")
            print(f"\n{result['content']}\n")
        else:
            print("No content found in result")
            print(f"Result: {result}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 