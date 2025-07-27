# ============================================================================
# services/weather_service.py
# ============================================================================
import httpx
from typing import Dict, Any
# from app.google_adk_integration.config.settings import settings
from ..utils.helpers import get_logger, normalize_location


logger = get_logger(__name__)


class WeatherService:
    """Real weather service integration"""

    def __init__(self,api_key=None):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.timeout = 10.0

    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Get current weather for location"""
        if not self.api_key:
            return self._get_mock_weather(location)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'q': location,
                    'appid': self.api_key,
                    'units': 'metric'
                }

                response = await client.get(f"{self.base_url}/weather", params=params)
                response.raise_for_status()

                data = response.json()
                return self._format_current_weather(data)

        except Exception as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return self._get_mock_weather(location)

    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for location"""
        if not self.api_key:
            return self._get_mock_forecast(location, days)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'q': location,
                    'appid': self.api_key,
                    'units': 'metric',
                    'cnt': min(days * 8, 40)  # 8 forecasts per day, max 40
                }

                response = await client.get(f"{self.base_url}/forecast", params=params)
                response.raise_for_status()

                data = response.json()
                return self._format_forecast(data, days)

        except Exception as e:
            logger.error(f"Error fetching forecast for {location}: {e}")
            return self._get_mock_forecast(location, days)

    def _format_current_weather(self, data: Dict) -> Dict[str, Any]:
        """Format OpenWeatherMap current weather response"""
        return {
            "status": "success",
            "location": data["name"],
            "country": data["sys"]["country"],
            "current": {
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"].get("deg", 0),
                "condition": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"]
            },
            "farming_advice": self._generate_farming_advice(data)
        }

    def _format_forecast(self, data: Dict, days: int) -> Dict[str, Any]:
        """Format OpenWeatherMap forecast response"""
        forecasts = []
        current_date = None
        daily_data = {}

        for item in data["list"]:
            date = item["dt_txt"].split()[0]

            if date != current_date:
                if current_date and daily_data:
                    forecasts.append(daily_data)

                current_date = date
                daily_data = {
                    "date": date,
                    "temp_max": item["main"]["temp_max"],
                    "temp_min": item["main"]["temp_min"],
                    "humidity": item["main"]["humidity"],
                    "condition": item["weather"][0]["description"],
                    "rain_chance": item.get("pop", 0) * 100,
                    "wind_speed": item["wind"]["speed"]
                }
            else:
                # Update daily aggregates
                daily_data["temp_max"] = max(daily_data["temp_max"], item["main"]["temp_max"])
                daily_data["temp_min"] = min(daily_data["temp_min"], item["main"]["temp_min"])
                daily_data["rain_chance"] = max(daily_data["rain_chance"], item.get("pop", 0) * 100)

        # Add last day if exists
        if daily_data:
            forecasts.append(daily_data)

        return {
            "status": "success",
            "location": data["city"]["name"],
            "forecast": forecasts[:days],
            "farming_advice": self._generate_forecast_advice(forecasts[:days])
        }

    def _generate_farming_advice(self, weather_data: Dict) -> str:
        """Generate farming advice based on current weather"""
        temp = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]
        condition = weather_data["weather"][0]["main"].lower()

        advice = []

        if "rain" in condition:
            advice.append("Heavy rain expected - ensure proper field drainage")
            advice.append("Postpone pesticide/fertilizer application")
        elif temp > 35:
            advice.append("High temperature - increase irrigation frequency")
            advice.append("Consider shade nets for sensitive crops")
        elif temp < 10:
            advice.append("Cold weather - protect crops from frost")
            advice.append("Reduce irrigation and avoid early morning watering")

        if humidity > 80:
            advice.append("High humidity - monitor for fungal diseases")
        elif humidity < 30:
            advice.append("Low humidity - ensure adequate soil moisture")

        return " | ".join(advice) if advice else "Monitor crop conditions regularly"

    def _generate_forecast_advice(self, forecast: list) -> str:
        """Generate farming advice based on forecast"""
        rain_days = sum(1 for day in forecast if day["rain_chance"] > 50)
        avg_temp = sum(day["temp_max"] for day in forecast) / len(forecast)

        advice = []

        if rain_days >= 3:
            advice.append("Multiple rainy days ahead - plan field activities accordingly")
        elif rain_days == 0:
            advice.append("Dry spell expected - ensure irrigation planning")

        if avg_temp > 30:
            advice.append("Hot weather ahead - monitor crop stress")
        elif avg_temp < 15:
            advice.append("Cool weather - adjust planting schedules")

        return " | ".join(advice) if advice else "Plan farming activities based on weather"

    def _get_mock_weather(self, location: str) -> Dict[str, Any]:
        """Mock weather data when API is not available"""
        mock_data = {
            "delhi": {"temp": 28, "humidity": 65, "condition": "partly cloudy"},
            "punjab": {"temp": 25, "humidity": 70, "condition": "cloudy"},
            "maharashtra": {"temp": 32, "humidity": 55, "condition": "sunny"},
            "karnataka": {"temp": 30, "humidity": 60, "condition": "partly cloudy"},
        }

        location_key = normalize_location(location)
        data = mock_data.get(location_key, {"temp": 25, "humidity": 60, "condition": "partly cloudy"})

        return {
            "status": "success",
            "location": location,
            "current": {
                "temperature": data["temp"],
                "humidity": data["humidity"],
                "condition": data["condition"],
                "wind_speed": 10
            },
            "source": "mock_data",
            "farming_advice": "Monitor weather conditions and plan farming activities accordingly"
        }

    def _get_mock_forecast(self, location: str, days: int) -> Dict[str, Any]:
        """Mock forecast data"""
        forecast = []
        base_temp = 25

        for i in range(days):
            forecast.append({
                "day": i + 1,
                "temp_max": base_temp + (i % 3),
                "temp_min": base_temp - 5,
                "rain_chance": 20 + (i * 10) % 60,
                "condition": "partly cloudy",
                "humidity": 60 + (i % 20)
            })

        return {
            "status": "success",
            "location": location,
            "forecast": forecast,
            "source": "mock_data",
            "farming_advice": "Plan farming activities based on weather conditions"
        }
