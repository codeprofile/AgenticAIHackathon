# ============================================================================
# app/tools/market_tools.py - Complete Market Tools with Database Integration
# ============================================================================
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session
from google.adk.tools import ToolContext

# Import database components
from ..database.database import get_db_session
from ..database.models import MarketPrice, MarketAnalytics, DataSyncLog
from ..utils.helpers import get_logger
from ..utils.validators import validate_crop_name
from ..services.market_service import MarketService

logger = get_logger(__name__)
market_service = MarketService()


def get_market_prices(
        crop_name: str,
        location: Optional[str] = None,
        tool_context=None
) -> Dict[str, Any]:
    """
    Get current market prices for a specific crop from database

    Args:
        crop_name (str): Name of the crop
        location (str, optional): Location/market to check
        tool_context: Session context (optional)

    Returns:
        Dict: Current market prices and trends
    """
    logger.info(f"Getting market prices for {crop_name} in {location}")

    try:
        # Validate inputs
        is_valid, error_msg = validate_crop_name(crop_name)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        with get_db_session() as db:
            # Get latest prices for the crop
            query = db.query(MarketPrice).filter(
                MarketPrice.commodity.ilike(f"%{crop_name}%")
            ).filter(
                MarketPrice.arrival_date >= datetime.now() - timedelta(days=2)
            )

            # Filter by location if provided
            if location:
                query = query.filter(
                    or_(
                        MarketPrice.state.ilike(f"%{location}%"),
                        MarketPrice.district.ilike(f"%{location}%"),
                        MarketPrice.market.ilike(f"%{location}%")
                    )
                )

            # Get results ordered by date and price
            prices = query.order_by(
                desc(MarketPrice.arrival_date),
                desc(MarketPrice.modal_price)
            ).limit(10).all()

            if not prices:
                return {
                    "status": "no_data",
                    "message": f"{crop_name} के लिए हाल की कीमत उपलब्ध नहीं है"
                }

            # Calculate analytics
            avg_price = sum(p.modal_price for p in prices) / len(prices)
            highest_price = max(p.modal_price for p in prices)
            lowest_price = min(p.modal_price for p in prices)

            # Determine overall trend
            up_trends = len([p for p in prices if p.trend == 'up'])
            down_trends = len([p for p in prices if p.trend == 'down'])

            if up_trends > down_trends:
                overall_trend = 'up'
            elif down_trends > up_trends:
                overall_trend = 'down'
            else:
                overall_trend = 'stable'

            # Format markets data
            markets = []
            for price in prices:
                markets.append({
                    "market_name": f"{price.market}, {price.district}, {price.state}",
                    "modal_price": price.modal_price,
                    "min_price": price.min_price,
                    "max_price": price.max_price,
                    "variety": price.variety or "स्टैंडर्ड",
                    "grade": price.grade or "FAQ",
                    "arrival_date": price.arrival_date.strftime("%d-%m-%Y"),
                    "price_change": price.price_change,
                    "percentage_change": price.percentage_change,
                    "trend": price.trend
                })

            # Update session with user's crop interests if tool_context available
            if tool_context and hasattr(tool_context, 'state'):
                tool_context.state["last_price_query"] = {
                    "crop": crop_name,
                    "location": location,
                    "timestamp": datetime.now().isoformat()
                }

                # Track user's market interests
                market_interests = tool_context.state.get("market_interests", [])
                if crop_name not in market_interests:
                    market_interests.append(crop_name)
                    tool_context.state["market_interests"] = market_interests[:5]

            return {
                "status": "success",
                "crop": crop_name,
                "location": location,
                "average_price": round(avg_price, 2),
                "highest_price": highest_price,
                "lowest_price": lowest_price,
                "price_range": round(highest_price - lowest_price, 2),
                "overall_trend": overall_trend,
                "markets": markets,
                "total_markets": len(markets),
                "last_updated": prices[0].arrival_date.strftime("%d-%m-%Y %H:%M") if prices else None,
                "recommendation": get_price_recommendation(avg_price, overall_trend, crop_name)
            }

    except Exception as e:
        logger.error(f"Error getting market prices: {e}")
        return {
            "status": "error",
            "message": "मार्केट की जानकारी लेने में समस्या हुई"
        }


def get_price_analysis(
        crop_name: str,
        days: int = 30,
        tool_context=None
) -> Dict[str, Any]:
    """Get price trend analysis and predictions from database"""
    logger.info(f"Getting price analysis for {crop_name} over {days} days")

    try:
        is_valid, error_msg = validate_crop_name(crop_name)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        with get_db_session() as db:
            # Get historical data
            historical_data = db.query(MarketPrice).filter(
                and_(
                    MarketPrice.commodity.ilike(f"%{crop_name}%"),
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=days)
                )
            ).order_by(MarketPrice.arrival_date.desc()).all()

            if len(historical_data) < 3:
                return {
                    "status": "insufficient_data",
                    "message": f"{crop_name} के लिए पर्याप्त हिस्टोरिकल डेटा नहीं है"
                }

            # Get analytics from database
            analytics = db.query(MarketAnalytics).filter(
                MarketAnalytics.commodity.ilike(f"%{crop_name}%")
            ).order_by(desc(MarketAnalytics.analysis_date)).first()

            # Calculate analysis metrics
            prices = [record.modal_price for record in historical_data]
            current_price = prices[0] if prices else 0

            analysis_result = {
                "status": "success",
                "crop": crop_name,
                "analysis_period": f"{days} दिन",
                "current_price": current_price,
                "historical_data": {
                    "highest_price": max(prices),
                    "lowest_price": min(prices),
                    "average_price": round(sum(prices) / len(prices), 2),
                    "total_records": len(historical_data)
                },
                "trends": {
                    "weekly_trend": analytics.weekly_trend if analytics else calculate_recent_trend(
                        historical_data[:7]),
                    "monthly_trend": analytics.monthly_trend if analytics else calculate_recent_trend(historical_data),
                    "price_volatility": analytics.price_volatility if analytics else calculate_volatility(prices)
                },
                "market_activity": {
                    "active_markets": analytics.active_markets if analytics else len(
                        set(f"{r.market}-{r.district}" for r in historical_data)),
                    "top_market": analytics.top_market if analytics else get_top_market(historical_data),
                    "market_distribution": json.loads(
                        analytics.market_distribution) if analytics and analytics.market_distribution else {}
                },
                "recommendations": json.loads(
                    analytics.recommendations) if analytics and analytics.recommendations else generate_basic_recommendations(
                    historical_data)
            }

            # Add predictions if available
            if analytics:
                analysis_result["predictions"] = {
                    "next_week": analytics.predicted_price_7d,
                    "next_month": analytics.predicted_price_14d,
                    "confidence": analytics.prediction_confidence,
                    "factors": ["मौसम की स्थिति", "बाजार की मांग", "मंडी में आपूर्ति"]
                }

            return analysis_result

    except Exception as e:
        logger.error(f"Error in price analysis: {e}")
        return {
            "status": "error",
            "message": "प्राइस एनालिसिस में समस्या हुई"
        }


