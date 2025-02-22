from textwrap import dedent
from crewai import Task

def create_research_task(agent, topic: str) -> Task:
    return Task(
        description=dedent(f"""
            Research the topic '{topic}'
            Focus on:
            1. Current applications and state of the art
            2. Emerging trends and technologies
            3. Potential impact and implications
            4. Challenges and considerations
            
            Provide a comprehensive research summary with key points and statistics.
        """),
        expected_output=f"[Research Summary] Comprehensive analysis of {topic}, including current state, trends, impacts, and challenges.",
        agent=agent,
        async_execution=False  # Run synchronously to maintain order
    )

def create_writing_task(agent) -> Task:
    return Task(
        description=dedent("""
            Using the research provided, create a compelling blog post.
            The post should:
            1. Have an engaging introduction
            2. Cover all key points from the research
            3. Include relevant examples and statistics
            4. Be approximately 200 words
            
            Focus on making complex information accessible to a general audience.
        """),
        expected_output="[Blog Post Draft] A well-structured, engaging blog post based on the research findings.",
        agent=agent,
        async_execution=False  # Run synchronously to maintain order
    )

def create_editing_task(agent) -> Task:
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
        expected_output="[Final Post] A polished, SEO-optimized blog post with improved clarity and engagement.",
        agent=agent,
        async_execution=False  # Run synchronously to maintain order
    ) 