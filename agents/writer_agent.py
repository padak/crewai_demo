from crewai import Agent
from textwrap import dedent

def create_writer_agent(llm):
    return Agent(
        role='Content Writer',
        goal='Create engaging and informative blog content',
        backstory=dedent("""
            You are a skilled content writer with years of experience in creating
            compelling blog posts. You excel at turning complex information into
            reader-friendly content while maintaining accuracy and engagement.
        """),
        llm=llm
    ) 