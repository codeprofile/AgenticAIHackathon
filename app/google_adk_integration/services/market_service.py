# ============================================================================
# app/google_adk_integration/services/market_service.py
# ============================================================================
from typing import Dict, Any, List, Optional
import random
from datetime import datetime, timedelta
from ..utils.helpers import get_logger, load_json_data, normalize_crop_name

logger = get_logger(__name__)


class MarketService:
    """Market data and analysis service"""

    def __init__(self):
        self.price_database = self._load_price_database()
        self.market_locations = self._get_market_locations()

    def get_current_prices(self, crop_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Get current market prices for a crop"""
        try:
            crop_normalized = normalize_crop_name(crop_name)

            if crop_normalized not in self.price_database:
                return {
                    "status": "crop_not_found",
                    "message": f"{crop_name} के लिए मार्केट डेटा उपलब्ध नहीं है",
                    "available_crops": list(self.price_database.keys())
                }

            crop_data = self.price_database[crop_normalized]

            # If location specified, try to find specific market
            if location:
                location_normalized = location.lower().strip()
                location_prices = []

                for market_info in crop_data["markets"]:
                    if location_normalized in market_info["location"].lower():
                        location_prices.append(market_info)

                if location_prices:
                    markets = location_prices
                else:
                    markets = crop_data["markets"][:3]  # Show nearby markets
            else:
                markets = crop_data["markets"][:5]  # Show top 5 markets

            # Calculate average and trends
            prices = [m["current_price"] for m in markets]
            avg_price = sum(prices) / len(prices)

            # Mock trend calculation
            trend_direction = "up" if avg_price > crop_data.get("base_price", avg_price) else "down"

            return {
                "status": "success",
                "crop": crop_name,
                "location_queried": location,
                "average_price": round(avg_price, 2),
                "price_unit": crop_data["unit"],
                "trend": trend_direction,
                "markets": markets,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "recommendation": self._get_price_recommendation(avg_price, trend_direction, crop_data)
            }

        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            return {
                "status": "error",
                "message": "मार्केट प्राइस प्राप्त करने में समस्या हुई"
            }

    def get_price_analysis(self, crop_name: str, days: int = 30) -> Dict[str, Any]:
        """Get price trend analysis and predictions"""
        try:
            crop_normalized = normalize_crop_name(crop_name)

            if crop_normalized not in self.price_database:
                return {
                    "status": "crop_not_found",
                    "message": f"{crop_name} के लिए डेटा उपलब्ध नहीं है"
                }

            crop_data = self.price_database[crop_normalized]
            current_price = crop_data["markets"][0]["current_price"]

            # Generate mock historical data
            historical_prices = self._generate_historical_prices(current_price, days)

            # Calculate trends
            recent_trend = self._calculate_trend(historical_prices[-7:])  # Last week trend
            monthly_trend = self._calculate_trend(historical_prices)  # Monthly trend

            # Generate predictions
            predictions = self._generate_price_predictions(current_price, recent_trend)

            return {
                "status": "success",
                "crop": crop_name,
                "analysis_period": f"{days} दिन",
                "current_price": current_price,
                "historical_data": {
                    "highest_price": max(historical_prices),
                    "lowest_price": min(historical_prices),
                    "average_price": round(sum(historical_prices) / len(historical_prices), 2)
                },
                "trends": {
                    "weekly_trend": recent_trend,
                    "monthly_trend": monthly_trend,
                    "trend_strength": abs(recent_trend)
                },
                "predictions": predictions,
                "market_sentiment": self._get_market_sentiment(recent_trend, monthly_trend),
                "recommendation": self._get_analysis_recommendation(recent_trend, predictions)
            }

        except Exception as e:
            logger.error(f"Error in price analysis: {e}")
            return {
                "status": "error",
                "message": "प्राइस एनालिसिस में समस्या हुई"
            }

    def get_selling_advice(self, crop_name: str, quantity: Optional[float], quality: str, location: Optional[str]) -> \
    Dict[str, Any]:
        """Get advice on selling strategy"""
        try:
            crop_normalized = normalize_crop_name(crop_name)

            if crop_normalized not in self.price_database:
                return {
                    "status": "crop_not_found",
                    "message": f"{crop_name} के लिए डेटा उपलब्ध नहीं है"
                }

            crop_data = self.price_database[crop_normalized]
            current_price = crop_data["markets"][0]["current_price"]

            # Quality adjustment
            quality_multiplier = {"high": 1.1, "medium": 1.0, "low": 0.9}
            adjusted_price = current_price * quality_multiplier.get(quality, 1.0)

            # Get best markets
            best_markets = sorted(crop_data["markets"], key=lambda x: x["current_price"], reverse=True)[:3]

            # Generate selling strategy
            strategy = self._generate_selling_strategy(crop_name, adjusted_price, quantity, quality)

            return {
                "status": "success",
                "crop": crop_name,
                "quantity": quantity,
                "quality": quality,
                "expected_price": round(adjusted_price, 2),
                "best_markets": best_markets,
                "selling_strategy": strategy,
                "timing_advice": self._get_timing_advice(crop_name),
                "storage_advice": self._get_storage_advice(crop_name, quality),
                "negotiation_tips": self._get_negotiation_tips(quality)
            }

        except Exception as e:
            logger.error(f"Error getting selling advice: {e}")
            return {
                "status": "error",
                "message": "बिक्री सलाह प्राप्त करने में समस्या हुई"
            }

    def _load_price_database(self) -> Dict[str, Any]:
        """Load price database"""
        return load_json_data("google_adk_integration/data/market_prices.json")

    def _get_market_locations(self) -> List[str]:
        """Get list of market locations"""
        return [
            "दिल्ली मंडी", "मुंबई मंडी", "कोलकाता मंडी", "चेन्नई मंडी",
            "बेंगलुरु मंडी", "पुणे मंडी", "जयपुर मंडी", "इंदौर मंडी",
            "नागपुर मंडी", "लुधियाना मंडी"
        ]

    def _generate_historical_prices(self, current_price: float, days: int) -> List[float]:
        """Generate mock historical price data"""
        prices = []
        base_price = current_price

        for i in range(days):
            # Add some randomness to simulate price fluctuation
            change_percent = random.uniform(-0.05, 0.05)  # ±5% daily change
            base_price *= (1 + change_percent)
            prices.append(round(base_price, 2))

        return prices

    def _calculate_trend(self, prices: List[float]) -> float:
        """Calculate price trend percentage"""
        if len(prices) < 2:
            return 0.0

        start_price = prices[0]
        end_price = prices[-1]
        trend = ((end_price - start_price) / start_price) * 100
        return round(trend, 2)

    def _generate_price_predictions(self, current_price: float, trend: float) -> Dict[str, Any]:
        """Generate price predictions"""
        # Simple trend extrapolation with some randomness
        next_week = current_price * (1 + (trend / 100) * 0.5 + random.uniform(-0.02, 0.02))
        next_month = current_price * (1 + (trend / 100) * 2 + random.uniform(-0.05, 0.05))

        return {
            "next_week": round(next_week, 2),
            "next_month": round(next_month, 2),
            "confidence": "medium",
            "factors": [
                "मौसम की स्थिति",
                "बाजार की मांग",
                "सरकारी नीतियां"
            ]
        }

    def _get_market_sentiment(self, weekly_trend: float, monthly_trend: float) -> str:
        """Determine market sentiment"""
        if weekly_trend > 2 and monthly_trend > 5:
            return "बहुत तेजी"
        elif weekly_trend > 0 and monthly_trend > 0:
            return "तेजी"
        elif weekly_trend < -2 and monthly_trend < -5:
            return "बहुत मंदी"
        elif weekly_trend < 0 and monthly_trend < 0:
            return "मंदी"
        else:
            return "स्थिर"

    def _get_price_recommendation(self, avg_price: float, trend: str, crop_data: Dict) -> str:
        """Get price-based recommendation"""
        if trend == "up":
            return f"कीमतें बढ़ रही हैं - बेचने का अच्छा समय है। औसत भाव ₹{avg_price}/{crop_data['unit']}"
        else:
            return f"कीमतें घट रही हैं - अगर संभव हो तो थोड़ा इंतजार करें या स्टोरेज का विकल्प देखें"

    def _get_analysis_recommendation(self, trend: float, predictions: Dict) -> str:
        """Get analysis-based recommendation"""
        if trend > 3:
            return "मजबूत तेजी - तुरंत बेचने का अच्छा समय"
        elif trend > 0:
            return "हल्की तेजी - बेच सकते हैं या थोड़ा इंतजार कर सकते हैं"
        elif trend < -3:
            return "तेज गिरावट - अगर तत्काल जरूरत नहीं तो स्टोरेज करें"
        else:
            return "मिश्रित संकेत - स्थानीय मार्केट देखकर फैसला लें"

    def _generate_selling_strategy(self, crop: str, price: float, quantity: Optional[float], quality: str) -> Dict[
        str, str]:
        """Generate selling strategy"""
        return {
            "immediate": "50% फसल तुरंत बेचें - तत्काल नकदी के लिए",
            "short_term": "30% फसल 2-3 सप्ताह में बेचें - बेहतर दाम के लिए",
            "long_term": "20% फसल स्टोरेज करें - त्योहारी सीजन के लिए",
            "risk_management": "सभी मंडियों में एक साथ न बेचें - रिस्क फैलाएं"
        }

    def _get_timing_advice(self, crop: str) -> str:
        """Get timing advice for selling"""
        timing_map = {
            "wheat": "अप्रैल-मई में बेचें, जब मांग ज्यादा होती है",
            "rice": "नवंबर-दिसंबर में बेचें, त्योहारी सीजन में मांग बढ़ती है",
            "tomato": "सुबह जल्दी बेचें जब फ्रेशनेस अच्छी हो"
        }
        return timing_map.get(crop.lower(), "स्थानीय मार्केट ट्रेंड के अनुसार बेचें")

    def _get_storage_advice(self, crop: str, quality: str) -> str:
        """Get storage advice"""
        if quality == "high":
            return "अच्छी क्वालिटी है - 2-3 महीने स्टोरेज करके बेहतर दाम पा सकते हैं"
        elif quality == "medium":
            return "मध्यम क्वालिटी - 1 महीने तक स्टोर कर सकते हैं"
        else:
            return "क्वालिटी साधारण है - जल्दी बेच देना बेहतर होगा"

    def _get_negotiation_tips(self, quality: str) -> List[str]:
        """Get negotiation tips"""
        base_tips = [
            "कई व्यापारियों से भाव पूछें",
            "तोल में कमी न होने दें",
            "पेमेंट का तत्काल इंतजाम सुनिश्चित करें"
        ]

        if quality == "high":
            base_tips.append("अच्छी क्वालिटी का फायदा उठाकर प्रीमियम मांगें")

        return base_tips