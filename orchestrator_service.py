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
    def research_task(self, inputs=None) -> Task:
        """Creates a research task for the given topic"""
        inputs = inputs or {}
        topic = inputs.get("topic", "General Knowledge")
        return Task(
            description=f"Research the topic: {topic}. Find comprehensive information including recent developments, key concepts, and relevant examples.",
            expected_output="A detailed research report with key findings and insights",
            agent=self.research_agent(),
            human_input=False
        )

    @task
    def writing_task(self, inputs=None) -> Task:
        """Creates a writing task based on research findings"""
        inputs = inputs or {}
        return Task(
            description="Using the research provided, create engaging and informative content on the topic.",
            expected_output="A well-structured draft article with clear sections and engaging content",
            agent=self.writer_agent(),
            context=[self.research_task()],
            human_input=False
        )

    @task
    def editing_task(self, inputs=None) -> Task:
        """Creates an editing task for final content polishing"""
        inputs = inputs or {}
        return Task(
            description="Review and polish the content to ensure quality, accuracy, and readability.",
            expected_output="A polished, final version of the content ready for publication",
            agent=self.editor_agent(),
            context=[self.writing_task()],
            human_input=False
        )

    @task
    def editing_with_feedback_task(self, inputs=None) -> Task:
        """Creates an editing task that incorporates human feedback"""
        inputs = inputs or {}
        feedback = inputs.get("feedback", "Please improve the content.")
        return Task(
            description=f"Review and polish the content to ensure quality, accuracy, and readability. Incorporate the following human feedback: {feedback}",
            expected_output="A polished, final version of the content that addresses human feedback",
            agent=self.editor_agent(),
            context=[self.writing_task()],
            human_input=False
        )

    @crew
    def content_crew(self) -> Crew:
        """Creates the standard content creation crew"""
        return Crew(
            agents=[self.research_agent(), self.writer_agent(), self.editor_agent()],
            tasks=[self.research_task(), self.writing_task(), self.editing_task()],
            process=Process.sequential,
            verbose=True
        )

    @crew
    def content_crew_with_feedback(self) -> Crew:
        """Creates a content creation crew that incorporates human feedback"""
        return Crew(
            agents=[self.research_agent(), self.writer_agent(), self.editor_agent()],
            tasks=[self.research_task(), self.writing_task(), self.editing_with_feedback_task()],
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
def create_content_with_hitl(topic: str, feedback: str = None, require_approval: bool = True) -> Dict[str, Any]:
    """
    Content creation function with human-in-the-loop capability
    Args:
        topic: The topic to create content about
        feedback: Optional human feedback for refinement
        require_approval: Whether to require human approval (default: True)
    Returns:
        Dictionary with content, execution details, and human approval status
    """
    logger.info(f"Starting content creation for topic: {topic}")
    
    try:
        logger.info("Creating ContentCreationCrew instance")
        crew_instance = ContentCreationCrew()
        inputs = {"topic": topic}
        
        if feedback:
            logger.info(f"Incorporating human feedback: {feedback}")
            inputs["feedback"] = feedback
            
            # Use the content_crew_with_feedback method
            logger.info("Getting content_crew_with_feedback method")
            crew_method = crew_instance.content_crew_with_feedback
            logger.info(f"Using content_crew_with_feedback method, type: {type(crew_method)}")
        else:
            # Use the content_crew method
            logger.info("Getting content_crew method")
            crew_method = crew_instance.content_crew
            logger.info(f"Using content_crew method, type: {type(crew_method)}")
        
        # Get the crew object
        logger.info(f"Calling crew method to get crew object")
        crew = crew_method()
        if crew is None:
            raise ValueError(f"Crew method returned None instead of a Crew object")
        
        logger.info(f"Got crew object of type: {type(crew).__name__}")
        logger.info(f"Crew object attributes: {dir(crew)}")
        
        # Call kickoff on the crew object
        logger.info(f"Calling kickoff with inputs: {inputs}")
        result = crew.kickoff(inputs=inputs)
        logger.info(f"Kickoff result type: {type(result).__name__}")
        logger.info(f"Kickoff result: {result}")
        
        # Convert result to string
        logger.info("Converting result to string")
        if hasattr(result, 'raw'):
            logger.info("Result has 'raw' attribute")
            content = str(result.raw)
        else:
            logger.info(f"Result does not have 'raw' attribute, using str() conversion")
            content = str(result)
        
        logger.info(f"Content length: {len(content)}")
        
        # If require_approval is False, return the content directly as success
        if not require_approval:
            logger.info("No approval required, returning success")
            return {
                "status": "success",
                "content": content,
                "length": len(content),
                "timestamp": datetime.now().isoformat(),
                "feedback_incorporated": feedback is not None
            }
        else:
            # Otherwise, set status to needs_approval for HITL workflow
            logger.info("Approval required, returning needs_approval")
            return {
                "status": "needs_approval",
                "content": content,
                "length": len(content),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error in content creation: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
