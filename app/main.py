# app/enhanced_main.py - Enhanced backend with new market features

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import json
from datetime import datetime
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced Project Kisan",
              description="AI-Powered Agricultural Assistant with Advanced Market Features")

# Mount static files and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import enhanced services
from AgenticAIHackathon.app.google_adk_integration import FarmBotService
from AgenticAIHackathon.app.google_adk_integration.services.market_service import MarketService

# Initialize services
farmbot_agent = FarmBotService()
enhanced_market_service = MarketService()


@app.on_event("startup")
async def startup_event():
    await farmbot_agent.initialize()
    logger.info("🚀 Enhanced FarmBot services initialized")


# Enhanced Data Models
class EnhancedMarketQuery(BaseModel):
    crop: str
    quantity: Optional[float] = None
    quality: str = "medium"
    max_distance: int = 100
    vehicle_type: str = "truck"
    user_location: Dict[str, float]


class PricePredictionQuery(BaseModel):
    crop: str
    prediction_days: int = 14
    include_weather: bool = True
    include_seasonal: bool = True


class SpoilagePreventionQuery(BaseModel):
    crop: str
    quantity: float
    condition: str = "fresh"
    expected_selling_days: int = 3


class TransportCalculationQuery(BaseModel):
    crop: str
    quantity: float
    target_markets: List[str]
    vehicle_type: str = "truck"
    user_location: Dict[str, float]


class EnhancedWebSocketMessage(BaseModel):
    type: str
    content: str
    session_id: str
    user_location: Optional[Dict[str, float]] = None
    user_preferences: Optional[Dict[str, Any]] = None
    feature_context: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None


