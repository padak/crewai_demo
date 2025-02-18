from crewai import Task
from textwrap import dedent

def create_research_task(agent):
    return Task(
        description=dedent("""
            Research the topic 'The Future of Artificial Intelligence in Healthcare'
            Focus on:
            1. Current AI applications in healthcare
            2. Emerging trends and technologies
            3. Potential impact on patient care
            4. Challenges and ethical considerations
            
            Provide a comprehensive research summary with key points and statistics.
        """),
        expected_output="A detailed research summary about AI in Healthcare with current applications, trends, impacts, and challenges.",
        agent=agent
    )

def create_writing_task(agent):
    return Task(
        description=dedent("""
            Using the research provided, create a compelling blog post about
            'The Future of AI in Healthcare'. The post should:
            1. Have an engaging introduction
            2. Cover all key points from the research
            3. Include relevant examples and statistics
            4. Be approximately 1000 words
            
            Focus on making complex information accessible to a general audience.
        """),
        expected_output="A well-structured, engaging 1000-word blog post about AI in Healthcare.",
        agent=agent
    )

def create_editing_task(agent):
    return Task(
        description=dedent("""
            Review and optimize the blog post. Focus on:
            1. Grammar and clarity
            2. Content structure and flow
            3. SEO optimization
            4. Engagement factors
            
            Provide the final, polished version of the blog post with any necessary
            improvements.
        """),
        expected_output="A polished, SEO-optimized final version of the blog post with improved clarity and engagement.",
        agent=agent
    ) 