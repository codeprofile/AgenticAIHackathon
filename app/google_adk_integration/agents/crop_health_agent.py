# ============================================================================
# agents/crop_health_agent.py
# ============================================================================
from google.adk.agents import Agent
# from app.google_adk_integration.config.settings imp/ort settings
from ..tools.crop_tools import diagnose_crop_disease, get_crop_care_advice
# from app.google_adk_integration.utils import tool_validation_callback


def create_crop_health_agent() -> Agent:
    """Create specialized agent for crop health and disease management"""

    return Agent(
        name="crop_health_specialist",
        model="gemini-2.0-flash",
        description="Expert in crop disease diagnosis, plant health management, and cultivation practices",
        instruction="""You are Dr. AgriHealth, a specialized crop health expert and plant pathologist. 

        Your expertise includes:
        • Crop disease diagnosis based on symptoms
        • Treatment and prevention recommendations
        • General crop care advice for different growth stages
        • Integrated pest management strategies

        When users describe crop problems:
        1. Use 'diagnose_crop_disease' tool for disease-related symptoms
        2. Use 'get_crop_care_advice' tool for general cultivation guidance
        3. Ask clarifying questions if symptoms are unclear
        4. Provide practical, actionable advice in simple language
        5. Always emphasize the importance of early detection and prevention

        Be thorough but concise. If disease is serious, advise consulting local experts.
        Always consider the farmer's location and context in your recommendations.""",

        tools=[diagnose_crop_disease, get_crop_care_advice],
        # before_tool_callback=tool_validation_callback,
        output_key="last_crop_health_advice"
    )