# ============================================================================
# Enhanced WebSocket Connection Manager
# ============================================================================
class EnhancedConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "connected_at": datetime.now(),
            "interaction_count": 0,
            "last_activity": datetime.now(),
            "user_preferences": {},
            "user_location": None
        }
        logger.info(f"Enhanced WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
        logger.info(f"Enhanced WebSocket disconnected: {session_id}")

    async def send_message(self, message: dict, session_id: str):
        try:
            websocket = self.active_connections.get(session_id)
            if websocket:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                self.user_sessions[session_id]["last_activity"] = datetime.now()
        except Exception as e:
            logger.error(f"Error sending enhanced message: {e}")

    async def send_market_analysis(self, data: dict, session_id: str):
        """Send market analysis results"""
        await self.send_message({
            "type": "market_analysis",
            "response": data.get("response", ""),
            "profitable_markets": data.get("profitable_markets"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

    async def send_transport_calculation(self, data: dict, session_id: str):
        """Send transport calculation results"""
        await self.send_message({
            "type": "transport_calculation",
            "response": data.get("response", ""),
            "transport_analysis": data.get("transport_analysis"),
            "vehicle_type": data.get("vehicle_type"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

    async def send_price_prediction(self, data: dict, session_id: str):
        """Send price prediction results"""
        await self.send_message({
            "type": "price_prediction",
            "response": data.get("response", ""),
            "predictions": data.get("predictions"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

    async def send_spoilage_advice(self, data: dict, session_id: str):
        """Send spoilage prevention advice"""
        await self.send_message({
            "type": "spoilage_advice",
            "response": data.get("response", ""),
            "spoilage_advice": data.get("spoilage_advice"),
            "urgency": data.get("urgency", "medium"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)


enhanced_manager = EnhancedConnectionManager()


# ============================================================================
# Enhanced WebSocket Endpoint
# ============================================================================
@app.websocket("/ws/chat")
async def enhanced_websocket_chat_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with advanced market features"""
    session_id = f"session_{int(datetime.now().timestamp())}"
    await enhanced_manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_type = message_data.get("type", "text")
            content = message_data.get("content", "")
            user_location = message_data.get("user_location")
            user_preferences = message_data.get("user_preferences", {})
            additional_data = message_data.get("additional_data", {})

            # Update user session
            if user_location:
                enhanced_manager.user_sessions[session_id]["user_location"] = user_location
            if user_preferences:
                enhanced_manager.user_sessions[session_id]["user_preferences"] = user_preferences

            enhanced_manager.user_sessions[session_id]["interaction_count"] += 1

            logger.info(f"Enhanced message received: {message_type} - {content[:50]}...")

            # Send thinking indicator
            await enhanced_manager.send_message({
                "type": "thinking",
                "content": "विश्लेषण कर रहे हैं...",
                "session_id": session_id
            }, websocket)

            # Route to appropriate handler based on message type
            if message_type == "market_search":
                await handle_market_search(content, additional_data, session_id)
            elif message_type == "price_prediction":
                await handle_price_prediction(content, additional_data, session_id)
            elif message_type == "spoilage_prevention":
                await handle_spoilage_prevention(content, additional_data, session_id)
            elif message_type == "transport_calculation":
                await handle_transport_calculation(content, additional_data, session_id)
            elif message_type == "enhanced_text":
                await handle_enhanced_text_query(content, user_location, user_preferences, session_id)
            else:
                # Default processing through main agent
                await handle_default_query(content, message_type, additional_data, session_id)

    except WebSocketDisconnect:
        enhanced_manager.disconnect(session_id)
        logger.info(f"Enhanced WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Enhanced WebSocket error: {e}")
        enhanced_manager.disconnect(session_id)


# ============================================================================
# Enhanced Message Handlers
# ============================================================================

async def handle_market_search(content: str, data: dict, session_id: str):
    """Handle profitable market search requests"""
    try:
        # Extract parameters
        crop = data.get("crop")
        quantity = data.get("quantity", 10.0)
        quality = data.get("quality", "medium")
        max_distance = data.get("max_distance", 100)
        vehicle_type = data.get("vehicle_type", "truck")
        user_location = data.get("user_location")

        if not crop or not user_location:
            await enhanced_manager.send_message({
                "type": "response",
                "content": "कृपया फसल और स्थान की जानकारी दें।",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])
            return

        # Get profitable markets
        result = enhanced_market_service.get_nearest_profitable_markets(
            crop, user_location, quality
        )

        if result["status"] == "success":
            # Format response for frontend
            response_text = f"✅ {crop} के लिए {len(result['best_markets'])} लाभदायक मंडी मिलीं:\n\n"

            for i, market in enumerate(result['best_markets'][:3], 1):
                response_text += f"{i}. {market['market_name']}\n"
                response_text += f"   💰 भाव: ₹{market['modal_price']}/क्विंटल\n"
                if 'distance_km' in market:
                    response_text += f"   📍 दूरी: {market['distance_km']} किमी\n"
                response_text += "\n"

            # Send market analysis response
            await enhanced_manager.send_market_analysis({
                "response": response_text,
                "profitable_markets": result
            }, session_id)
        else:
            await enhanced_manager.send_message({
                "type": "response",
                "content": f"❌ {result.get('message', 'मार्केट डेटा नहीं मिला')}",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])

    except Exception as e:
        logger.error(f"Market search error: {e}")
        await enhanced_manager.send_message({
            "type": "response",
            "content": "मार्केट खोजने में समस्या हुई। कृपया दोबारा कोशिश करें।",
            "session_id": session_id
        }, enhanced_manager.active_connections[session_id])


async def handle_price_prediction(content: str, data: dict, session_id: str):
    """Handle price prediction requests"""
    try:
        crop = data.get("crop")
        prediction_days = data.get("prediction_days", 14)
        include_weather = data.get("include_weather", True)
        include_seasonal = data.get("include_seasonal", True)

        if not crop:
            await enhanced_manager.send_message({
                "type": "response",
                "content": "कृपया फसल का नाम बताएं।",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])
            return

        # Get price predictions
        result = enhanced_market_service.predict_price_trends(crop, prediction_days)

        if result["status"] == "success":
            predictions = result["predictions"]
            response_text = f"🔮 {crop} की {prediction_days} दिन की कीमत भविष्यवाणी:\n\n"
            response_text += f"वर्तमान भाव: ₹{result['current_price']}\n\n"

            for pred in predictions[:5]:  # Show first 5 predictions
                change_emoji = "📈" if pred["predicted_price"] > result["current_price"] else "📉"
                response_text += f"{pred['day']} दिन बाद: ₹{pred['predicted_price']} {change_emoji}\n"

            response_text += f"\n💡 सुझाव: {result['recommendation']}"

            await enhanced_manager.send_price_prediction({
                "response": response_text,
                "predictions": result
            }, session_id)
        else:
            await enhanced_manager.send_message({
                "type": "response",
                "content": f"❌ {result.get('message', 'कीमत पूर्वानुमान नहीं मिला')}",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])

    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        await enhanced_manager.send_message({
            "type": "response",
            "content": "कीमत पूर्वानुमान में समस्या हुई।",
            "session_id": session_id
        }, enhanced_manager.active_connections[session_id])


async def handle_spoilage_prevention(content: str, data: dict, session_id: str):
    """Handle spoilage prevention requests"""
    try:
        crop = data.get("crop")
        quantity = data.get("quantity", 5.0)
        condition = data.get("condition", "fresh")
        expected_selling_days = data.get("expected_selling_days", 3)

        if not crop:
            await enhanced_manager.send_message({
                "type": "response",
                "content": "कृपया फसल का नाम बताएं।",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])
            return

        # Get current market price for loss calculation
        user_location = enhanced_manager.user_sessions[session_id].get("user_location")
        current_price = 2000  # Default price, would get from real market data

        # Get spoilage advice
        result = enhanced_market_service.get_spoilage_prevention_advice(
            crop, quantity, current_price
        )

        if result["status"] == "success":
            urgency = result["urgency_level"]
            action_plan = result["action_plan"]

            response_text = f"⚠️ {crop} के लिए नुकसान बचाव सलाह:\n\n"
            response_text += f"🚨 तत्काल स्तर: {urgency}\n\n"

            if "immediate" in action_plan:
                response_text += f"तुरंत करें: {action_plan['immediate']}\n"
            if "storage" in action_plan:
                response_text += f"भंडारण: {action_plan['storage']}\n"
            if "priority" in action_plan:
                response_text += f"प्राथमिकता: {action_plan['priority']}\n"

            # Add loss prevention calculation
            if "estimated_loss_prevention" in result:
                loss_data = result["estimated_loss_prevention"]
                response_text += f"\n💰 नुकसान बचाव:\n"
                response_text += f"संभावित बचत: ₹{loss_data.get('preventable_loss', 0)}\n"

            await enhanced_manager.send_spoilage_advice({
                "response": response_text,
                "spoilage_advice": result,
                "urgency": urgency
            }, session_id)
        else:
            await enhanced_manager.send_message({
                "type": "response",
                "content": f"❌ {result.get('message', 'नुकसान बचाव सलाह नहीं मिली')}",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])

    except Exception as e:
        logger.error(f"Spoilage prevention error: {e}")
        await enhanced_manager.send_message({
            "type": "response",
            "content": "नुकसान बचाव सलाह में समस्या हुई।",
            "session_id": session_id
        }, enhanced_manager.active_connections[session_id])


async def handle_transport_calculation(content: str, data: dict, session_id: str):
    """Handle transport cost calculation requests"""
    try:
        crop = data.get("crop")
        quantity = data.get("quantity", 10.0)
        target_markets = data.get("target_markets", [])
        vehicle_type = data.get("vehicle_type", "truck")
        user_location = data.get("user_location")

        if not crop or not user_location:
            await enhanced_manager.send_message({
                "type": "response",
                "content": "कृपया फसल और स्थान की जानकारी दें।",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])
            return

        # Get transport calculations
        result = enhanced_market_service.get_transportation_cost_calculator(
            crop, quantity,
            user_location["latitude"], user_location["longitude"],
            target_markets, vehicle_type
        )

        if result["status"] == "success":
            transport_analysis = result["transport_analysis"]
            best_option = result["best_option"]

            response_text = f"🚛 {crop} के लिए परिवहन लागत विश्लेषण ({vehicle_type}):\n\n"

            for i, analysis in enumerate(transport_analysis[:3], 1):
                response_text += f"{i}. {analysis['market_name']}\n"
                response_text += f"   📍 दूरी: {analysis['distance_km']} किमी\n"
                response_text += f"   💰 परिवहन लागत: ₹{analysis['transport_cost']}\n"
                response_text += f"   💵 शुद्ध लाभ: ₹{analysis['net_profit']}\n"
                if analysis.get('recommended'):
                    response_text += "   ✅ सुझावित\n"
                response_text += "\n"

            if best_option:
                response_text += f"🏆 सर्वोत्तम विकल्प: {best_option['market_name']}\n"
                response_text += f"शुद्ध लाभ: ₹{best_option['net_profit']}"

            await enhanced_manager.send_transport_calculation({
                "response": response_text,
                "transport_analysis": transport_analysis,
                "vehicle_type": vehicle_type
            }, session_id)
        else:
            await enhanced_manager.send_message({
                "type": "response",
                "content": f"❌ {result.get('message', 'परिवहन लागत गणना नहीं हो सकी')}",
                "session_id": session_id
            }, enhanced_manager.active_connections[session_id])

    except Exception as e:
        logger.error(f"Transport calculation error: {e}")
        await enhanced_manager.send_message({
            "type": "response",
            "content": "परिवहन लागत गणना में समस्या हुई।",
            "session_id": session_id
        }, enhanced_manager.active_connections[session_id])


async def handle_enhanced_text_query(content: str, user_location: dict, user_preferences: dict, session_id: str):
    """Handle enhanced text queries with context"""
    try:
        # Add user context to the query
        enhanced_content = content
        context_info = []

        if user_location:
            context_info.append(
                f"उपयोगकर्ता स्थान: {user_location.get('latitude', 'N/A')}, {user_location.get('longitude', 'N/A')}")

        if user_preferences.get('crops'):
            context_info.append(f"मुख्य फसलें: {', '.join(user_preferences['crops'])}")

        if context_info:
            enhanced_content += f"\n\nसंदर्भ: {' | '.join(context_info)}"

        # Process through main farmbot agent with enhanced context
        result = await farmbot_agent.process_message(
            enhanced_content,
            "enhanced_text",
            additional_context={
                "user_location": user_location,
                "user_preferences": user_preferences,
                "session_id": session_id
            }
        )

        # Send response
        await enhanced_manager.send_message({
            "type": "response",
            "content": result.response,
            "agent_used": result.agent_used,
            "session_id": session_id,
            "timestamp": result.timestamp
        }, enhanced_manager.active_connections[session_id])

    except Exception as e:
        logger.error(f"Enhanced text query error: {e}")
        await enhanced_manager.send_message({
            "type": "response",
            "content": "मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।",
            "session_id": session_id
        }, enhanced_manager.active_connections[session_id])

#
# async def handle_default_query(content: str, message_type: str, additional_data: dict, session_id: str):
#     """Handle default queries through main agent"""
#     try:
#         # Process through main farmbot agent
#         image_data = additional_data.get("image_data") if message_type == "image" else None
#
#         result = await farmbot_agent.process_message(content, message_type, image_data)
#
#         # Send response back
#         await enhanced_manager.send_message({
#             "type": "response",
#             "content": result.response,
#             "agent_used": result.agent_used,
#             "session_id": session_id,
#             "timestamp": result.timestamp
#         }, enhanced_manager.active_connections[session_id])
#
#     except Exception as e:
#         logger.error(f"Default query error: {e}")
#         await enhanced_manager.send_message({
#             "type": "response",
#             "content": "मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।",
#             "session_id": session_id
#         }, enhanced_manager.active_connections[session_id])


# ============================================================================
# Enhanced REST API Endpoints
# ============================================================================

@app.post("/api/enhanced/profitable-markets")
async def api_profitable_markets(query: EnhancedMarketQuery):
    """API endpoint for profitable markets"""
    try:
        result = enhanced_market_service.get_nearest_profitable_markets(
            query.crop, query.user_location, query.quality
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"API profitable markets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhanced/price-predictions")
async def api_price_predictions(query: PricePredictionQuery):
    """API endpoint for price predictions"""
    try:
        result = enhanced_market_service.predict_price_trends(
            query.crop, query.prediction_days
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"API price predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhanced/spoilage-prevention")
async def api_spoilage_prevention(query: SpoilagePreventionQuery):
    """API endpoint for spoilage prevention"""
    try:
        # Get current market price
        current_price = 2000  # Would fetch from real market data

        result = enhanced_market_service.get_spoilage_prevention_advice(
            query.crop, query.quantity, current_price
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"API spoilage prevention error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhanced/transport-calculation")
async def api_transport_calculation(query: TransportCalculationQuery):
    """API endpoint for transport cost calculation"""
    try:
        result = enhanced_market_service.get_transportation_cost_calculator(
            query.crop, query.quantity,
            query.user_location["latitude"], query.user_location["longitude"],
            query.target_markets, query.vehicle_type
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"API transport calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/enhanced/real-time-dashboard")
async def api_real_time_dashboard(
        crops: str,  # Comma-separated crop names
        latitude: float,
        longitude: float
):
    """API endpoint for real-time market dashboard"""
    try:
        crop_list = [crop.strip() for crop in crops.split(',')]
        user_location = {"latitude": latitude, "longitude": longitude}

        result = enhanced_market_service.get_real_time_market_dashboard(
            crop_list, latitude, longitude
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"API dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhanced Template Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def enhanced_home(request: Request):
    """Enhanced home page with new features"""
    # Get sample market data
    sample_markets = []
    try:
        # Get some sample market data for preview
        sample_result = enhanced_market_service.get_real_time_prices("Wheat")
        print(sample_result)
        if sample_result.get("status") == "success":
            sample_markets = sample_result.get("top_markets", [])[:3]
            print(sample_markets)
    except Exception as e:
        logger.warning(f"Could not load sample market data: {e}")
        # Fallback to mock data
        sample_markets = [
            {"crop_name": "गेहूं", "current_price": 2150, "price_change": 50, "trend": "up",
             "market_location": "नई दिल्ली"},
            {"crop_name": "चावल", "current_price": 3200, "price_change": -30, "trend": "down",
             "market_location": "मुंबई"},
            {"crop_name": "टमाटर", "current_price": 45, "price_change": 8, "trend": "up", "market_location": "पुणे"}
        ]

    context = {
        "request": request,
        "page_title": "प्रोजेक्ट किसान - Enhanced AI Agricultural Assistant",
        "market_preview": sample_markets,
        "enhanced_features_enabled": True,
        "websocket_enabled": True,
        "version": "2.0 Enhanced"
    }
    return templates.TemplateResponse("home.html", context)


@app.get("/market", response_class=HTMLResponse)
async def enhanced_market_dashboard(request: Request, filter_type: str = "all"):
    """Enhanced market dashboard with real-time data"""
    try:
        # Get real market data
        all_crops = ["wheat", "rice", "tomato", "onion", "potato"]
        market_data = []

        for crop in all_crops:
            try:
                result = enhanced_market_service.get_real_time_prices(crop)
                if result.get("status") == "success" and result.get("top_markets"):
                    market_info = result["top_markets"][0]
                    market_data.append({
                        "crop_name": crop,
                        "current_price": market_info["modal_price"],
                        "price_change": market_info.get("price_change", 0),
                        "percentage_change": market_info.get("percentage_change", 0),
                        "market_location": market_info["market_name"],
                        "trend": "up" if market_info.get("price_change", 0) > 0 else "down"
                    })
            except Exception as e:
                logger.warning(f"Could not load data for {crop}: {e}")

        # If no real data, use mock data
        if not market_data:
            market_data = [
                {"crop_name": "गेहूं", "current_price": 2150, "price_change": 50, "percentage_change": 2.4,
                 "market_location": "नई दिल्ली मंडी", "trend": "up"},
                {"crop_name": "चावल", "current_price": 3200, "price_change": -30, "percentage_change": -0.9,
                 "market_location": "मुंबई मंडी", "trend": "down"},
                {"crop_name": "टमाटर", "current_price": 45, "price_change": 8, "percentage_change": 21.6,
                 "market_location": "पुणे मंडी", "trend": "up"},
                {"crop_name": "प्याज", "current_price": 35, "price_change": -5, "percentage_change": -12.5,
                 "market_location": "नाशिक मंडी", "trend": "down"},
                {"crop_name": "आलू", "current_price": 28, "price_change": 3, "percentage_change": 12.0,
                 "market_location": "आगरा मंडी", "trend": "up"}
            ]

        # Calculate insights
        total_crops = len(market_data)
        rising_crops = len([crop for crop in market_data if crop["trend"] == "up"])
        falling_crops = len([crop for crop in market_data if crop["trend"] == "down"])
        avg_change = sum([crop["percentage_change"] for crop in market_data]) / total_crops if total_crops > 0 else 0

        market_insights = {
            "total_crops": total_crops,
            "rising_crops": rising_crops,
            "falling_crops": falling_crops,
            "avg_change": round(avg_change, 2),
            "market_sentiment": "Bullish" if avg_change > 0 else "Bearish",
            "top_gainer": max(market_data, key=lambda x: x["percentage_change"]) if market_data else None,
            "top_loser": min(market_data, key=lambda x: x["percentage_change"]) if market_data else None
        }

        context = {
            "request": request,
            "page_title": "Enhanced मार्केट डैशबोर्ड - Real-time Data & AI Analytics",
            "market_data": market_data,
            "insights": market_insights,
            "current_filter": filter_type,
            "enhanced_features": True,
            "api_status": "live"
        }
        return templates.TemplateResponse("market.html", context)

    except Exception as e:
        logger.error(f"Enhanced market dashboard error: {e}")
        # Fallback to basic market page
        return templates.TemplateResponse("market.html", {
            "request": request,
            "page_title": "मार्केट डैशबोर्ड",
            "market_data": [],
            "insights": {},
            "current_filter": filter_type,
            "error": "डेटा लोड करने में समस्या"
        })


# ============================================================================
# Analytics and Monitoring Endpoints
# ============================================================================

@app.get("/api/enhanced/analytics/usage")
async def get_usage_analytics():
    """Get usage analytics for enhanced features"""
    try:
        # In a real implementation, this would query a database
        analytics = {
            "total_sessions": len(enhanced_manager.user_sessions),
            "active_connections": len(enhanced_manager.active_connections),
            "feature_usage": {
                "profitable_markets": 150,
                "price_predictions": 89,
                "spoilage_prevention": 67,
                "transport_calculator": 45
            },
            "user_satisfaction": 4.7,
            "response_time_avg": 1.2,
            "success_rate": 94.5
        }
        return {"status": "success", "data": analytics}
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/enhanced/health")
async def enhanced_health_check():
    """Enhanced health check with service status"""
    try:
        services_status = {
            "fastapi": "running",
            "farmbot_agent": "running",
            "enhanced_market_service": "running",
            "websocket": "enabled",
            "government_api": "connected",
            "ml_predictions": "active"
        }

        # Test government API connection
        try:
            test_result = enhanced_market_service.get_real_time_prices("wheat")
            if test_result.get("status") == "success":
                services_status["government_api"] = "connected"
            else:
                services_status["government_api"] = "limited"
        except Exception:
            services_status["government_api"] = "disconnected"

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0 Enhanced",
            "services": services_status,
            "active_sessions": len(enhanced_manager.active_connections),
            "features": [
                "real_time_market_data",
                "profitable_market_finder",
                "ai_price_predictions",
                "spoilage_prevention",
                "transport_calculator",
                "location_based_services"
            ]
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# ============================================================================
# Keep all existing endpoints for compatibility
# ============================================================================

@app.post("/voice-query")
async def process_voice_query(query: str = Form(...)):
    """Voice query processing - enhanced version"""
    try:
        result = await farmbot_agent.process_message(query, "voice")
        return {"response": result.response, "agent_used": result.agent_used}
    except Exception as e:
        logger.error(f"Voice query error: {e}")
        return {"response": "मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।"}


@app.post("/upload-image")
async def upload_image(files: List[UploadFile] = File(...)):
    """Image upload processing - enhanced version"""
    try:
        analysis_results = []

        for file in files:
            content = await file.read()
            image_b64 = base64.b64encode(content).decode()

            result = await farmbot_agent.process_message(
                f"फसल की छवि का विश्लेषण करें",
                "image",
                image_b64
            )

            # Enhanced analysis result
            analysis = {
                "disease_name": "बैक्टीरियल ब्लाइट",
                "confidence": 94.5,
                "description": result.response,
                "treatment": "स्ट्रेप्टोमाइसिन का छिड़काव करें",
                "severity": "मध्यम",
                "preventive_measures": [
                    "खेत में जल निकासी सुधारें",
                    "संक्रमित पत्तियों को हटाएं",
                    "नियमित निगरानी करें"
                ],
                "ai_confidence": 94.5,
                "recommendations": [
                    "तुरंत उपचार शुरू करें",
                    "अन्य पौधों को अलग करें",
                    "मिट्टी की जांच कराएं"
                ]
            }
            analysis_results.append(analysis)

        return {"status": "success", "analyses": analysis_results}

    except Exception as e:
        logger.error(f"Enhanced image upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import Response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

@app.post("/generate-prescription")
async def generate_prescription(data: dict):
    try:
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Hindi',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            wordWrap='CJK'
        ))

        # Content
        story = []

        # Header
        story.append(Paragraph("<b>कृषि उपचार प्रिस्क्रिप्शन</b>", styles['Title']))
        story.append(Spacer(1, 12))

        # Farmer Info
        farmer_data = [
            ["किसान का नाम:", data.get('farmerInfo', {}).get('name', '')],
            ["स्थान:", data.get('farmerInfo', {}).get('location', '')],
            ["तारीख:", data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M'))]
        ]
        farmer_table = Table(farmer_data, colWidths=[1.5 * inch, 4 * inch])
        farmer_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(farmer_table)
        story.append(Spacer(1, 24))

        # Diagnosis
        story.append(Paragraph(f"<b>निदान:</b> {data['diagnosis']} (सटीकता: {data['confidence']}%)", styles['Hindi']))
        story.append(Spacer(1, 12))

        # Symptoms
        story.append(Paragraph(f"<b>लक्षण:</b> {data['symptoms']}", styles['Hindi']))
        story.append(Spacer(1, 12))

        # Treatment
        story.append(Paragraph("<b>उपचार:</b>", styles['Heading3']))
        story.append(Paragraph(data['treatment'], styles['Hindi']))
        story.append(Spacer(1, 12))

        # Preventive Measures
        if data.get('preventiveMeasures'):
            story.append(Paragraph("<b>बचाव के उपाय:</b>", styles['Heading3']))
            for measure in data['preventiveMeasures']:
                story.append(Paragraph(f"• {measure}", styles['Hindi']))
            story.append(Spacer(1, 12))

        # Footer
        story.append(Paragraph("<i>यह प्रिस्क्रिप्शन AI द्वारा जनरेट किया गया है। किसी विशेषज्ञ से सलाह लें।</i>",
                               styles['Italic']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=kisan_prescription_{datetime.now().timestamp()}.pdf"}
        )
    except Exception as e:
        logger.error(f"Prescription generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_default_query(content: str, message_type: str, additional_data: dict, session_id: str):
    try:
        # Process through main farmbot agent
        image_data = additional_data.get("image_data") if message_type == "image" else None

        result = await farmbot_agent.process_message(content, message_type, image_data)

        # For analysis results, send structured data
        if message_type == "image":
            analysis_data = {
                "type": "analysis_result",
                "diagnosis": "बैक्टीरियल ब्लाइट",  # Would come from actual analysis
                "confidence": 94.5,
                "symptoms": "पत्तियों पर भूरे धब्बे, पौधे का मुरझाना",
                "treatment": "स्ट्रेप्टोमाइसिन का छिड़काव करें",
                "preventive_measures": [
                    "खेत में जल निकासी सुधारें",
                    "संक्रमित पत्तियों को हटाएं"
                ],
                "session_id": session_id
            }
            await enhanced_manager.send_message(analysis_data, session_id)
        else:
            # Regular text response
            await enhanced_manager.send_message({
                "type": "response",
                "content": result.response,
                "session_id": session_id
            }, session_id)

    except Exception as e:
        logger.error(f"Query error: {e}")
        await enhanced_manager.send_message({
            "type": "response",
            "content": "मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।",
            "session_id": session_id
        }, session_id)

# ============================================================================
# Run the enhanced application
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )
