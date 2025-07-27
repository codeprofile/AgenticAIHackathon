# ============================================================================
# app/google_adk_integration/services/disease_service.py
# ============================================================================
from typing import Dict, Any, List, Optional, Tuple
import json
import re
from ..utils.helpers import get_logger, load_json_data, normalize_crop_name

logger = get_logger(__name__)


class DiseaseService:
    """Crop disease diagnosis service"""

    def __init__(self):
        self.disease_database = self._load_disease_database()
        self.symptom_patterns = self._build_symptom_patterns()

    def _load_disease_database(self) -> Dict[str, Any]:
        """Load disease database from JSON file"""
        return load_json_data("google_adk_integration/data/diseases_db.json") or self._get_default_disease_data()

    def _build_symptom_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for symptom matching"""
        return {
            "leaf_yellowing": [r"पीले?\s*पत्ते?", r"yellowing", r"chlorosis", r"पीलाहट"],
            "leaf_spots": [r"धब्बे?", r"spots?", r"lesions?", r"patches", r"blotches?", r"दाग"],
            "wilting": [r"मुरझा", r"wilt(ing)?", r"drooping", r"sagging", r"सूख"],
            "stunted_growth": [r"बौना", r"stunted", r"dwarf", r"छोटा", r"slow.{0,10}growth"],
            "root_rot": [r"जड़.{0,10}सड़न", r"root.{0,10}rot", r"black.{0,10}roots?"],
            "powdery_coating": [r"सफेद.{0,10}पाउडर", r"powder", r"white.{0,10}coating"],
            "brown_patches": [r"भूरे?.{0,10}धब्बे?", r"brown.{0,10}patches", r"blight"],
            "holes": [r"छेद", r"holes?", r"eaten", r"chewed"],
            "curling": [r"मुड़", r"curl(ing)?", r"twisted", r"deformed"]
        }

    def diagnose_disease(self, crop_type: str, symptoms: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Diagnose crop disease based on symptoms"""
        try:
            crop_normalized = normalize_crop_name(crop_type)

            if crop_normalized not in self.disease_database:
                return {
                    "status": "crop_not_supported",
                    "message": f"{crop_type} के लिए रोग डेटाबेस उपलब्ध नहीं है",
                    "supported_crops": list(self.disease_database.keys())
                }

            # Extract symptoms from description
            detected_symptoms = self._extract_symptoms(symptoms)

            if not detected_symptoms:
                return {
                    "status": "insufficient_symptoms",
                    "message": "विवरण से स्पष्ट लक्षण पहचाने नहीं जा सके",
                    "suggestion": "कृपया विशिष्ट लक्षण बताएं जैसे पत्तियों का रंग, धब्बे, मुरझाना आदि"
                }

            # Find matching diseases
            possible_diseases = self._match_diseases(crop_normalized, detected_symptoms, location)

            if not possible_diseases:
                return {
                    "status": "no_match",
                    "message": f"{crop_type} में इन लक्षणों के लिए कोई मेल खाने वाला रोग नहीं मिला",
                    "general_advice": "फसल की बारीकी से निगरानी करें और स्थानीय कृषि विशेषज्ञ से सलाह लें",
                    "detected_symptoms": detected_symptoms
                }

            # Return the most likely disease
            primary_disease = possible_diseases[0]

            return {
                "status": "success",
                "crop": crop_type,
                "detected_symptoms": detected_symptoms,
                "primary_diagnosis": {
                    "disease": primary_disease["name"],
                    "confidence": primary_disease["confidence"],
                    "description": primary_disease["description"],
                    "treatment": primary_disease["treatment"],
                    "prevention": primary_disease["prevention"],
                    "severity": primary_disease.get("severity", "moderate")
                },
                "alternative_diagnoses": possible_diseases[1:3] if len(possible_diseases) > 1 else [],
                "immediate_actions": self._get_immediate_actions(primary_disease),
                "when_to_consult_expert": self._should_consult_expert(primary_disease)
            }

        except Exception as e:
            logger.error(f"Error in disease diagnosis: {e}")
            return {
                "status": "error",
                "message": "रोग निदान प्रक्रिया में समस्या हुई",
                "suggestion": "कृपया दोबारा कोशिश करें या स्थानीय कृषि विशेषज्ञ से संपर्क करें"
            }

    def _extract_symptoms(self, description: str) -> List[str]:
        """Extract symptoms from description using pattern matching"""
        description_lower = description.lower()
        detected = []

        for symptom_type, patterns in self.symptom_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    detected.append(symptom_type)
                    break

        return detected

    def _match_diseases(self, crop: str, symptoms: List[str], location: Optional[str]) -> List[Dict[str, Any]]:
        """Match symptoms to possible diseases"""
        crop_diseases = self.disease_database.get(crop, {})
        matches = []

        for disease_name, disease_info in crop_diseases.items():
            disease_symptoms = disease_info.get("symptoms", [])

            # Calculate symptom match score
            matching_symptoms = set(symptoms) & set(disease_symptoms)
            if not matching_symptoms:
                continue

            confidence = len(matching_symptoms) / len(disease_symptoms)

            # Adjust confidence based on location (some diseases are region-specific)
            if location:
                location_factor = self._get_location_factor(disease_info, location)
                confidence *= location_factor

            matches.append({
                "name": disease_name,
                "confidence": min(confidence, 1.0),
                "matching_symptoms": list(matching_symptoms),
                **disease_info
            })

        # Sort by confidence
        return sorted(matches, key=lambda x: x["confidence"], reverse=True)

    def _get_location_factor(self, disease_info: Dict, location: str) -> float:
        """Get location-based confidence factor"""
        common_regions = disease_info.get("common_regions", [])
        if not common_regions:
            return 1.0

        location_normalized = location.lower()
        for region in common_regions:
            if region.lower() in location_normalized:
                return 1.2  # Boost confidence for region-specific diseases

        return 0.8  # Slightly reduce confidence for diseases uncommon in region

    def _get_immediate_actions(self, disease: Dict) -> List[str]:
        """Get immediate actions for the disease"""
        severity = disease.get("severity", "moderate")

        immediate_actions = [
            "प्रभावित पौधों को अलग करें ताकि फैलाव रुके",
            "गंभीर प्रभावित पत्तियों को हटाकर जला दें"
        ]

        if severity == "high":
            immediate_actions.insert(0, "⚠️ तुरंत कार्रवाई: यह गंभीर रोग है - तत्काल उपचार करें")

        # Add disease-specific immediate actions
        if "immediate_actions" in disease:
            immediate_actions.extend(disease["immediate_actions"])

        return immediate_actions

    def _should_consult_expert(self, disease: Dict) -> str:
        """Determine when to consult expert"""
        severity = disease.get("severity", "moderate")

        if severity == "high":
            return "तुरंत कृषि विशेषज्ञ से संपर्क करें - यह रोग गंभीर नुकसान पहुंचा सकता है"
        elif severity == "moderate":
            return "यदि लक्षण बिगड़ते हैं या 7-10 दिन में सुधार न दिखे तो विशेषज्ञ से मिलें"
        else:
            return "यदि उपचार के बारे में संदेह हो या लक्षण बने रहें तो विशेषज्ञ से सलाह लें"

    def _get_default_disease_data(self) -> Dict[str, Any]:
        """Default disease database in Hindi"""
        return {
            "wheat": {
                "गेहूं का रतुआ": {
                    "description": "पत्तियों पर नारंगी-लाल पुस्ट्यूल्स बनने वाला फंगल रोग",
                    "symptoms": ["leaf_spots", "leaf_yellowing", "brown_patches"],
                    "treatment": "प्रोपिकोनाजोल या टेबुकोनाजोल युक्त फफूंदनाशक का छिड़काव करें। संक्रमण की शुरुआती अवस्था में छिड़काव करें।",
                    "prevention": "प्रतिरोधी किस्मों का प्रयोग, उचित फसल चक्र, ऊपरी सिंचाई से बचें",
                    "severity": "high",
                    "common_regions": ["punjab", "haryana", "uttar_pradesh"],
                    "immediate_actions": ["ऊपरी सिंचाई बंद करें", "तुरंत फफूंदनाशक का छिड़काव करें"]
                },
                "पत्ती धब्बा रोग": {
                    "description": "पीले हाले के साथ भूरे धब्बे बनने वाला फंगल रोग",
                    "symptoms": ["brown_patches", "leaf_spots", "leaf_yellowing"],
                    "treatment": "मैंकोजेब या क्लोरोथैलोनिल फफूंदनाशक का छिड़काव करें। आवश्यकता पड़ने पर 15 दिन बाद दोहराएं।",
                    "prevention": "हवा का संचार सुधारें, गीली पत्तियों से बचें, संतुलित उर्वरीकरण",
                    "severity": "moderate",
                    "common_regions": ["all"]
                }
            },
            "rice": {
                "धान का ब्लास्ट": {
                    "description": "ग्रे सेंटर के साथ हीरे के आकार के घाव बनने वाला फंगल रोग",
                    "symptoms": ["leaf_spots", "brown_patches", "stunted_growth"],
                    "treatment": "ट्राइसाइक्लाजोल या आइसोप्रोथायोलेन फफूंदनाशक का प्रयोग करें। सुझावित मात्रा का उपयोग करें।",
                    "prevention": "संतुलित उर्वरीकरण, अधिक नाइट्रोजन से बचें, प्रतिरोधी किस्मों का प्रयोग",
                    "severity": "high",
                    "common_regions": ["all"],
                    "immediate_actions": ["नाइट्रोजन उर्वरक कम करें", "खेत की जल निकासी सुधारें"]
                },
                "बैक्टीरियल ब्लाइट": {
                    "description": "पत्तियों पर पीली धारियां और मुरझाने वाला बैक्टीरियल रोग",
                    "symptoms": ["wilting", "leaf_yellowing", "stunted_growth"],
                    "treatment": "कॉपर आधारित बैक्टीरियासाइड का प्रयोग करें, संक्रमित पौधों को हटाएं",
                    "prevention": "प्रमाणित बीज का प्रयोग, खेत की स्वच्छता बनाए रखें, पौधों को चोट से बचाएं",
                    "severity": "high",
                    "common_regions": ["all"]
                }
            },
            "tomato": {
                "अर्ली ब्लाइट": {
                    "description": "संकेंद्रित वलयों के साथ गहरे धब्बे बनने वाला फंगल रोग",
                    "symptoms": ["brown_patches", "leaf_spots", "leaf_yellowing"],
                    "treatment": "क्लोरोथैलोनिल या मैंकोजेब फफूंदनाशक का छिड़काव करें। हवा का संचार सुधारें।",
                    "prevention": "मल्चिंग, ड्रिप सिंचाई, फसल चक्र, प्रतिरोधी किस्में",
                    "severity": "moderate",
                    "common_regions": ["all"]
                },
                "फ्यूजेरियम विल्ट": {
                    "description": "मिट्टी जनित फंगल रोग जो पीलाहट और मुरझाने का कारण बनता है",
                    "symptoms": ["wilting", "leaf_yellowing", "stunted_growth"],
                    "treatment": "कोई इलाज नहीं - संक्रमित पौधों को हटाएं, मिट्टी सोलराइजेशन, प्रतिरोधी किस्मों का प्रयोग",
                    "prevention": "मिट्टी की जल निकासी, फसल चक्र, प्रतिरोधी किस्में, जड़ों को नुकसान से बचाएं",
                    "severity": "high"
                }
            }
        }
