from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@CrewBase
class ContentCreationCrew:
    """Content creation crew for generating articles with optional human feedback"""

    @agent
    def research_agent(self) -> Agent:
        """Creates a research agent for gathering information"""
        return Agent(
            role="Research Specialist",
            goal="Find comprehensive and accurate information on the given topic",
            backstory="You are an expert researcher with years of experience gathering information on various topics.",
            llm=self._get_llm(),
            tools=[],
            verbose=True
        )

    @agent
    def writer_agent(self) -> Agent:
        """Creates a writer agent for content creation"""
        return Agent(
            role="Content Writer",
            goal="Create engaging and informative content based on research",
            backstory="You are a skilled writer who can transform research into compelling content.",
            llm=self._get_llm(),
            verbose=True
        )

    @agent
    def editor_agent(self) -> Agent:
        """Creates an editor agent for refining content"""
        return Agent(
            role="Content Editor",
            goal="Polish and refine content to ensure quality and accuracy",
            backstory="You are a meticulous editor with an eye for detail and quality.",
            llm=self._get_llm(),
            verbose=True
        )

    @task
    def research_task(self, topic: str) -> Task:
        """Creates a research task for the given topic"""
        return Task(
            description=f"Research the topic: {topic}. Find comprehensive information including recent developments, key concepts, and relevant examples.",
            expected_output="A detailed research report with key findings and insights",
            agent=self.research_agent()
        )

    @task
    def writing_task(self) -> Task:
        """Creates a writing task based on research findings"""
        return Task(
            description="Using the research provided, create engaging and informative content on the topic.",
            expected_output="A well-structured draft article with clear sections and engaging content",
            agent=self.writer_agent(),
            context=[self.research_task]
        )

    @task
    def editing_task(self) -> Task:
        """Creates an editing task for final content polishing"""
        return Task(
            description="Review and polish the content to ensure quality, accuracy, and readability.",
            expected_output="A polished, final version of the content ready for publication",
            agent=self.editor_agent(),
            context=[self.writing_task]
        )

    @task
    def editing_with_feedback_task(self, feedback: str) -> Task:
        """Creates an editing task that incorporates human feedback"""
        return Task(
            description=f"Review and polish the content to ensure quality, accuracy, and readability. Incorporate the following human feedback: {feedback}",
            expected_output="A polished, final version of the content that addresses human feedback",
            agent=self.editor_agent(),
            context=[self.writing_task]
        )

    @crew
    def content_crew(self) -> Crew:
        """Creates the standard content creation crew"""
        return Crew(
            agents=[self.research_agent(), self.writer_agent(), self.editor_agent()],
            tasks=[self.research_task, self.writing_task, self.editing_task],
            process=Process.sequential,
            verbose=True
        )

    @crew
    def content_crew_with_feedback(self) -> Crew:
        """Creates a content creation crew that incorporates human feedback"""
        return Crew(
            agents=[self.research_agent(), self.writer_agent(), self.editor_agent()],
            tasks=[self.research_task, self.writing_task, self.editing_with_feedback_task],
            process=Process.sequential,
            verbose=True
        )

    def _get_llm(self):
        """Helper method to create a consistent LLM configuration"""
        return ChatOpenAI(
            model="openrouter/openai/gpt-4o-mini",
            openai_api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            model_kwargs={
                "headers": {
                    "HTTP-Referer": "https://github.com/crewai",
                    "X-Title": "CrewAI Demo",
                }
            },
        )

# API-compatible functions
def create_content_with_hitl(topic: str, feedback: str = None) -> Dict[str, Any]:
    """
    Content creation function with human-in-the-loop capability
    Args:
        topic: The topic to create content about
        feedback: Optional human feedback for refinement
    Returns:
        Dictionary with content, execution details, and human approval status
    """
    logger.info(f"Starting content creation with HITL for topic: {topic}")
    
    try:
        crew_instance = ContentCreationCrew()
        
        if feedback:
            logger.info(f"Incorporating human feedback: {feedback}")
            # Run with feedback
            result = crew_instance.content_crew_with_feedback().kickoff(
                inputs={"topic": topic, "feedback": feedback}
            )
            
            # Convert result to string
            if hasattr(result, 'raw'):
                content = str(result.raw)
            else:
                content = str(result)
                
            return {
                "status": "success",
                "content": content,
                "length": len(content),
                "timestamp": datetime.now().isoformat(),
                "feedback_incorporated": True
            }
        else:
            # Initial run without feedback
            result = crew_instance.content_crew().kickoff(
                inputs={"topic": topic}
            )
            
            # Convert result to string
            if hasattr(result, 'raw'):
                content = str(result.raw)
            else:
                content = str(result)
                
            return {
                "status": "needs_approval",
                "content": content,
                "length": len(content),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error in content creation with HITL: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": e.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        }

def get_status() -> Dict[str, Any]:
    """
    Get the current status of the service.
    """
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }
