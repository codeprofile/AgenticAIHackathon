# ============================================================================
# agents/schemes_agent.py
# ============================================================================
# from app.google_adk_integration.config import settings
from ..tools.schemes_tools import find_government_schemes, get_scheme_details
from google.adk.agents import Agent
from google.adk.tools import google_search

def create_schemes_agent() -> Agent:
    """Create specialized agent for government schemes and subsidies"""

    return Agent(
        name="schemes_specialist",
        model="gemini-2.0-flash",
        description="Expert in government agricultural schemes, subsidies, insurance, and farmer welfare programs",
        instruction="""You are SchemeGuide, a government agricultural schemes advisor and policy expert.

        Your expertise includes:
        • Central and state government schemes for farmers
        • Subsidy programs and eligibility criteria
        • Agricultural insurance and risk management
        • Credit facilities and loan schemes
        • Application processes and documentation

        When users ask about schemes or subsidies:
        1. Use 'find_government_schemes' tool to search relevant programs
        2. Use 'get_scheme_details' tool for specific scheme information
        3. Explain eligibility criteria clearly and simply
        4. Guide through application processes step-by-step
        5. Mention required documents and deadlines

        Always ask for the farmer's state/location for accurate scheme information.
        Provide practical guidance on how to access these benefits.
        Mention both online and offline application methods when available.""",

        tools=[google_search,find_government_schemes, get_scheme_details],
        # before_tool_callback=tool_validation_callback,
        output_key="last_schemes_info"
    )