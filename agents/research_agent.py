from crewai import Agent
from textwrap import dedent

def create_research_agent(llm):
    return Agent(
        role='Research Analyst',
        goal='Gather comprehensive information on the given topic',
        backstory=dedent("""
            You are an experienced research analyst with a keen eye for credible information.
            Your expertise lies in gathering, analyzing, and summarizing complex information
            from various sources. You have a talent for identifying key trends and insights.
        """),
        llm=llm
    ) 