def get_selling_advice(
        crop_name: str,
        quantity: Optional[float] = None,
        quality: str = "medium",
        location: Optional[str] = None,
        tool_context=None
) -> Dict[str, Any]:
    """Get advice on when and where to sell crop"""
    logger.info(f"Getting selling advice for {crop_name}")

    try:
        is_valid, error_msg = validate_crop_name(crop_name)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        with get_db_session() as db:
            # Get recent market data
            recent_data = db.query(MarketPrice).filter(
                and_(
                    MarketPrice.commodity.ilike(f"%{crop_name}%"),
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=3)
                )
            ).order_by(desc(MarketPrice.modal_price)).all()

            if not recent_data:
                return {
                    "status": "no_data",
                    "message": f"{crop_name} के लिए हाल का डेटा नहीं मिला"
                }

            # Get analytics for predictions
            analytics = db.query(MarketAnalytics).filter(
                MarketAnalytics.commodity.ilike(f"%{crop_name}%")
            ).order_by(desc(MarketAnalytics.analysis_date)).first()

            # Quality adjustment
            quality_multipliers = {"premium": 1.15, "high": 1.1, "medium": 1.0, "low": 0.9, "poor": 0.8}
            quality_factor = quality_multipliers.get(quality, 1.0)

            # Get best markets
            best_markets = []
            for market in recent_data[:5]:
                adjusted_price = market.modal_price * quality_factor
                best_markets.append({
                    "market_name": f"{market.market}, {market.district}",
                    "base_price": market.modal_price,
                    "adjusted_price": round(adjusted_price, 2),
                    "trend": market.trend,
                    "distance_estimate": estimate_distance(location,
                                                           f"{market.district}, {market.state}") if location else "N/A"
                })

            # Generate selling strategy based on trends and predictions
            strategy = generate_selling_strategy(recent_data, analytics, quality, quantity)

            # Timing advice based on trends and predictions
            timing_advice = generate_timing_advice(recent_data, analytics)

            return {
                "status": "success",
                "crop": crop_name,
                "quantity": quantity,
                "quality": quality,
                "current_market_condition": analytics.weekly_trend if analytics else calculate_recent_trend(
                    recent_data),
                "best_markets": best_markets,
                "selling_strategy": strategy,
                "timing_advice": timing_advice,
                "storage_advice": get_storage_advice(crop_name, quality),
                "negotiation_tips": get_negotiation_tips(quality, recent_data),
                "expected_revenue": calculate_expected_revenue(recent_data[0], quantity,
                                                               quality_factor) if quantity and recent_data else None
            }

    except Exception as e:
        logger.error(f"Error getting selling advice: {e}")
        return {
            "status": "error",
            "message": "बिक्री सलाह प्राप्त करने में समस्या हुई"
        }


def get_location_based_markets(
        user_latitude: float,
        user_longitude: float,
        crop_name: str = None,
        radius_km: int = 100
) -> Dict[str, Any]:
    """Get markets based on user location with live prices"""
    logger.info(f"Getting location-based markets for lat: {user_latitude}, lng: {user_longitude}")

    try:
        with get_db_session() as db:
            query = db.query(MarketPrice).filter(
                MarketPrice.arrival_date >= datetime.now() - timedelta(days=2)
            )

            if crop_name:
                query = query.filter(MarketPrice.commodity.ilike(f"%{crop_name}%"))

            # Get all recent market data
            markets = query.order_by(desc(MarketPrice.modal_price)).all()

            # Add distance calculation (simplified - in real implementation use geopy)
            location_markets = []
            for market in markets[:20]:  # Limit to top 20 for performance
                # Simplified distance calculation
                estimated_distance = estimate_distance_simple(
                    user_latitude, user_longitude,
                    market.state, market.district
                )

                if estimated_distance <= radius_km:
                    location_markets.append({
                        "market_name": f"{market.market}, {market.district}",
                        "state": market.state,
                        "district": market.district,
                        "commodity": market.commodity,
                        "modal_price": market.modal_price,
                        "trend": market.trend,
                        "estimated_distance": estimated_distance,
                        "arrival_date": market.arrival_date.strftime("%d-%m-%Y")
                    })

            # Sort by distance
            location_markets.sort(key=lambda x: x["estimated_distance"])

            return {
                "status": "success",
                "user_location": {"latitude": user_latitude, "longitude": user_longitude},
                "radius_km": radius_km,
                "total_markets_found": len(location_markets),
                "markets": location_markets[:10],  # Return top 10
                "crop_filter": crop_name
            }

    except Exception as e:
        logger.error(f"Error getting location-based markets: {e}")
        return {
            "status": "error",
            "message": "स्थान आधारित मंडी खोजने में समस्या हुई"
        }


