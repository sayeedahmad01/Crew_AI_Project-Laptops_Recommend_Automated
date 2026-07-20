import os
from crewai import Agent, Task, Crew, Process, LLM

try:
    from backend.tools import get_dataset_stats_tool, query_laptops_tool
except ModuleNotFoundError:
    from tools import get_dataset_stats_tool, query_laptops_tool

def create_laptop_crew(api_key: str, provider: str, user_profile: dict) -> Crew:
    """
    Create a Crew to analyze user requirements, query the laptop database,
    and generate custom recommendations.
    
    api_key: User provided LLM API Key (OpenAI or Gemini)
    provider: 'openai' or 'gemini'
    user_profile: dict containing budget, major, RAM, etc.
    """
    # Set default keys from env if frontend didn't supply them11
    if not api_key:
        if provider == 'gemini':
            api_key = os.environ.get("GEMINI_API_KEY")
        elif provider == 'openai':
            api_key = os.environ.get("OPENAI_API_KEY")
        elif provider in ('kimi', 'nvidia_kimi'):
            api_key = os.environ.get("NVIDIA_API_KEY")

    if not api_key:
        raise ValueError(f"API Key for {provider} not found. Please provide it in the UI or environment.")

    # Initialize the appropriate LLM
    if provider == 'gemini':
        # Clean model name for crewai LLM class
        llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=api_key,
            temperature=0.3
        )
    elif provider == 'openai':
        llm = LLM(
            model="openai/gpt-4o-mini",
            api_key=api_key,
            temperature=0.3
        )
    elif provider in ('kimi', 'nvidia_kimi'):
        # NVIDIA API gateway for Moonshot AI Kimi model
        llm = LLM(
            model="openai/moonshotai/kimi-k2.6",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
            temperature=0.3
        )
    else:
        # Fallback default
        llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=api_key,
            temperature=0.3
        )

    # Convert user profile to descriptive string for agents
    profile_desc = f"""
    - **Academic Major / Workload**: {user_profile.get('major', 'Student')}
    - **Price Budget**: Max {user_profile.get('budget', 'Any')} INR
    - **Minimum RAM**: {user_profile.get('ram', 'Any')} GB
    - **Preferred Brand**: {user_profile.get('brand', 'Any')}
    - **Preferred OS**: {user_profile.get('os', 'Any')}
    - **Specific Details/Preferences**: {user_profile.get('details', 'None')}
    """

    # Agent 1: Data Specialist Agent
    data_specialist = Agent(
        role="Laptop Database Specialist",
        goal="Search the database using filters to find matching laptops that fit the user's budget and technical constraints.",
        backstory="""You are a meticulous data engineer. Your job is to query the laptop database
        using custom search tools. You look for laptops that fall within the user's budget and meet
        their basic RAM, storage, brand, and OS needs. You gather evidence and output exact product data,
        ensuring that no laptop specs or prices are made up. You always double-check the raw rows before presenting them.""",
        tools=[get_dataset_stats_tool, query_laptops_tool],
        llm=llm,
        verbose=True
    )

    # Agent 2: Recommender Agent
    recommender = Agent(
        role="Academic & Professional Hardware Advisor",
        goal="Select the top 3 best matching laptops from the database search results, and explain how their specifications suit the user's academic major or professional workload.",
        backstory="""You are an expert computing systems consultant and academic advisor.
        You understand hardware inside out. You know that a Computer Science student needs a fast CPU,
        at least 16GB RAM for running Docker/VMs/compilers, and an SSD; a Graphic Designer needs a premium screen
        and strong processor; a business student needs long battery life and portability.
        Your goal is to explain *why* the recommended specs fit the customer's specific studies/workload,
        breaking down the trade-offs (Pros & Cons) of each recommendation in a friendly, persuasive tone.""",
        llm=llm,
        verbose=True
    )

    # Task 1: Search the dataset
    search_task = Task(
        description=f"""
        1. Examine the user profile criteria:
        {profile_desc}
        
        2. First, call the statistics tool to check the dataset stats (price ranges, brand counts) if needed to understand what is available.
        3. Call the 'Query Laptops Dataset' tool with filters representing the user's budget, preferred brand, RAM, and OS to find matching laptops.
        4. If no laptops match the exact combination, relax some filters (e.g. increase the budget slightly, or search for other brands with similar RAM) to find the closest matches.
        5. Compile a list of the matching laptops, keeping their exact price, RAM, Storage, Processor, OS, and rating.
        """,
        expected_output="A markdown table containing the matching laptops retrieved from the database, along with their specifications and prices. Do not invent models or specs.",
        agent=data_specialist
    )

    # Task 2: Formulate recommendations
    recommendation_task = Task(
        description=f"""
        1. Analyze the matching laptops table from the search task.
        2. Choose the top 3 best matching options for the user's profile:
        {profile_desc}
        
        3. Write a comprehensive, personalized recommendation report.
        4. For each laptop, explain:
           - Why the hardware specs (RAM, Storage, Processor, OS) fit their academic major or workload.
           - Specific benefits for their profile (e.g. 'Since you are in Computer Science, 16GB RAM allows you to run virtual machines and IDEs smoothly...').
           - Pros and Cons (e.g. price vs. rating, color, brand reputation).
           - How it fits their financial constraints.
        5. Formulate a final comparison table comparing the recommended models.
        6. Structure the report beautifully in Markdown with sections, clear bullet points, bold highlights, and clean typography.
        
        Do not make up any specifications, ratings, or prices that are not present in the database search results.
        """,
        expected_output="A beautiful, detailed markdown report listing the top 3 laptop recommendations, including academic/professional justifications, pros/cons, and a final summary comparison table.",
        agent=recommender
    )

    # Combine into a Crew
    crew = Crew(
        agents=[data_specialist, recommender],
        tasks=[search_task, recommendation_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew
