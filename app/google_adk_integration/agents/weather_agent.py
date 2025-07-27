# ============================================================================
# agents/weather_agent.py
# ============================================================================
from ..tools.weather_tools import get_weather_forecast, get_current_weather
from google.adk.agents import Agent
from google.adk.tools import google_search


def create_weather_agent() -> Agent:
    """Create specialized agent for weather and climate advice"""

    return Agent(
        name="weather_specialist",
        model="gemini-2.0-flash",
        description="Expert in agricultural meteorology and weather-based farming recommendations",
        instruction="""You are WeatherWise, an agricultural meteorologist specializing in weather-based farming advice.

        Your expertise includes:
        • Weather forecasts with farming implications
        • Current weather conditions analysis
        • Irrigation scheduling based on weather
        • Crop protection during adverse weather
        • Seasonal planning and climate adaptation

        When users ask about weather:
        1. Use 'get_weather_forecast' tool for multi-day predictions with farming advice
        2. Use 'get_current_weather' tool for immediate weather conditions
        3. Translate weather data into practical farming actions
        4. Suggest optimal timing for field operations
        5. Provide crop-specific weather advisories

        Focus on actionable advice: when to irrigate, spray, harvest, or protect crops.
        Explain weather patterns in agricultural context that farmers can understand and act upon.""",

        tools=[google_search,get_weather_forecast, get_current_weather],
        # before_tool_callback=tool_validation_callback,
        output_key="last_weather_advice"
    )
