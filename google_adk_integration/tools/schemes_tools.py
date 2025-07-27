# ============================================================================
# tools/schemes_tools.py
# ============================================================================
from ..services.schemes_service import SchemesService
from google.adk.tools.tool_context import ToolContext
from  typing import Dict,Any
schemes_service = SchemesService()


def find_government_schemes(
        state: str,
        category: str = "all",
        farmer_type: str = "all",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Find relevant government schemes for farmers.

    Args:
        state (str): State or region of the farmer
        category (str): Category of scheme (insurance, subsidy, credit, etc.)
        farmer_type (str): Type of farmer (small, marginal, all)
        tool_context (ToolContext): Session context

    Returns:
        Dict: List of applicable government schemes
    """
    # logger.info(f"Finding schemes for {farmer_type} farmers in {state}, category: {category}")

    try:
        # Validate state
        is_valid, error_msg = validate_location(state)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        # Get schemes from service
        schemes_data = schemes_service.get_schemes(state, category, farmer_type)

        # Update session state
        if tool_context and schemes_data.get("status") == "success":
            tool_context.state["last_schemes_search"] = {
                "state": state,
                "category": category,
                "farmer_type": farmer_type,
                "schemes_found": schemes_data.get("total_schemes", 0),
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

            # Update user's state preference
            tool_context.state["farmer_state"] = state
            if farmer_type != "all":
                tool_context.state["farmer_type"] = farmer_type

        return schemes_data

    except Exception as e:
        # logger.error(f"Error finding government schemes: {e}")
        return {
            "status": "error",
            "message": "Unable to fetch government schemes information at the moment"
        }


def get_scheme_details(
        scheme_name: str,
        state: str = None,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific government scheme.

    Args:
        scheme_name (str): Name of the scheme
        state (str, optional): State for state-specific schemes
        tool_context (ToolContext): Session context

    Returns:
        Dict: Detailed scheme information
    """
    # logger.info(f"Getting details for scheme: {scheme_name}")

    try:
        if not scheme_name or len(scheme_name.strip()) < 3:
            return {"status": "error", "message": "Please provide a valid scheme name"}

        # Get scheme details
        scheme_details = schemes_service.get_scheme_details(scheme_name, state)

        # Update session state
        if tool_context and scheme_details.get("status") == "success":
            tool_context.state["last_scheme_viewed"] = {
                "scheme_name": scheme_name,
                "state": state,
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

        return scheme_details

    except Exception as e:
        # logger.error(f"Error getting scheme details: {e}")
        return {
            "status": "error",
            "message": "Unable to fetch scheme details at the moment"
        }
