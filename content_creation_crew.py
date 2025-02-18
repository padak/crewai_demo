from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from crewai import Crew
from langchain_openai import ChatOpenAI

# Import agents
from agents.research_agent import create_research_agent
from agents.writer_agent import create_writer_agent
from agents.editor_agent import create_editor_agent

# Import tasks
from tasks.content_tasks import (
    create_research_task,
    create_writing_task,
    create_editing_task
)

def main():
    # Configure the LLM to use OpenRouter
    llm = ChatOpenAI(
        model="openai/gpt-4-turbo",
        openai_api_key=os.environ["OPENROUTER_API_KEY"],
        openai_api_base=os.environ["OPENAI_API_BASE"],
        model_kwargs={
            "headers": {
                "HTTP-Referer": "https://github.com/crewai",
                "X-Title": "CrewAI Demo"
            }
        }
    )

    # Create agents
    research_agent = create_research_agent(llm)
    writer_agent = create_writer_agent(llm)
    editor_agent = create_editor_agent(llm)

    # Create tasks
    research_task = create_research_task(research_agent)
    writing_task = create_writing_task(writer_agent)
    editing_task = create_editing_task(editor_agent)

    # Create the crew
    content_crew = Crew(
        agents=[research_agent, writer_agent, editor_agent],
        tasks=[research_task, writing_task, editing_task],
        verbose=True
    )

    # Run the crew
    result = content_crew.kickoff()
    print("\n🎯 Final Result:")
    print(result)

if __name__ == "__main__":
    main() 