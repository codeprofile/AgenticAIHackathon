# ============================================================================
# app/google_adk_integration/tools/crop_tools.py
# ============================================================================
from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext
from ..services.disease_service import DiseaseService
from ..utils.helpers import get_logger
from ..utils.validators import validate_crop_name

logger = get_logger(__name__)
disease_service = DiseaseService()


def diagnose_crop_disease(
        crop_type: str,
        symptoms: str,
        location: str = None,
        growth_stage: str = None,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Diagnose crop disease based on symptoms and provide treatment recommendations.

    Args:
        crop_type (str): Type of crop (e.g., wheat, rice, tomato)
        symptoms (str): Detailed description of observed symptoms
        location (str, optional): Location/region where crop is grown
        growth_stage (str, optional): Current growth stage of the crop
        tool_context (ToolContext): Session context for state management

    Returns:
        Dict: Disease diagnosis with treatment and prevention recommendations
    """
    logger.info(f"Diagnosing disease for {crop_type} with symptoms: {symptoms[:100]}...")

    try:
        # Validate inputs
        is_valid, error_msg = validate_crop_name(crop_type)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        if not symptoms or len(symptoms.strip()) < 10:
            return {
                "status": "error",
                "message": "कृपया विस्तार से लक्षण बताएं (कम से कम 10 अक्षर)"
            }

        # Get diagnosis from service
        diagnosis = disease_service.diagnose_disease(crop_type, symptoms, location)

        # Update session state with diagnosis
        if tool_context and diagnosis.get("status") == "success":
            tool_context.state["last_disease_diagnosis"] = {
                "crop": crop_type,
                "disease": diagnosis["primary_diagnosis"]["disease"],
                "confidence": diagnosis["primary_diagnosis"]["confidence"],
                "location": location,
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

            # Track user's crop interests
            user_crops = tool_context.state.get("user_crops", [])
            if crop_type not in user_crops:
                user_crops.append(crop_type)
                tool_context.state["user_crops"] = user_crops[:5]  # Keep last 5 crops

        return diagnosis

    except Exception as e:
        logger.error(f"Error in crop disease diagnosis: {e}")
        return {
            "status": "error",
            "message": "रोग निदान में समस्या हुई। कृपया स्थानीय कृषि विशेषज्ञ से संपर्क करें।"
        }


def get_crop_care_advice(
        crop_type: str,
        growth_stage: str = "general",
        season: str = "current",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get general crop care advice based on crop type and growth stage.

    Args:
        crop_type (str): Type of crop
        growth_stage (str): Current growth stage
        season (str): Season or time of year
        tool_context (ToolContext): Session context

    Returns:
        Dict: Crop care recommendations
    """
    logger.info(f"Getting care advice for {crop_type} at {growth_stage} stage")

    try:
        # Validate crop
        is_valid, error_msg = validate_crop_name(crop_type)
        if not is_valid:
            return {"status": "error", "message": error_msg}

        # Care advice database (simplified)
        care_advice = {
            "wheat": {
                "sowing": {
                    "irrigation": "बुआई के बाद हल्की सिंचाई, जलभराव से बचें",
                    "fertilizer": "DAP और यूरिया का बेसल डोज डालें",
                    "pest_management": "बीज को फफूंदनाशक से उपचारित करें",
                    "general": "3-4 सेमी की उचित गहराई सुनिश्चित करें"
                },
                "vegetative": {
                    "irrigation": "15-20 दिन के अंतराल पर नियमित सिंचाई",
                    "fertilizer": "पहली सिंचाई के बाद यूरिया का टॉप ड्रेसिंग",
                    "pest_management": "माहू और रतुआ रोग की निगरानी करें",
                    "general": "इस अवस्था में खरपतवार नियंत्रण महत्वपूर्ण है"
                },
                "flowering": {
                    "irrigation": "महत्वपूर्ण सिंचाई अवधि - पर्याप्त पानी सुनिश्चित करें",
                    "fertilizer": "नाइट्रोजन की अधिकता से बचें, पोटाश पर ध्यान दें",
                    "pest_management": "दाना भरने की अवस्था में कीटों की निगरानी करें",
                    "general": "दाना बनने के दौरान किसी भी तनाव से बचें"
                }
            },
            "rice": {
                "sowing": {
                    "irrigation": "नर्सरी में 2-3 सेमी पानी का स्तर बनाए रखें",
                    "fertilizer": "पूरा फास्फोरस और पोटाश, 1/3 नाइट्रोजन दें",
                    "pest_management": "बीज उपचार करें और तना छेदक को नियंत्रित करें",
                    "general": "21-25 दिन पुराने पौधों की रोपाई करें"
                },
                "vegetative": {
                    "irrigation": "5 सेमी पानी का स्तर बनाए रखें, कल्ले निकलने के दौरान पानी निकालें",
                    "fertilizer": "नाइट्रोजन को 2-3 भागों में दें",
                    "pest_management": "भूरा फुदका और पत्ती लपेटक की निगरानी करें",
                    "general": "यांत्रिक या रासायनिक विधि से खरपतवार नियंत्रण"
                }
            },
            "tomato": {
                "seedling": {
                    "irrigation": "हल्की बार-बार सिंचाई, जलभराव से बचें",
                    "fertilizer": "फास्फोरस पर जोर देने के साथ संतुलित NPK",
                    "pest_management": "डैम्पिंग ऑफ और माहू से बचाव",
                    "general": "स्वस्थ वृद्धि के लिए 18-25°C तापमान बनाए रखें"
                },
                "flowering": {
                    "irrigation": "नियमित सिंचाई, पानी के तनाव से बचें",
                    "fertilizer": "नाइट्रोजन कम करें, पोटाश और कैल्शियम बढ़ाएं",
                    "pest_management": "सफेद मक्खी और थ्रिप्स की निगरानी करें",
                    "general": "स्टेकिंग या केजिंग से पौधों को सहारा दें"
                }
            }
        }

        crop_advice = care_advice.get(crop_type.lower(), {})
        stage_advice = crop_advice.get(growth_stage.lower(), crop_advice.get("general", {}))

        if not stage_advice:
            return {
                "status": "limited_data",
                "message": f"{crop_type} की {growth_stage} अवस्था के लिए सीमित जानकारी उपलब्ध है",
                "general_advice": "उचित सिंचाई, संतुलित उर्वरीकरण और कीट-रोगों की नियमित निगरानी सुनिश्चित करें"
            }

        # Update user preferences
        if tool_context:
            tool_context.state["last_crop_advice"] = {
                "crop": crop_type,
                "stage": growth_stage,
                "timestamp": tool_context.state.get("timestamp", "unknown")
            }

        return {
            "status": "success",
            "crop": crop_type,
            "growth_stage": growth_stage,
            "season": season,
            "care_recommendations": stage_advice,
            "general_tips": f"{crop_type} की खेती में नियमित निगरानी और समय पर हस्तक्षेप सफलता की कुंजी है"
        }

    except Exception as e:
        logger.error(f"Error getting crop care advice: {e}")
        return {
            "status": "error",
            "message": "फसल देखभाल की सलाह प्राप्त करने में समस्या"
        }