def get_market_carousel_data(limit: int = 8) -> List[Dict[str, Any]]:
    """Get market data for home page carousel"""
    logger.info(f"Getting carousel data for {limit} crops")

    try:
        with get_db_session() as db:
            # Get diverse crop data from different states
            carousel_data = []

            # Get popular crops with recent data
            popular_crops = ['wheat', 'rice', 'tomato', 'onion', 'potato', 'sugarcane', 'cotton', 'soybean']

            for crop in popular_crops[:limit]:
                latest_price = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity.ilike(f"%{crop}%"),
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=2)
                    )
                ).order_by(desc(MarketPrice.modal_price)).first()

                if latest_price:
                    carousel_data.append({
                        "crop_name": translate_crop_name(crop),
                        "current_price": latest_price.modal_price,
                        "price_change": latest_price.price_change or 0,
                        "percentage_change": latest_price.percentage_change or 0,
                        "trend": latest_price.trend,
                        "market_location": f"{latest_price.market}, {latest_price.district}",
                        "last_updated": latest_price.arrival_date.strftime("%d-%m-%Y")
                    })

            # If we don't have enough data, fill with any available data
            if len(carousel_data) < limit:
                additional_data = db.query(MarketPrice).filter(
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=2)
                ).order_by(desc(MarketPrice.arrival_date)).limit(limit - len(carousel_data)).all()

                for price in additional_data:
                    if not any(item['crop_name'] == translate_crop_name(price.commodity) for item in carousel_data):
                        carousel_data.append({
                            "crop_name": translate_crop_name(price.commodity),
                            "current_price": price.modal_price,
                            "price_change": price.price_change or 0,
                            "percentage_change": price.percentage_change or 0,
                            "trend": price.trend,
                            "market_location": f"{price.market}, {price.district}",
                            "last_updated": price.arrival_date.strftime("%d-%m-%Y")
                        })

            logger.info(f"Returning {len(carousel_data)} carousel items")
            return carousel_data

    except Exception as e:
        logger.error(f"Error getting carousel data: {e}")
        return []


def get_comprehensive_market_analysis() -> Dict[str, Any]:
    """Get comprehensive market analysis for market.html page"""
    logger.info("Getting comprehensive market analysis")

    try:
        with get_db_session() as db:
            # Get all recent analytics
            all_analytics = db.query(MarketAnalytics).filter(
                MarketAnalytics.analysis_date >= datetime.now() - timedelta(days=1)
            ).all()

            if not all_analytics:
                # Fallback: generate basic analysis from recent price data
                return generate_fallback_analysis(db)

            # Calculate overall market insights
            total_crops = len(all_analytics)
            rising_crops = len([a for a in all_analytics if a.weekly_trend == 'up'])
            falling_crops = len([a for a in all_analytics if a.weekly_trend == 'down'])

            # Calculate average price changes
            avg_changes = []
            for analytics in all_analytics:
                if analytics.price_history:
                    try:
                        price_history = json.loads(analytics.price_history)
                        if len(price_history) >= 2:
                            recent_change = ((price_history[-1]['price'] - price_history[-2]['price']) /
                                             price_history[-2]['price']) * 100
                            avg_changes.append(recent_change)
                    except (json.JSONDecodeError, KeyError, ZeroDivisionError):
                        continue

            avg_change = sum(avg_changes) / len(avg_changes) if avg_changes else 0

            # Get top gainers and losers
            sorted_analytics = sorted(all_analytics, key=lambda x: (x.predicted_price_7d or 0) - (x.avg_price or 0),
                                      reverse=True)
            top_gainer = sorted_analytics[0] if sorted_analytics else None
            top_loser = sorted_analytics[-1] if sorted_analytics else None

            # Prepare market data for display
            market_data = []
            for analytics in all_analytics:
                # Get latest price data
                latest_price = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity.ilike(f"%{analytics.commodity}%"),
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=2)
                    )
                ).order_by(desc(MarketPrice.arrival_date)).first()

                if latest_price:
                    market_data.append({
                        "crop_name": translate_crop_name(analytics.commodity),
                        "current_price": latest_price.modal_price,
                        "price_change": latest_price.price_change or 0,
                        "percentage_change": latest_price.percentage_change or 0,
                        "market_location": f"{latest_price.market}, {latest_price.district}",
                        "trend": latest_price.trend,
                        "volatility": analytics.price_volatility or 0,
                        "prediction_7d": analytics.predicted_price_7d,
                        "confidence": analytics.prediction_confidence,
                        "active_markets": analytics.active_markets or 0
                    })

            return {
                "status": "success",
                "insights": {
                    "total_crops": total_crops,
                    "rising_crops": rising_crops,
                    "falling_crops": falling_crops,
                    "avg_change": round(avg_change, 2),
                    "market_sentiment": "Bullish" if avg_change > 0 else "Bearish",
                    "top_gainer": {
                        "crop_name": translate_crop_name(top_gainer.commodity),
                        "percentage_change": round(
                            ((top_gainer.predicted_price_7d or top_gainer.avg_price) - (top_gainer.avg_price or 0)) / (
                                        top_gainer.avg_price or 1) * 100, 2)
                    } if top_gainer else None,
                    "top_loser": {
                        "crop_name": translate_crop_name(top_loser.commodity),
                        "percentage_change": round(
                            ((top_loser.predicted_price_7d or top_loser.avg_price) - (top_loser.avg_price or 0)) / (
                                        top_loser.avg_price or 1) * 100, 2)
                    } if top_loser else None
                },
                "market_data": market_data,
                "last_analysis": max(a.analysis_date for a in all_analytics).strftime("%d-%m-%Y %H:%M")
            }

    except Exception as e:
        logger.error(f"Error getting comprehensive market analysis: {e}")
        return {
            "status": "error",
            "message": "व्यापक मार्केट विश्लेषण में समस्या हुई"
        }


def generate_fallback_analysis(db: Session) -> Dict[str, Any]:
    """Generate basic analysis when no analytics data is available"""
    try:
        # Get recent price data
        recent_prices = db.query(MarketPrice).filter(
            MarketPrice.arrival_date >= datetime.now() - timedelta(days=2)
        ).all()

        if not recent_prices:
            return {
                "status": "no_data",
                "message": "कोई हाल का मार्केट डेटा उपलब्ध नहीं है"
            }

        # Group by commodity
        commodity_data = {}
        for price in recent_prices:
            commodity = price.commodity.lower()
            if commodity not in commodity_data:
                commodity_data[commodity] = []
            commodity_data[commodity].append(price)

        # Calculate basic insights
        total_crops = len(commodity_data)
        rising_crops = 0
        falling_crops = 0
        market_data = []

        for commodity, prices in commodity_data.items():
            if not prices:
                continue

            latest_price = max(prices, key=lambda x: x.arrival_date)
            avg_price = sum(p.modal_price for p in prices) / len(prices)

            # Determine trend
            up_trends = len([p for p in prices if p.trend == 'up'])
            down_trends = len([p for p in prices if p.trend == 'down'])

            if up_trends > down_trends:
                trend = 'up'
                rising_crops += 1
            elif down_trends > up_trends:
                trend = 'down'
                falling_crops += 1
            else:
                trend = 'stable'

            market_data.append({
                "crop_name": translate_crop_name(commodity),
                "current_price": latest_price.modal_price,
                "price_change": latest_price.price_change or 0,
                "percentage_change": latest_price.percentage_change or 0,
                "market_location": f"{latest_price.market}, {latest_price.district}",
                "trend": trend,
                "volatility": 0,
                "prediction_7d": None,
                "confidence": None,
                "active_markets": len(prices)
            })

        # Calculate average change
        all_changes = [item["percentage_change"] for item in market_data if item["percentage_change"]]
        avg_change = sum(all_changes) / len(all_changes) if all_changes else 0

        return {
            "status": "success",
            "insights": {
                "total_crops": total_crops,
                "rising_crops": rising_crops,
                "falling_crops": falling_crops,
                "avg_change": round(avg_change, 2),
                "market_sentiment": "Bullish" if avg_change > 0 else "Bearish",
                "top_gainer": None,
                "top_loser": None
            },
            "market_data": market_data,
            "last_analysis": datetime.now().strftime("%d-%m-%Y %H:%M")
        }

    except Exception as e:
        logger.error(f"Error generating fallback analysis: {e}")
        return {
            "status": "error",
            "message": "बेसिक मार्केट विश्लेषण में भी समस्या हुई"
        }


