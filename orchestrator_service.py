from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@CrewBase
class ContentCreationCrew:
    """Content creation crew for generating articles with optional human feedback"""

    def __init__(self, inputs=None):
        """Initialize the crew with inputs"""
        self.inputs = inputs or {}
        logger.info(f"ContentCreationCrew initialized with inputs: {self.inputs}")

    @agent
    def research_agent(self) -> Agent:
        """Creates a research agent for gathering information"""
        return Agent(
            role="Research Specialist",
            goal="Find comprehensive and accurate information on the given topic",
            backstory="You are an expert researcher with years of experience gathering information on various topics.",
            llm=self._get_llm(),
            tools=[],
            verbose=True,
        )

    @agent
    def writer_agent(self) -> Agent:
        """Creates a writer agent for content creation"""
        return Agent(
            role="Content Writer",
            goal="Create engaging and informative content based on research",
            backstory="You are a skilled writer who can transform research into compelling content.",
            llm=self._get_llm(),
            verbose=True,
        )

    @agent
    def editor_agent(self) -> Agent:
        """Creates an editor agent for refining content"""
        return Agent(
            role="Content Editor",
            goal="Polish and refine content to ensure quality and accuracy",
            backstory="You are a meticulous editor with an eye for detail and quality.",
            llm=self._get_llm(),
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        """Creates a research task for the given topic"""
        # Get topic from inputs
        topic = (
            self.inputs.get("topic")
            if hasattr(self, "inputs") and self.inputs
            else None
        )

        if not topic:
            topic = "General Knowledge"
            logger.warning("No topic provided, defaulting to 'General Knowledge'")

        logger.info(f"Creating research task for topic: {topic}")

        return Task(
            description=f"Research the topic: {topic}. Find comprehensive information including recent developments, key concepts, and relevant examples.",
            expected_output="A detailed research report with key findings and insights",
            agent=self.research_agent(),
            human_input=False,
        )

    @task
    def writing_task(self) -> Task:
        """Creates a writing task based on research findings"""
        return Task(
            description="Using the research provided, create engaging and informative content on the topic.",
            expected_output="A well-structured draft article with clear sections and engaging content",
            agent=self.writer_agent(),
            context=[self.research_task()],
            human_input=False,
        )

    @task
    def editing_task(self) -> Task:
        """Creates an editing task for final content polishing"""
        return Task(
            description="Review and polish the content to ensure quality, accuracy, and readability.",
            expected_output="A polished, final version of the content ready for publication",
            agent=self.editor_agent(),
            context=[self.writing_task()],
            human_input=False,
        )

    @task
    def editing_with_feedback_task(self) -> Task:
        """Creates an editing task that incorporates human feedback"""
        # Get feedback from inputs
        feedback = (
            self.inputs.get("feedback")
            if hasattr(self, "inputs") and self.inputs
            else None
        )

        if not feedback:
            feedback = "Please improve the content."

        logger.info(f"Creating editing task with feedback: {feedback}")

        return Task(
            description=f"Review and polish the content to ensure quality, accuracy, and readability. Incorporate the following human feedback: {feedback}",
            expected_output="A polished, final version of the content that addresses human feedback",
            agent=self.editor_agent(),
            context=[self.writing_task()],
            human_input=False,
        )

    @crew
    def content_crew(self) -> Crew:
        """Creates the standard content creation crew"""
        # Log the topic being used
        topic = (
            self.inputs.get("topic")
            if hasattr(self, "inputs") and self.inputs
            else None
        )
        logger.info(f"Creating content crew for topic: {topic or 'General Knowledge'}")

        # Create tasks
        research = self.research_task()
        writing = self.writing_task()
        editing = self.editing_task()

        return Crew(
            agents=[self.research_agent(), self.writer_agent(), self.editor_agent()],
            tasks=[research, writing, editing],
            process=Process.sequential,
            verbose=True,
        )

    @crew
    def content_crew_with_feedback(self) -> Crew:
        """Creates a content creation crew that incorporates human feedback"""
        # Log the topic and feedback being used
        topic = (
            self.inputs.get("topic")
            if hasattr(self, "inputs") and self.inputs
            else None
        )
        feedback = (
            self.inputs.get("feedback")
            if hasattr(self, "inputs") and self.inputs
            else None
        )
        logger.info(
            f"Creating content crew with feedback for topic: {topic or 'General Knowledge'}"
        )
        logger.info(f"Feedback to incorporate: {feedback or 'None provided'}")

        # Create tasks
        research = self.research_task()
        writing = self.writing_task()
        editing = self.editing_with_feedback_task()

        return Crew(
            agents=[self.research_agent(), self.writer_agent(), self.editor_agent()],
            tasks=[research, writing, editing],
            process=Process.sequential,
            verbose=True,
        )

    def _get_llm(self):
        """Helper method to create a consistent LLM configuration"""
        # Determine which LLM provider to use
        llm_provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
        
        if llm_provider == "azure":
            # Azure OpenAI configuration
            api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
            deployment_id = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-35-turbo-0125")
            
            if not api_key or not azure_endpoint:
                raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set for Azure OpenAI")
            
            logger.info(f"Using Azure OpenAI with deployment_id: {deployment_id}")
            
            # For Azure OpenAI, we use the deployment_id as the model name
            return ChatOpenAI(
                model=deployment_id,
                openai_api_key=api_key,
                openai_api_version=api_version,
                azure_endpoint=azure_endpoint,
                azure_deployment=deployment_id,
                temperature=0.7,
            )
        else:
            # Default to OpenRouter
            api_key = os.environ.get("OPENROUTER_API_KEY")
            base_url = os.environ.get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
            model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
            
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY must be set for OpenRouter")
            
            logger.info(f"Using OpenRouter with model: {model}")
            
            return ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                base_url=base_url,
                temperature=0.7,
                default_headers={
                    "HTTP-Referer": "https://github.com/crewai",
                    "X-Title": "CrewAI Demo",
                }
            )


# API-compatible functions
def create_content_with_hitl(
    topic: str, feedback: str = None, require_approval: bool = True
) -> Dict[str, Any]:
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
        # Prepare inputs
        inputs = {"topic": topic}
        if feedback:
            inputs["feedback"] = feedback

        logger.info(f"Creating ContentCreationCrew instance with inputs: {inputs}")
        crew_instance = ContentCreationCrew(inputs=inputs)

        if feedback:
            logger.info(f"Incorporating human feedback: {feedback}")

            # Use the content_crew_with_feedback method
            logger.info("Getting content_crew_with_feedback method")
            crew_method = crew_instance.content_crew_with_feedback
            logger.info(
                f"Using content_crew_with_feedback method, type: {type(crew_method)}"
            )
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
        logger.info(f"Calling kickoff with inputs already in crew instance")
        result = crew.kickoff()
        logger.info(f"Kickoff result type: {type(result).__name__}")
        logger.info(f"Kickoff result: {result}")

        # Convert result to string
        logger.info("Converting result to string")
        if hasattr(result, "raw"):
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
                "feedback_incorporated": feedback is not None,
            }
        else:
            # Otherwise, set status to needs_approval for HITL workflow
            logger.info("Approval required, returning needs_approval")
            return {
                "status": "needs_approval",
                "content": content,
                "length": len(content),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error in content creation: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": e.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
        }


def get_status() -> Dict[str, Any]:
    """
    Get the current status of the service.
    """
    return {"status": "running", "timestamp": datetime.now().isoformat()}
