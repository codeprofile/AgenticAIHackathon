# ============================================================================
# tools/weather_tools.py
# ============================================================================
from ..services.weather_service import WeatherService
from  typing import Dict,Any
from google.adk.tools.tool_context import ToolContext
# logger = get_logger(__name__)
weather_service = WeatherService()


def get_weather_forecast(
        location: str,
        days: int = 7,
        include_farming_advice: bool = True,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get weather forecast with farming recommendations.

    Args:
        location (str): Location for weather forecast
        days (int): Number of days for forecast (1-10)
        include_farming_advice (bool): Include farming-specific advice
        tool_context (ToolContext): Session context

    Returns:
        Dict: Weather forecast with farming recommendations
    """
    # logger.info(f"Getting weather forecast for {location} for {days} days")

    try:
        # Validate inputs
        is_valid, error_msg = validate_location(location)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        if days < 1 or days > 10:
            return {"status": "error", "message": "Forecast days must be between 1 and 10"}

        # Get forecast from service
        forecast_data = weather_service.get_forecast(location, days)

        # Add farming-specific enhancements if requested
        if include_farming_advice and forecast_data.get("status") == "success":
            forecast_data["detailed_farming_advice"] = generate_detailed_farming_advice(
                forecast_data.get("forecast", []),
                tool_context
            )

        # Update session state
        if tool_context and forecast_data.get("status") == "success":
            tool_context.state["last_weather_location"] = location
            tool_context.state["last_weather_check"] = {
                "location": location,
                "days": days,
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

        return forecast_data

    except Exception as e:
        # logger.error(f"Error getting weather forecast: {e}")
        return {
            "status": "error",
            "message": "Unable to fetch weather forecast at the moment"
        }


def get_current_weather(
        location: str,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get current weather conditions.

    Args:
        location (str): Location for current weather
        tool_context (ToolContext): Session context

    Returns:
        Dict: Current weather information
    """
    # logger.info(f"Getting current weather for {location}")

    try:
        # Validate location
        is_valid, error_msg = validate_location(location)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        # Get current weather
        weather_data =  weather_service.get_current_weather(location)

        # Update session state
        if tool_context and weather_data.get("status") == "success":
            tool_context.state["last_weather_location"] = location
            tool_context.state["current_weather"] = {
                "location": location,
                "temperature": weather_data["current"]["temperature"],
                "condition": weather_data["current"]["condition"],
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

        return weather_data

    except Exception as e:
        # logger.error(f"Error getting current weather: {e}")
        return {
            "status": "error",
            "message": "Unable to fetch current weather information"
        }


def generate_detailed_farming_advice(forecast_data: list, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Generate detailed farming advice based on weather forecast"""
    if not forecast_data:
        return {"advice": "No forecast data available for detailed analysis"}

    # Analyze forecast patterns
    rain_days = sum(1 for day in forecast_data if day.get("rain_chance", 0) > 50)
    hot_days = sum(1 for day in forecast_data if day.get("temp_max", 0) > 35)
    cold_days = sum(1 for day in forecast_data if day.get("temp_min", 50) < 10)

    advice = {
        "irrigation_schedule": [],
        "pest_disease_alerts": [],
        "crop_operations": [],
        "harvesting_recommendations": []
    }

    # Irrigation advice
    if rain_days >= 3:
        advice["irrigation_schedule"].append("Reduce irrigation frequency due to expected rainfall")
        advice["irrigation_schedule"].append("Ensure proper drainage to prevent waterlogging")
    elif rain_days == 0:
        advice["irrigation_schedule"].append("Increase irrigation frequency - dry period ahead")
        advice["irrigation_schedule"].append("Consider mulching to retain soil moisture")

    # Temperature-based advice
    if hot_days >= 2:
        advice["crop_operations"].append("Plan field operations for early morning or evening")
        advice["crop_operations"].append("Consider shade nets for sensitive crops")

    if cold_days >= 1:
        advice["crop_operations"].append("Protect crops from cold stress")
        advice["crop_operations"].append("Delay early morning irrigation")

    # Pest and disease alerts
    if rain_days >= 2:
        advice["pest_disease_alerts"].append("High humidity expected - monitor for fungal diseases")
        advice["pest_disease_alerts"].append("Avoid pesticide application during rainy periods")

    # Get user's crops for specific advice
    user_crops = []
    if tool_context:
        user_crops = tool_context.state.get("user_crops", [])

    if user_crops:
        advice["crop_specific"] = {}
        for crop in user_crops[:3]:  # Limit to 3 crops
            advice["crop_specific"][crop] = get_crop_specific_weather_advice(crop, forecast_data)

    return advice


def get_crop_specific_weather_advice(crop: str, forecast_data: list) -> list:
    """Get crop-specific weather advice"""
    crop_advice = {
        "wheat": [
            "Monitor for rust diseases during humid conditions",
            "Avoid harvesting during rainy days",
            "Ensure grain moisture is below 14% for storage"
        ],
        "rice": [
            "Maintain proper water levels in fields",
            "Watch for blast disease during cool, humid weather",
            "Plan transplanting during favorable weather windows"
        ],
        "tomato": [
            "Protect from excessive rain to prevent fruit cracking",
            "Monitor for late blight during cool, wet conditions",
            "Ensure proper ventilation in polyhouse cultivation"
        ]
    }

    return crop_advice.get(crop.lower(), ["Monitor crop conditions regularly based on weather"])