# ============================================================================
# Helper Functions
# ============================================================================

def get_price_recommendation(avg_price: float, trend: str, crop_name: str) -> str:
    """Generate price recommendation"""
    if trend == "up":
        return f"{crop_name} की कीमतें बढ़ रही हैं - बेचने का अच्छा समय है। औसत भाव ₹{avg_price}"
    elif trend == "down":
        return f"{crop_name} की कीमतें घट रही हैं - अगर संभव हो तो थोड़ा इंतजार करें"
    else:
        return f"{crop_name} की कीमतें स्थिर हैं - नियमित बिक्री कर सकते हैं"


def calculate_recent_trend(data: List) -> str:
    """Calculate recent trend from price data"""
    if not data or len(data) < 2:
        return 'stable'

    # Calculate average trend
    up_count = len([d for d in data if hasattr(d, 'trend') and d.trend == 'up'])
    down_count = len([d for d in data if hasattr(d, 'trend') and d.trend == 'down'])

    if up_count > down_count:
        return 'up'
    elif down_count > up_count:
        return 'down'
    else:
        return 'stable'


def calculate_volatility(prices: List[float]) -> float:
    """Calculate price volatility"""
    if len(prices) < 2:
        return 0

    avg_price = sum(prices) / len(prices)
    variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
    volatility = (variance ** 0.5 / avg_price) * 100 if avg_price > 0 else 0

    return round(volatility, 2)


def get_top_market(data: List) -> str:
    """Get top market by price"""
    if not data:
        return "N/A"

    top_market = max(data, key=lambda x: x.modal_price)
    return f"{top_market.market}, {top_market.district}"


def generate_basic_recommendations(data: List) -> List[str]:
    """Generate basic recommendations"""
    if not data:
        return ["पर्याप्त डेटा नहीं है"]

    avg_price = sum(d.modal_price for d in data) / len(data)
    max_price = max(d.modal_price for d in data)

    recommendations = []

    if (max_price - avg_price) / avg_price > 0.15:
        recommendations.append("कुछ मंडियों में 15% ज्यादा दाम मिल रहा है")

    up_trends = len([d for d in data if d.trend == 'up'])
    if up_trends > len(data) * 0.6:
        recommendations.append("अधिकतर मंडियों में तेजी है - बेचने का अच्छा समय")

    return recommendations[:3]


def generate_selling_strategy(recent_data: List, analytics, quality: str, quantity: Optional[float]) -> Dict[str, str]:
    """Generate selling strategy"""
    strategy = {}

    # Determine market condition
    if analytics and analytics.weekly_trend == 'up':
        strategy["immediate"] = "50% फसल तुरंत बेचें - कीमतें अच्छी हैं"
        strategy["short_term"] = "30% फसल 1 सप्ताह में बेचें"
        strategy["long_term"] = "20% फसल स्टोरेज करें अगर और तेजी की उम्मीद है"
    elif analytics and analytics.weekly_trend == 'down':
        strategy["immediate"] = "तुरंत बेचने से बचें अगर संभव हो"
        strategy["short_term"] = "बेहतर मंडी की तलाश करें"
        strategy["long_term"] = "गुणवत्ता बनाए रखने पर फोकस करें"
    else:
        strategy["immediate"] = "नियमित बिक्री करते रहें"
        strategy["short_term"] = "मार्केट मॉनिटर करें"
        strategy["long_term"] = "स्थिर कीमतों का फायदा उठाएं"

    return strategy


def generate_timing_advice(recent_data: List, analytics) -> str:
    """Generate timing advice"""
    if analytics and analytics.predicted_price_7d and analytics.avg_price:
        if analytics.predicted_price_7d > analytics.avg_price * 1.05:
            return "अगले सप्ताह कीमतें बढ़ सकती हैं - थोड़ा इंतजार करें"
        elif analytics.predicted_price_7d < analytics.avg_price * 0.95:
            return "कीमतें गिर सकती हैं - जल्दी बेच दें"

    return "मार्केट मॉनिटर करके बेचें"


def get_storage_advice(crop_name: str, quality: str) -> str:
    """Get storage advice for crop"""
    storage_advice = {
        "tomato": "टमाटर को 10-12°C में रखें, 5-7 दिन तक टिक सकती है",
        "onion": "प्याज को सूखी जगह रखें, 20-30 दिन तक रह सकती है",
        "potato": "आलू को अंधेरी, ठंडी जगह रखें",
        "wheat": "गेहूं को नमी रहित जगह स्टोर करें"
    }

    base_advice = storage_advice.get(crop_name.lower(), "उचित तापमान और नमी में रखें")

    if quality == "high":
        return base_advice + " - अच्छी क्वालिटी के कारण ज्यादा दिन रह सकती है"
    elif quality == "low":
        return base_advice + " - कम क्वालिटी के कारण जल्दी बेच देना बेहतर"

    return base_advice


def get_negotiation_tips(quality: str, recent_data: List) -> List[str]:
    """Get negotiation tips"""
    tips = [
        "कई व्यापारियों से भाव पूछें",
        "मार्केट रेट पता करके जाएं",
        "तोल में कमी न होने दें"
    ]

    if quality == "high":
        tips.append("अच्छी क्वालिटी का फायदा उठाकर प्रीमियम मांगें")

    if recent_data and len(recent_data) > 1:
        price_range = max(d.modal_price for d in recent_data) - min(d.modal_price for d in recent_data)
        if price_range > 100:
            tips.append("कीमतों में अंतर है - बेहतर दाम की तलाश करें")

    return tips


