# ============================================================================
# tools/general_tools.py
# ============================================================================
import json
from  typing import Dict,Any
from google.adk.tools.tool_context import ToolContext

def get_general_farming_advice(
        query: str,
        user_context: Dict[str, Any] = None,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Provide general farming advice using Gemini's knowledge.

    Args:
        query (str): User's farming question
        user_context (Dict): User context (location, crops, etc.)
        tool_context (ToolContext): Session context

    Returns:
        Dict: General farming advice response
    """
    logger.info(f"Providing general advice for: {query[:100]}...")

    try:
        # Extract user context
        context_info = ""
        if user_context:
            location = user_context.get("location", "")
            crops = user_context.get("crops", [])
            farming_type = user_context.get("farming_type", "")

            context_parts = []
            if location:
                context_parts.append(f"Location: {location}")
            if crops:
                context_parts.append(f"Crops: {', '.join(crops)}")
            if farming_type:
                context_parts.append(f"Farming type: {farming_type}")

            context_info = " | ".join(context_parts)

        # Get additional context from session state
        if tool_context:
            state = tool_context.state
            if state.get("user_crops"):
                context_info += f" | Known crops: {', '.join(state['user_crops'])}"
            if state.get("farmer_state"):
                context_info += f" | State: {state['farmer_state']}"

        # In production, this would call Gemini API with agricultural context
        # For now, provide structured response with agricultural expertise

        # Categorize the query
        query_lower = query.lower()
        response_category = "general"

        if any(word in query_lower for word in ["soil", "fertilizer", "nutrition", "nutrient"]):
            response_category = "soil_nutrition"
        elif any(word in query_lower for word in ["pest", "insect", "disease", "fungus"]):
            response_category = "pest_disease"
        elif any(word in query_lower for word in ["irrigation", "water", "drought"]):
            response_category = "irrigation"
        elif any(word in query_lower for word in ["seed", "variety", "planting", "sowing"]):
            response_category = "seeds_planting"
        elif any(word in query_lower for word in ["harvest", "storage", "post-harvest"]):
            response_category = "harvest_storage"
        elif any(word in query_lower for word in ["organic", "natural", "bio"]):
            response_category = "organic_farming"

        # Generate response based on category
        response_data = generate_expert_response(query, response_category, context_info)

        # Update session state
        if tool_context:
            tool_context.state["last_general_query"] = {
                "query": query[:100],
                "category": response_category,
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

        return {
            "status": "success",
            "query": query,
            "category": response_category,
            "context": context_info,
            "response": response_data["response"],
            "expert_tips": response_data.get("tips", []),
            "related_topics": response_data.get("related", []),
            "confidence": "high",
            "source": "agricultural_knowledge_base"
        }

    except Exception as e:
        logger.error(f"Error in general farming advice: {e}")
        return {
            "status": "error",
            "message": "Unable to provide advice at the moment. Please try again."
        }


def generate_expert_response(query: str, category: str, context: str) -> Dict[str, Any]:
    """Generate expert agricultural response based on category"""

    expert_responses = {
        "soil_nutrition": {
            "response": f"Based on your query about soil and nutrition: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Soil health is fundamental to successful farming. Here are key recommendations:\n"
                        "• Regular soil testing (pH, NPK, organic matter) every 2-3 years\n"
                        "• Maintain soil pH between 6.0-7.5 for most crops\n"
                        "• Add organic matter through compost, FYM, or green manure\n"
                        "• Follow balanced fertilization based on soil test results\n"
                        "• Practice crop rotation to maintain soil fertility\n"
                        "• Use bio-fertilizers like Rhizobium, Azotobacter for natural nutrition",
            "tips": [
                "Apply organic matter before monsoon for better decomposition",
                "Use soil amendments like lime for acidic soils, gypsum for alkaline soils",
                "Monitor soil moisture regularly - neither too dry nor waterlogged"
            ],
            "related": ["crop rotation", "composting", "soil testing", "organic farming"]
        },

        "pest_disease": {
            "response": f"Regarding pest and disease management for your query: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Integrated Pest Management (IPM) is the most effective approach:\n"
                        "• Early detection through regular field monitoring\n"
                        "• Use resistant varieties when available\n"
                        "• Encourage beneficial insects through biodiversity\n"
                        "• Cultural practices: proper spacing, sanitation, crop rotation\n"
                        "• Biological control using natural predators and parasites\n"
                        "• Chemical control as last resort, following recommended doses",
            "tips": [
                "Scout fields weekly for early pest detection",
                "Use pheromone traps for monitoring and mass trapping",
                "Apply pesticides during cooler parts of the day"
            ],
            "related": ["beneficial insects", "organic pesticides", "crop rotation", "resistant varieties"]
        },

        "irrigation": {
            "response": f"For irrigation and water management regarding: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Efficient water management is crucial for sustainable farming:\n"
                        "• Drip irrigation saves 30-50% water compared to flood irrigation\n"
                        "• Schedule irrigation based on crop stage and soil moisture\n"
                        "• Mulching reduces water evaporation by 20-30%\n"
                        "• Rainwater harvesting for water conservation\n"
                        "• Use soil moisture sensors for precision irrigation\n"
                        "• Different crops have different water requirements at various stages",
            "tips": [
                "Water early morning or evening to reduce evaporation",
                "Check soil moisture at root zone depth before irrigating",
                "Use organic mulch to retain soil moisture"
            ],
            "related": ["drip irrigation", "mulching", "rainwater harvesting", "soil moisture"]
        },

        "seeds_planting": {
            "response": f"Regarding seeds and planting for your query: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Quality seeds and proper planting are foundation of good yields:\n"
                        "• Use certified seeds from reliable sources\n"
                        "• Treat seeds with fungicide before planting\n"
                        "• Follow recommended planting dates for your region\n"
                        "• Maintain proper seed depth and spacing\n"
                        "• Consider local climate and soil conditions\n"
                        "• Keep some traditional varieties for genetic diversity",
            "tips": [
                "Test seed germination percentage before large-scale planting",
                "Store seeds in cool, dry conditions",
                "Inoculate legume seeds with appropriate rhizobia"
            ],
            "related": ["seed treatment", "planting calendar", "spacing", "varieties"]
        },

        "harvest_storage": {
            "response": f"For harvesting and storage regarding: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Proper harvesting and storage prevent post-harvest losses:\n"
                        "• Harvest at optimum maturity for maximum quality\n"
                        "• Handle produce carefully to avoid physical damage\n"
                        "• Dry grains to safe moisture levels (12-14% for most cereals)\n"
                        "• Use proper storage structures and containers\n"
                        "• Control storage pests using integrated methods\n"
                        "• Regular monitoring of stored produce",
            "tips": [
                "Harvest during cool, dry weather when possible",
                "Clean storage areas thoroughly before storing new harvest",
                "Use hermetic storage for long-term grain storage"
            ],
            "related": ["drying", "storage pests", "moisture content", "post-harvest losses"]
        },

        "organic_farming": {
            "response": f"Regarding organic farming practices for: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Organic farming focuses on natural and sustainable methods:\n"
                        "• Build soil health through organic matter and compost\n"
                        "• Use bio-fertilizers and organic nutrients\n"
                        "• Implement biological pest control methods\n"
                        "• Practice crop rotation and intercropping\n"
                        "• Maintain biodiversity on the farm\n"
                        "• Avoid synthetic chemicals and GMOs",
            "tips": [
                "Start transition gradually - convert one field at a time",
                "Get organic certification if planning to sell as organic",
                "Keep detailed records of all inputs and practices"
            ],
            "related": ["composting", "bio-fertilizers", "biological control", "certification"]
        },

        "general": {
            "response": f"Regarding your farming query: {query}\n\n"
                        f"Context: {context}\n\n"
                        "Here's general agricultural guidance:\n"
                        "• Follow scientific farming practices based on local conditions\n"
                        "• Regular monitoring and timely interventions are crucial\n"
                        "• Consult local agricultural extension officers for region-specific advice\n"
                        "• Keep learning about new technologies and methods\n"
                        "• Maintain farm records for better decision making\n"
                        "• Focus on sustainable practices for long-term success",
            "tips": [
                "Join local farmer groups for knowledge sharing",
                "Attend agricultural training programs and demonstrations",
                "Use technology like weather apps and soil testing"
            ],
            "related": ["extension services", "farmer training", "agricultural technology", "record keeping"]
        }
    }

    return expert_responses.get(category, expert_responses["general"])