def calculate_expected_revenue(latest_price, quantity: float, quality_factor: float) -> Dict[str, float]:
    """Calculate expected revenue"""
    base_revenue = latest_price.modal_price * quantity * quality_factor
    min_revenue = latest_price.min_price * quantity * quality_factor
    max_revenue = latest_price.max_price * quantity * quality_factor

    return {
        "expected_revenue": round(base_revenue, 2),
        "min_revenue": round(min_revenue, 2),
        "max_revenue": round(max_revenue, 2),
        "per_quintal_rate": round(latest_price.modal_price * quality_factor, 2)
    }


def estimate_distance(location1: str, location2: str) -> str:
    """Estimate distance between locations (simplified)"""
    if not location1 or not location2:
        return "अज्ञात"

    # Simple state-based distance estimation
    state_distances = {
        ("punjab", "haryana"): "150 किमी",
        ("maharashtra", "gujarat"): "200 किमी",
        ("uttar pradesh", "bihar"): "180 किमी"
    }

    return "लगभग 100-200 किमी"  # Default estimate


def estimate_distance_simple(lat: float, lng: float, state: str, district: str) -> float:
    """Simplified distance estimation"""
    # State center coordinates (approximate)
    state_coords = {
        "punjab": (31.1471, 75.3412),
        "haryana": (29.0588, 76.0856),
        "uttar pradesh": (26.8467, 80.9462),
        "maharashtra": (19.7515, 75.7139),
        "gujarat": (23.0225, 72.5714),
        "rajasthan": (27.0238, 74.2179),
        "andhra pradesh": (15.9129, 79.7400),
        "karnataka": (15.3173, 75.7139),
        "tamil nadu": (11.1271, 78.6569),
        "west bengal": (22.9868, 87.8550),
        "bihar": (25.0961, 85.3131),
        "jharkhand": (23.6102, 85.2799)
    }

    state_coord = state_coords.get(state.lower(), (20.5937, 78.9629))  # Default to India center

    # Simple distance calculation (Euclidean approximation)
    lat_diff = abs(lat - state_coord[0])
    lng_diff = abs(lng - state_coord[1])
    distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # Rough km conversion

    return round(distance, 1)


def translate_crop_name(english_name: str) -> str:
    """Translate crop names to Hindi"""
    translations = {
        "wheat": "गेहूं",
        "rice": "चावल",
        "paddy": "धान",
        "tomato": "टमाटर",
        "onion": "प्याज",
        "potato": "आलू",
        "sugarcane": "गन्ना",
        "cotton": "कपास",
        "soybean": "सोयाबीन",
        "soyabean": "सोयाबीन",
        "maize": "मक्का",
        "bajra": "बाजरा",
        "jowar": "ज्वार",
        "groundnut": "मूंगफली",
        "mustard": "सरसों",
        "sunflower": "सूरजमुखी",
        "sesame": "तिल",
        "turmeric": "हल्दी",
        "coriander": "धनिया",
        "cumin": "जीरा",
        "chilli": "मिर्च",
        "garlic": "लहसुन",
        "ginger": "अदरक",
        "coconut": "नारियल",
        "banana": "केला",
        "mango": "आम",
        "apple": "सेब",
        "grapes": "अंगूर",
        "orange": "संतरा",
        "lemon": "नींबू",
        "pomegranate": "अनार",
        "papaya": "पपीता",
        "guava": "अमरूद",
        "moong": "मूंग",
        "chana": "चना",
        "arhar": "अरहर",
        "urad": "उड़द",
        "masoor": "मसूर",
        "gram": "चना",
        "black gram": "उड़द",
        "green gram": "मूंग",
        "red gram": "अरहर",
        "bengal gram": "चना"
    }

    # Clean the input
    clean_name = english_name.lower().strip()

    # Try exact match first
    if clean_name in translations:
        return translations[clean_name]

    # Try partial match
    for english, hindi in translations.items():
        if english in clean_name or clean_name in english:
            return hindi

    # If no translation found, return title case of original
    return english_name.title()


def normalize_crop_name(crop_name: str) -> str:
    """Normalize crop name for database queries"""
    # Convert Hindi to English for database queries
    hindi_to_english = {
        "गेहूं": "wheat",
        "चावल": "rice",
        "धान": "paddy",
        "टमाटर": "tomato",
        "प्याज": "onion",
        "आलू": "potato",
        "गन्ना": "sugarcane",
        "कपास": "cotton",
        "सोयाबीन": "soybean",
        "मक्का": "maize",
        "बाजरा": "bajra",
        "ज्वार": "jowar",
        "मूंगफली": "groundnut",
        "सरसों": "mustard",
        "सूरजमुखी": "sunflower",
        "तिल": "sesame",
        "हल्दी": "turmeric",
        "धनिया": "coriander",
        "जीरा": "cumin",
        "मिर्च": "chilli",
        "लहसुन": "garlic",
        "अदरक": "ginger"
    }

    clean_name = crop_name.strip()

    # If Hindi name, convert to English
    if clean_name in hindi_to_english:
        return hindi_to_english[clean_name]

    # Return lowercase English name
    return clean_name.lower()


# ============================================================================
# Validation Functions
# ============================================================================

def validate_crop_name(crop_name: str) -> tuple:
    """Validate crop name"""
    if not crop_name or not crop_name.strip():
        return False, "फसल का नाम खाली नहीं हो सकता"

    if len(crop_name.strip()) < 2:
        return False, "फसल का नाम कम से कम 2 अक्षर का होना चाहिए"

    return True, ""


def validate_location(location: str) -> tuple:
    """Validate location"""
    if not location or not location.strip():
        return False, "स्थान खाली नहीं हो सकता"

    if len(location.strip()) < 2:
        return False, "स्थान का नाम कम से कम 2 अक्षर का होना चाहिए"

    return True, ""


# ============================================================================
# Market Data Utilities
# ============================================================================

def get_market_summary() -> Dict[str, Any]:
    """Get overall market summary"""
    try:
        with get_db_session() as db:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Get today's data
            today_data = db.query(MarketPrice).filter(
                MarketPrice.arrival_date >= today
            ).all()

            if not today_data:
                return {"status": "no_data", "message": "आज का डेटा उपलब्ध नहीं है"}

            total_records = len(today_data)
            unique_commodities = len(set(record.commodity for record in today_data))
            unique_markets = len(set(f"{record.market}-{record.district}" for record in today_data))

            # Calculate average prices and trends
            avg_price = sum(record.modal_price for record in today_data) / total_records

            trends = [record.trend for record in today_data if record.trend]
            up_trends = trends.count('up')
            down_trends = trends.count('down')
            stable_trends = trends.count('stable')

            return {
                "status": "success",
                "date": today.strftime("%d-%m-%Y"),
                "total_records": total_records,
                "unique_commodities": unique_commodities,
                "unique_markets": unique_markets,
                "average_price": round(avg_price, 2),
                "trends": {
                    "up": up_trends,
                    "down": down_trends,
                    "stable": stable_trends
                },
                "market_sentiment": "bullish" if up_trends > down_trends else "bearish" if down_trends > up_trends else "neutral"
            }

    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return {"status": "error", "message": "मार्केट समरी प्राप्त करने में समस्या"}


def get_trending_commodities(limit: int = 5) -> List[Dict[str, Any]]:
    """Get trending commodities based on price changes"""
    try:
        with get_db_session() as db:
            # Get commodities with recent price changes
            trending = db.query(MarketPrice).filter(
                and_(
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=1),
                    MarketPrice.percentage_change != None,
                    MarketPrice.percentage_change != 0
                )
            ).order_by(desc(MarketPrice.percentage_change)).limit(limit).all()

            trending_data = []
            for record in trending:
                trending_data.append({
                    "commodity": translate_crop_name(record.commodity),
                    "current_price": record.modal_price,
                    "percentage_change": record.percentage_change,
                    "trend": record.trend,
                    "market": f"{record.market}, {record.district}"
                })

            return trending_data

    except Exception as e:
        logger.error(f"Error getting trending commodities: {e}")
        return []


def search_markets(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search markets by commodity, location, or market name"""
    try:
        with get_db_session() as db:
            # Search in multiple fields
            search_results = db.query(MarketPrice).filter(
                and_(
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=2),
                    or_(
                        MarketPrice.commodity.ilike(f"%{query}%"),
                        MarketPrice.market.ilike(f"%{query}%"),
                        MarketPrice.district.ilike(f"%{query}%"),
                        MarketPrice.state.ilike(f"%{query}%")
                    )
                )
            ).order_by(desc(MarketPrice.modal_price)).limit(limit).all()

            results = []
            for record in search_results:
                results.append({
                    "commodity": translate_crop_name(record.commodity),
                    "market_name": f"{record.market}, {record.district}, {record.state}",
                    "current_price": record.modal_price,
                    "trend": record.trend,
                    "arrival_date": record.arrival_date.strftime("%d-%m-%Y"),
                    "variety": record.variety or "स्टैंडर्ड",
                    "grade": record.grade or "FAQ"
                })

            return results

    except Exception as e:
        logger.error(f"Error searching markets: {e}")
        return []


def get_nearest_profitable_markets(
        crop_name: str,
        user_latitude: float,
        user_longitude: float,
        max_distance_km: int = 100,
        quality: str = "medium",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Find nearest markets with highest profitability considering transport costs

    Args:
        crop_name (str): Name of the crop
        user_latitude (float): User's latitude
        user_longitude (float): User's longitude
        max_distance_km (int): Maximum distance to search (default 100km)
        quality (str): Crop quality - high/medium/low
        tool_context (ToolContext): Session context

    Returns:
        Dict: Nearest profitable markets with distance and net profit calculations
    """
    logger.info(f"Finding profitable markets for {crop_name} within {max_distance_km}km")

    try:
        # Validate inputs
        is_valid, error_msg = validate_crop_name(crop_name)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        user_location = {
            "latitude": user_latitude,
            "longitude": user_longitude
        }

        # Get profitable markets
        result = market_service.get_nearest_profitable_markets(crop_name, user_location, quality)

        # Update session context
        if tool_context and result.get("status") == "success":
            tool_context.state["last_market_search"] = {
                "crop": crop_name,
                "location": user_location,
                "quality": quality,
                "timestamp": datetime.now().isoformat()
            }

        return result

    except Exception as e:
        logger.error(f"Error finding profitable markets: {e}")
        return {
            "status": "error",
            "message": "लाभदायक मंडी खोजने में समस्या हुई"
        }


def get_spoilage_prevention_advice(
        crop_name: str,
        quantity_quintals: float,
        current_condition: str = "fresh",
        expected_selling_days: int = 3,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get advice to prevent crop spoilage and minimize losses

    Args:
        crop_name (str): Name of the crop
        quantity_quintals (float): Quantity in quintals
        current_condition (str): Current condition - fresh/good/fair/poor
        expected_selling_days (int): Days until planned selling
        tool_context (ToolContext): Session context

    Returns:
        Dict: Spoilage prevention advice and loss minimization strategies
    """
    logger.info(f"Getting spoilage prevention advice for {crop_name}")

    try:
        # Validate inputs
        is_valid, error_msg = validate_crop_name(crop_name)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        # Get current market price for loss calculation
        price_data = market_service.get_real_time_prices(crop_name)
        current_price = 0

        if price_data.get("status") == "success" and price_data.get("top_markets"):
            current_price = price_data["top_markets"][0]["modal_price"]

        # Get spoilage advice
        advice = market_service.get_spoilage_prevention_advice(crop_name, quantity_quintals, current_price)

        # Add condition-based urgency adjustment
        if current_condition in ["fair", "poor"]:
            advice["urgency_level"] = "अत्यधिक तत्काल"
            advice["immediate_action"] = "तुरंत बेच दें - और देरी नुकसानदायक होगी"

        # Update session context
        if tool_context:
            tool_context.state["spoilage_alerts"] = tool_context.state.get("spoilage_alerts", [])
            tool_context.state["spoilage_alerts"].append({
                "crop": crop_name,
                "quantity": quantity_quintals,
                "condition": current_condition,
                "urgency": advice.get("urgency_level"),
                "timestamp": datetime.now().isoformat()
            })
            # Keep only last 5 alerts
            tool_context.state["spoilage_alerts"] = tool_context.state["spoilage_alerts"][-5:]

        return advice

    except Exception as e:
        logger.error(f"Error getting spoilage advice: {e}")
        return {
            "status": "error",
            "message": "फसल खराब होने से बचाव की सलाह में समस्या हुई"
        }


def predict_price_trends(
        crop_name: str,
        prediction_days: int = 14,
        include_seasonal_factors: bool = True,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Predict crop price trends for coming weeks using historical data and ML

    Args:
        crop_name (str): Name of the crop
        prediction_days (int): Number of days to predict (default 14)
        include_seasonal_factors (bool): Include seasonal price patterns
        tool_context (ToolContext): Session context

    Returns:
        Dict: Price predictions with trend analysis and selling recommendations
    """
    logger.info(f"Predicting price trends for {crop_name} for {prediction_days} days")

    try:
        # Validate inputs
        is_valid, error_msg = validate_crop_name(crop_name)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        # Get price predictions
        predictions = market_service.predict_price_trends(crop_name, prediction_days)

        # Add seasonal context if requested
        if include_seasonal_factors and predictions.get("status") == "success":
            seasonal_info = _get_seasonal_price_context(crop_name)
            predictions["seasonal_context"] = seasonal_info

        # Generate actionable recommendations
        if predictions.get("status") == "success":
            predictions["selling_strategy"] = _generate_selling_strategy_from_predictions(
                predictions["predictions"], predictions["trend_analysis"]
            )

        # Update session context
        if tool_context and predictions.get("status") == "success":
            tool_context.state["price_predictions"] = {
                "crop": crop_name,
                "predictions": predictions["predictions"][:7],  # Store 1 week
                "generated_at": datetime.now().isoformat()
            }

        return predictions

    except Exception as e:
        logger.error(f"Error predicting prices: {e}")
        return {
            "status": "error",
            "message": "कीमत पूर्वानुमान में समस्या हुई"
        }


def get_real_time_market_dashboard(
        crops: List[str],
        user_latitude: float,
        user_longitude: float,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get comprehensive market dashboard for multiple crops

    Args:
        crops (List[str]): List of crop names
        user_latitude (float): User's latitude
        user_longitude (float): User's longitude
        tool_context (ToolContext): Session context

    Returns:
        Dict: Comprehensive market dashboard with all crops data
    """
    logger.info(f"Creating market dashboard for crops: {crops}")

    try:
        user_location = {
            "latitude": user_latitude,
            "longitude": user_longitude
        }

        dashboard_data = {
            "status": "success",
            "user_location": user_location,
            "crops_data": {},
            "market_summary": {},
            "alerts": [],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        total_markets_found = 0
        best_opportunities = []

        # Get data for each crop
        for crop in crops:
            try:
                # Get market data
                crop_data = market_service.get_real_time_prices(crop, user_location, max_distance_km=150)

                if crop_data.get("status") == "success":
                    dashboard_data["crops_data"][crop] = crop_data
                    total_markets_found += crop_data.get("total_markets_found", 0)

                    # Identify best opportunities
                    if crop_data.get("top_markets"):
                        best_market = crop_data["top_markets"][0]
                        best_opportunities.append({
                            "crop": crop,
                            "market": best_market["market_name"],
                            "price": best_market["modal_price"],
                            "distance": best_market.get("distance_km", "N/A")
                        })

                    # Get spoilage alerts
                    spoilage_advice = market_service.get_spoilage_prevention_advice(crop, 10,
                                                                                    best_market["modal_price"])
                    if spoilage_advice.get("urgency_level") in ["अत्यधिक तत्काल", "तत्काल"]:
                        dashboard_data["alerts"].append({
                            "type": "spoilage_warning",
                            "crop": crop,
                            "message": f"{crop} जल्दी खराब हो सकती है - तुरंत बेचें",
                            "urgency": spoilage_advice["urgency_level"]
                        })

            except Exception as e:
                logger.warning(f"Error processing crop {crop}: {e}")
                dashboard_data["crops_data"][crop] = {
                    "status": "error",
                    "message": f"{crop} के लिए डेटा प्राप्त नहीं हो सका"
                }

        # Generate market summary
        dashboard_data["market_summary"] = {
            "total_crops_tracked": len(crops),
            "total_markets_found": total_markets_found,
            "best_opportunities": sorted(best_opportunities, key=lambda x: x["price"], reverse=True)[:3],
            "market_status": "सक्रिय" if total_markets_found > 0 else "सीमित डेटा"
        }

        # Update session context
        if tool_context:
            tool_context.state["dashboard_data"] = {
                "crops": crops,
                "last_updated": datetime.now().isoformat(),
                "alerts_count": len(dashboard_data["alerts"])
            }

        return dashboard_data

    except Exception as e:
        logger.error(f"Error creating market dashboard: {e}")
        return {
            "status": "error",
            "message": "मार्केट डैशबोर्ड बनाने में समस्या हुई"
        }


def get_transportation_cost_calculator(
        crop_name: str,
        quantity_quintals: float,
        from_latitude: float,
        from_longitude: float,
        to_markets: List[str],
        vehicle_type: str = "truck",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Calculate transportation costs to different markets

    Args:
        crop_name (str): Name of the crop
        quantity_quintals (float): Quantity in quintals
        from_latitude (float): Origin latitude
        from_longitude (float): Origin longitude
        to_markets (List[str]): List of target market names
        vehicle_type (str): Type of vehicle - truck/tempo/tractor
        tool_context (ToolContext): Session context

    Returns:
        Dict: Transportation cost breakdown and profit analysis
    """
    logger.info(f"Calculating transportation costs for {crop_name}")

    try:
        # Vehicle cost per km per quintal
        vehicle_costs = {
            "truck": 2.5,  # ₹2.5 per km per quintal
            "tempo": 3.0,  # ₹3.0 per km per quintal
            "tractor": 2.0,  # ₹2.0 per km per quintal
            "pickup": 4.0  # ₹4.0 per km per quintal
        }

        cost_per_km = vehicle_costs.get(vehicle_type, 2.5)

        # Get market data
        user_location = {"latitude": from_latitude, "longitude": from_longitude}
        market_data = market_service.get_real_time_prices(crop_name, user_location)

        if market_data.get("status") != "success":
            return {
                "status": "error",
                "message": f"{crop_name} के लिए मार्केट डेटा उपलब्ध नहीं है"
            }

        transport_analysis = []

        # Analyze each market
        for market in market_data.get("top_markets", [])[:10]:  # Top 10 markets
            if any(target_market.lower() in market["market_name"].lower() for target_market in to_markets):
                distance = market.get("distance_km", 50)  # Default 50km if not available

                # Calculate costs
                transport_cost = distance * cost_per_km * quantity_quintals
                total_revenue = market["modal_price"] * quantity_quintals
                net_profit = total_revenue - transport_cost
                profit_margin = (net_profit / total_revenue) * 100 if total_revenue > 0 else 0

                transport_analysis.append({
                    "market_name": market["market_name"],
                    "distance_km": distance,
                    "market_price": market["modal_price"],
                    "transport_cost": round(transport_cost, 2),
                    "total_revenue": round(total_revenue, 2),
                    "net_profit": round(net_profit, 2),
                    "profit_margin": round(profit_margin, 2),
                    "travel_time_hours": round(distance / 40, 1),  # Assuming 40 km/hr
                    "fuel_cost_estimate": round(distance * 8, 2),  # ₹8 per km fuel
                    "recommended": net_profit > 0 and profit_margin > 15
                })

        # Sort by net profit
        transport_analysis.sort(key=lambda x: x["net_profit"], reverse=True)

        # Generate recommendations
        best_option = transport_analysis[0] if transport_analysis else None
        recommendations = _generate_transport_recommendations(transport_analysis, quantity_quintals)

        result = {
            "status": "success",
            "crop": crop_name,
            "quantity_quintals": quantity_quintals,
            "vehicle_type": vehicle_type,
            "cost_per_km_per_quintal": cost_per_km,
            "transport_analysis": transport_analysis,
            "best_option": best_option,
            "recommendations": recommendations,
            "total_markets_analyzed": len(transport_analysis)
        }

        # Update session context
        if tool_context and best_option:
            tool_context.state["transport_calculations"] = {
                "crop": crop_name,
                "best_market": best_option["market_name"],
                "net_profit": best_option["net_profit"],
                "calculated_at": datetime.now().isoformat()
            }

        return result

    except Exception as e:
        logger.error(f"Error calculating transportation costs: {e}")
        return {
            "status": "error",
            "message": "परिवहन लागत की गणना में समस्या हुई"
        }


# Helper functions
def _get_seasonal_price_context(crop_name: str) -> Dict[str, Any]:
    """Get seasonal price patterns for the crop"""
    seasonal_patterns = {
        "tomato": {
            "peak_season": "जनवरी-मार्च",
            "lean_season": "जुलाई-सितंबर",
            "price_factor": "सर्दी में अच्छे दाम, बारिश में कम दाम"
        },
        "onion": {
            "peak_season": "अक्टूबर-दिसंबर",
            "lean_season": "अप्रैल-जून",
            "price_factor": "भंडारण के बाद दाम बढ़ते हैं"
        },
        "potato": {
            "peak_season": "फरवरी-अप्रैल",
            "lean_season": "जुलाई-सितंबर",
            "price_factor": "गर्मी में अच्छे दाम मिलते हैं"
        }
    }

    crop_normalized = crop_name.lower()
    return seasonal_patterns.get(crop_normalized, {
        "general": "मौसम और त्योहारों के आधार पर दाम बदलते रहते हैं"
    })


def _generate_selling_strategy_from_predictions(predictions: List[Dict], trend_analysis: Dict) -> Dict[str, str]:
    """Generate selling strategy based on price predictions"""
    if not predictions:
        return {"strategy": "डेटा अपर्याप्त है"}

    current_price = predictions[0]["predicted_price"]
    future_prices = [p["predicted_price"] for p in predictions[3:]]  # 3+ days ahead
    avg_future_price = sum(future_prices) / len(future_prices) if future_prices else current_price

    price_change_percent = ((avg_future_price - current_price) / current_price) * 100

    if price_change_percent > 5:
        return {
            "strategy": "इंतजार करें",
            "reason": f"आने वाले दिनों में {price_change_percent:.1f}% तक दाम बढ़ सकते हैं",
            "timing": "1-2 सप्ताह बाद बेचें"
        }
    elif price_change_percent < -5:
        return {
            "strategy": "तुरंत बेचें",
            "reason": f"आने वाले दिनों में {abs(price_change_percent):.1f}% तक दाम गिर सकते हैं",
            "timing": "आज ही बेच देना बेहतर है"
        }
    else:
        return {
            "strategy": "लचीला दृष्टिकोण",
            "reason": "दाम में बड़ा बदलाव नहीं दिख रहा",
            "timing": "अपनी जरूरत के हिसाब से बेच सकते हैं"
        }


def _generate_transport_recommendations(transport_analysis: List[Dict], quantity: float) -> Dict[str, str]:
    """Generate transportation recommendations"""
    if not transport_analysis:
        return {"message": "कोई उपयुक्त मार्केट नहीं मिला"}

    profitable_markets = [m for m in transport_analysis if m["net_profit"] > 0]

    if not profitable_markets:
        return {
            "warning": "सभी मार्केट में परिवहन लागत ज्यादा है",
            "suggestion": "स्थानीय मंडी में बेचना बेहतर हो सकता है"
        }

    best_market = profitable_markets[0]

    if best_market["profit_margin"] > 25:
        return {
            "recommendation": "बहुत अच्छा अवसर",
            "action": f"{best_market['market_name']} में बेचें",
            "profit": f"₹{best_market['net_profit']} का शुद्ध लाभ"
        }
    elif best_market["profit_margin"] > 15:
        return {
            "recommendation": "अच्छा अवसर",
            "action": f"{best_market['market_name']} में बेचने पर फायदा है",
            "consideration": "परिवहन व्यवस्था पहले से करें"
        }
    else:
        return {
            "recommendation": "सामान्य लाभ",
            "action": "स्थानीय और दूर की मंडी में तुलना करें",
            "suggestion": "छोटी मात्रा में टेस्ट करके देखें"
        }

# ============================================================================
# Export Functions for API Usage
# ============================================================================

__all__ = [
    'get_market_prices',
    'get_price_analysis',
    'get_selling_advice',
    'get_location_based_markets',
    'get_market_carousel_data',
    'get_comprehensive_market_analysis',
    'get_market_summary',
    'get_trending_commodities',
    'search_markets',
    'translate_crop_name',
    'normalize_crop_name',
    'validate_crop_name',
    'validate_location'
]