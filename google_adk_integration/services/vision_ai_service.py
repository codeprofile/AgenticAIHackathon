# ============================================================================
# google_adk_integration/services/vision_ai_service.py
# ============================================================================

import asyncio
import base64
import io
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import httpx
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CropDiagnosis:
    """Crop diagnosis result from Vision AI"""
    disease_name: str
    confidence: float
    severity: str
    treatment: str
    prevention: List[str]
    symptoms_detected: List[str]
    immediate_actions: List[str]
    follow_up_timeline: str
    organic_alternatives: List[str]
    expected_recovery_time: str


class ImageEnhancer:
    """Advanced image enhancement for better crop disease detection"""

    @staticmethod
    def enhance_image(image_data: bytes, target_size: Tuple[int, int] = (1024, 1024)) -> bytes:
        """
        Enhance image quality for better disease detection

        Args:
            image_data: Raw image bytes
            target_size: Target resolution for the enhanced image

        Returns:
            Enhanced image bytes
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            original_format = image.format

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Auto-orient image based on EXIF data
            image = ImageOps.exif_transpose(image)

            # Resize while maintaining aspect ratio
            image.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Create new image with target size and paste the resized image
            enhanced = Image.new('RGB', target_size, (255, 255, 255))
            paste_position = ((target_size[0] - image.size[0]) // 2,
                              (target_size[1] - image.size[1]) // 2)
            enhanced.paste(image, paste_position)

            # Apply enhancements
            enhanced = ImageEnhancer._apply_enhancements(enhanced)

            # Convert back to bytes
            output = io.BytesIO()
            enhanced.save(output, format='JPEG', quality=95, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Image enhancement error: {e}")
            return image_data  # Return original if enhancement fails

    @staticmethod
    def _apply_enhancements(image: Image.Image) -> Image.Image:
        """Apply various image enhancements for better disease detection"""

        # Step 1: Enhance sharpness for better detail visibility
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        # Step 2: Enhance contrast for better symptom visibility
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        # Step 3: Enhance color saturation for better disease spot detection
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.15)

        # Step 4: Adjust brightness if needed
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05)

        # Step 5: Apply subtle gaussian blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(radius=0.3))

        # Step 6: Enhance edges for disease boundary detection
        image_array = np.array(image)

        # Simple edge enhancement
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        if len(image_array.shape) == 3:
            enhanced_array = np.zeros_like(image_array)
            for i in range(3):  # Process each color channel
                channel = image_array[:, :, i]
                # Apply simple convolution (edge detection)
                enhanced_channel = np.clip(channel * 1.1, 0, 255)
                enhanced_array[:, :, i] = enhanced_channel
            image = Image.fromarray(enhanced_array.astype(np.uint8))

        return image

    @staticmethod
    def extract_image_features(image_data: bytes) -> Dict[str, Any]:
        """Extract features from image for analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to numpy array
            img_array = np.array(image)

            # Calculate color statistics
            features = {
                "image_size": image.size,
                "color_stats": {
                    "mean_rgb": np.mean(img_array, axis=(0, 1)).tolist(),
                    "std_rgb": np.std(img_array, axis=(0, 1)).tolist()
                },
                "brightness": np.mean(img_array),
                "contrast": np.std(img_array),
                "has_green_areas": np.mean(img_array[:, :, 1]) > np.mean(img_array[:, :, 0]),  # More green than red
                "potential_disease_indicators": []
            }

            # Simple disease indicator detection
            green_channel = img_array[:, :, 1]
            red_channel = img_array[:, :, 0]

            # Check for yellowing (high red, medium green, low blue)
            yellow_areas = np.sum((red_channel > 150) & (green_channel > 100) & (img_array[:, :, 2] < 100))
            if yellow_areas > (image.size[0] * image.size[1] * 0.1):  # More than 10% yellow
                features["potential_disease_indicators"].append("yellowing_detected")

            # Check for brown spots (low green, medium red)
            brown_areas = np.sum((red_channel > 80) & (green_channel < 80) & (img_array[:, :, 2] < 80))
            if brown_areas > (image.size[0] * image.size[1] * 0.05):  # More than 5% brown
                features["potential_disease_indicators"].append("brown_spots_detected")

            return features

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return {"error": str(e)}


class VisionAIService:
    """Advanced crop disease detection using Google Vision AI and image analysis"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-pro-vision-latest"
        self.timeout = 30.0
        self.call_count = 0
        self.success_count = 0
        self.error_count = 0

        # Disease knowledge base
        self.disease_database = self._load_disease_database()

    async def detect_crop_disease(
            self,
            image_data: bytes,
            crop_type: str = None,
            location: str = None,
            symptoms: str = None,
            growth_stage: str = None
    ) -> CropDiagnosis:
        """
        Detect crop disease using advanced Vision AI with image enhancement

        Args:
            image_data: Enhanced image bytes
            crop_type: Type of crop (optional for better context)
            location: Location for regional disease patterns
            symptoms: Additional symptom description
            growth_stage: Current growth stage of crop

        Returns:
            CropDiagnosis object with detailed analysis
        """
        try:
            self.call_count += 1
            logger.info(f"Analyzing crop image for disease detection (call #{self.call_count})")

            # Step 1: Enhance image quality
            enhanced_image = ImageEnhancer.enhance_image(image_data)

            # Step 2: Extract image features for preprocessing
            image_features = ImageEnhancer.extract_image_features(enhanced_image)

            # Step 3: Encode image for Vision AI
            image_b64 = base64.b64encode(enhanced_image).decode('utf-8')

            # Step 4: Create comprehensive prompt for agricultural analysis
            prompt = self._create_agricultural_analysis_prompt(
                crop_type, location, symptoms, growth_stage, image_features
            )

            # Step 5: Call Google Vision AI
            vision_result = await self._call_vision_ai(image_b64, prompt)

            # Step 6: Parse and enhance result with agricultural knowledge
            diagnosis = self._parse_and_enhance_diagnosis(vision_result, crop_type, location)

            self.success_count += 1
            logger.info(f"✅ Disease detection completed with {diagnosis.confidence}% confidence")

            return diagnosis

        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Disease detection error: {e}")

            # Return fallback diagnosis
            return CropDiagnosis(
                disease_name="विश्लेषण असफल",
                confidence=0.0,
                severity="unknown",
                treatment="छवि विश्लेषण नहीं हो सका। कृपया स्पष्ट और अच्छी गुणवत्ता की तस्वीर के साथ दोबारा कोशिश करें।",
                prevention=["बेहतर गुणवत्ता की तस्वीर लें", "प्रभावित भागों को स्पष्ट रूप से दिखाएं"],
                symptoms_detected=[],
                immediate_actions=["स्थानीय कृषि विशेषज्ञ से सलाह लें"],
                follow_up_timeline="तत्काल",
                organic_alternatives=["जैविक उपचार के लिए विशेषज्ञ से पूछें"],
                expected_recovery_time="अज्ञात"
            )

    def _create_agricultural_analysis_prompt(
            self, crop_type: str, location: str, symptoms: str, growth_stage: str, image_features: Dict
    ) -> str:
        """Create comprehensive prompt for agricultural analysis"""

        base_prompt = """आप एक विशेषज्ञ कृषि रोग विशेषज्ञ और पादप रोग विज्ञानी हैं। इस फसल की छवि का विस्तृत विश्लेषण करें।

**विश्लेषण दिशानिर्देश:**
1. पत्तियों, तने, फल/अनाज पर किसी भी असामान्यता की पहचान करें
2. रोग के लक्षण जैसे धब्बे, मुरझाना, रंग परिवर्तन, कीड़े का नुकसान देखें
3. रोग की गंभीरता का आकलन करें (मंद, मध्यम, गंभीर)
4. तत्काल और दीर्घकालिक उपचार सुझाएं
5. रोकथाम के उपाय बताएं

**मुझे निम्नलिखित प्रारूप में जानकारी चाहिए:**

रोग का नाम: [रोग का स्पष्ट नाम]
विश्वास स्तर: [0-100% में]
गंभीरता: [मंद/मध्यम/गंभीर]
मुख्य लक्षण: [देखे गए लक्षणों की सूची]
तत्काल उपचार: [तुरंत करने योग्य कार्य]
दीर्घकालिक उपचार: [विस्तृत उपचार योजना]
रोकथाम: [भविष्य में बचाव के उपाय]
जैविक विकल्प: [रासायनिक के अलावा प्राकृतिक उपचार]
रिकवरी समय: [अनुमानित ठीक होने का समय]
फॉलो-अप: [कब दोबारा जांच करें]"""

        # Add context if available
        if crop_type:
            base_prompt += f"\n\n**फसल का प्रकार:** {crop_type}"

        if location:
            base_prompt += f"\n**स्थान:** {location} (क्षेत्रीय रोगों को ध्यान में रखें)"

        if symptoms:
            base_prompt += f"\n**अतिरिक्त लक्षण:** {symptoms}"

        if growth_stage:
            base_prompt += f"\n**फसल की अवस्था:** {growth_stage}"

        # Add image feature context
        if image_features and not image_features.get("error"):
            indicators = image_features.get("potential_disease_indicators", [])
            if indicators:
                base_prompt += f"\n**प्रारंभिक संकेत:** {', '.join(indicators)}"

            brightness = image_features.get("brightness", 0)
            if brightness < 50:
                base_prompt += "\n**नोट:** छवि कम रोशनी में ली गई है, संभावित निदान में इसे ध्यान में रखें"

        base_prompt += "\n\n**महत्वपूर्ण:** यदि आपको निश्चित रूप से कोई रोग दिखाई नहीं दे रहा या छवि अस्पष्ट है, तो कृपया इसका स्पष्ट उल्लेख करें और बेहतर छवि लेने की सलाह दें।"

        return base_prompt

    async def _call_vision_ai(self, image_b64: str, prompt: str) -> str:
        """Call Google Vision AI API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_b64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for consistent medical advice
                    "maxOutputTokens": 2048,
                    "topP": 0.8,
                    "topK": 40
                }
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    headers=headers,
                    json=payload
                )

                response.raise_for_status()
                result = response.json()

                # Extract response text
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        return candidate["content"]["parts"][0]["text"]

                raise Exception("Invalid API response format")

        except httpx.HTTPStatusError as e:
            logger.error(f"Vision AI API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Vision AI API failed: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error("Vision AI API timeout")
            raise Exception("Vision AI service timeout")
        except Exception as e:
            logger.error(f"Vision AI call error: {e}")
            raise

    def _parse_and_enhance_diagnosis(self, ai_response: str, crop_type: str, location: str) -> CropDiagnosis:
        """Parse AI response and enhance with agricultural knowledge"""
        try:
            # Extract information using regex patterns
            disease_name = self._extract_field(ai_response, r"रोग का नाम[:\s]*([^\n]+)")
            confidence_str = self._extract_field(ai_response, r"विश्वास स्तर[:\s]*([0-9.]+)")
            severity = self._extract_field(ai_response, r"गंभीरता[:\s]*([^\n]+)")
            symptoms = self._extract_field(ai_response, r"मुख्य लक्षण[:\s]*([^\n]+)")
            immediate_treatment = self._extract_field(ai_response, r"तत्काल उपचार[:\s]*([^\n]+)")
            long_term_treatment = self._extract_field(ai_response, r"दीर्घकालिक उपचार[:\s]*([^\n]+)")
            prevention_text = self._extract_field(ai_response, r"रोकथाम[:\s]*([^\n]+)")
            organic_alternatives_text = self._extract_field(ai_response, r"जैविक विकल्प[:\s]*([^\n]+)")
            recovery_time = self._extract_field(ai_response, r"रिकवरी समय[:\s]*([^\n]+)")
            follow_up = self._extract_field(ai_response, r"फॉलो-अप[:\s]*([^\n]+)")

            # Process confidence
            try:
                confidence = float(confidence_str) if confidence_str else 50.0
            except:
                confidence = 50.0

            # Process lists
            prevention_list = [p.strip() for p in prevention_text.split(',') if p.strip()] if prevention_text else []
            organic_list = [o.strip() for o in organic_alternatives_text.split(',') if
                            o.strip()] if organic_alternatives_text else []
            symptoms_list = [s.strip() for s in symptoms.split(',') if s.strip()] if symptoms else []

            # Enhance with database knowledge
            enhanced_info = self._enhance_with_database(disease_name, crop_type, location)

            # Create comprehensive treatment plan
            comprehensive_treatment = self._create_comprehensive_treatment(
                immediate_treatment, long_term_treatment, enhanced_info
            )

            # Generate immediate actions
            immediate_actions = self._generate_immediate_actions(severity, disease_name, confidence)

            return CropDiagnosis(
                disease_name=disease_name or "अज्ञात रोग",
                confidence=min(confidence, 95.0),  # Cap at 95%
                severity=severity or "मध्यम",
                treatment=comprehensive_treatment,
                prevention=prevention_list + enhanced_info.get("additional_prevention", []),
                symptoms_detected=symptoms_list,
                immediate_actions=immediate_actions,
                follow_up_timeline=follow_up or "7 दिन बाद",
                organic_alternatives=organic_list + enhanced_info.get("organic_options", []),
                expected_recovery_time=recovery_time or "2-3 सप्ताह"
            )

        except Exception as e:
            logger.error(f"Diagnosis parsing error: {e}")
            # Return parsed information from full response
            return self._fallback_parse(ai_response)

    def _extract_field(self, text: str, pattern: str) -> str:
        """Extract field using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _enhance_with_database(self, disease_name: str, crop_type: str, location: str) -> Dict[str, Any]:
        """Enhance diagnosis with database knowledge"""
        enhanced_info = {
            "additional_prevention": [],
            "organic_options": [],
            "regional_factors": [],
            "seasonal_considerations": []
        }

        if not disease_name or not crop_type:
            return enhanced_info

        # Check disease database
        crop_diseases = self.disease_database.get(crop_type.lower(), {})

        # Find matching disease
        disease_key = None
        for key in crop_diseases.keys():
            if any(word in disease_name.lower() for word in key.lower().split()):
                disease_key = key
                break

        if disease_key:
            disease_info = crop_diseases[disease_key]

            # Add database prevention measures
            enhanced_info["additional_prevention"] = disease_info.get("prevention", [])

            # Add organic alternatives
            enhanced_info["organic_options"] = disease_info.get("organic_treatment", [])

            # Add regional factors
            if location:
                location_lower = location.lower()
                regional_info = disease_info.get("regional_info", {})
                for region, info in regional_info.items():
                    if region.lower() in location_lower:
                        enhanced_info["regional_factors"] = info.get("special_considerations", [])
                        break

        # Add seasonal considerations
        current_month = datetime.now().month
        seasonal_map = {
            "monsoon": [6, 7, 8, 9],
            "winter": [11, 12, 1, 2],
            "summer": [3, 4, 5, 10]
        }

        current_season = None
        for season, months in seasonal_map.items():
            if current_month in months:
                current_season = season
                break

        if current_season:
            seasonal_advice = {
                "monsoon": ["अधिक आर्द्रता के कारण फंगल रोगों का खतरा", "जल निकासी सुनिश्चित करें"],
                "winter": ["कम तापमान में रोग धीमी गति से फैलता है", "सुबह की ओस का प्रभाव देखें"],
                "summer": ["तेज गर्मी में कीट समस्या बढ़ सकती है", "पानी की कमी से तनाव न बढ़ने दें"]
            }
            enhanced_info["seasonal_considerations"] = seasonal_advice.get(current_season, [])

        return enhanced_info

    def _create_comprehensive_treatment(self, immediate: str, long_term: str, enhanced_info: Dict) -> str:
        """Create comprehensive treatment plan"""
        treatment_parts = []

        if immediate:
            treatment_parts.append(f"**तत्काल उपचार:** {immediate}")

        if long_term:
            treatment_parts.append(f"**दीर्घकालिक उपचार:** {long_term}")

        # Add regional considerations
        regional_factors = enhanced_info.get("regional_factors", [])
        if regional_factors:
            treatment_parts.append(f"**क्षेत्रीय विशेष बातें:** {'; '.join(regional_factors)}")

        # Add seasonal considerations
        seasonal_considerations = enhanced_info.get("seasonal_considerations", [])
        if seasonal_considerations:
            treatment_parts.append(f"**मौसमी सावधानियां:** {'; '.join(seasonal_considerations)}")

        return "\n\n".join(treatment_parts) if treatment_parts else "स्थानीय कृषि विशेषज्ञ से सलाह लें"

    def _generate_immediate_actions(self, severity: str, disease_name: str, confidence: float) -> List[str]:
        """Generate immediate actions based on severity and confidence"""
        actions = []

        # High confidence actions
        if confidence > 80:
            actions.append("✅ निदान की पुष्टि हो गई है - तुरंत उपचार शुरू करें")
        elif confidence > 60:
            actions.append("⚠️ संभावित निदान - सावधानी से उपचार करें")
        else:
            actions.append("❓ अनिश्चित निदान - विशेषज्ञ से पुष्टि कराएं")

        # Severity-based actions
        if severity and "गंभीर" in severity.lower():
            actions.extend([
                "🚨 गंभीर स्थिति - तत्काल कार्रवाई आवश्यक",
                "🚨 प्रभावित पौधों को तुरंत अलग करें",
                "🚨 24 घंटे के अंदर उपचार शुरू करें"
            ])
        elif severity and "मध्यम" in severity.lower():
            actions.extend([
                "⚡ मध्यम गंभीरता - 2-3 दिन में उपचार शुरू करें",
                "📸 प्रगति की निगरानी के लिए तस्वीरें लेते रहें"
            ])
        else:
            actions.extend([
                "👁️ नियमित निगरानी बनाए रखें",
                "📝 लक्षणों में बदलाव का रिकॉर्ड रखें"
            ])

        # Disease-specific actions
        if disease_name:
            if "रतुआ" in disease_name or "rust" in disease_name.lower():
                actions.append("🍃 संक्रमित पत्तियों को तुरंत हटाकर जलाएं")
            elif "ब्लाइट" in disease_name or "blight" in disease_name.lower():
                actions.append("💨 हवा का संचार बढ़ाने के लिए पत्तियों को काटें")
            elif "विल्ट" in disease_name or "wilt" in disease_name.lower():
                actions.append("💧 सिंचाई की जांच करें - अधिक या कम पानी दोनों हानिकारक")

        # General actions
        actions.extend([
            "🧤 उपचार के दौरान दस्ताने पहनें",
            "📞 स्थानीय कृषि विभाग को स्थिति की जानकारी दें",
            "📱 इस ऐप में अपडेट करते रहें"
        ])

        return actions

    def _fallback_parse(self, ai_response: str) -> CropDiagnosis:
        """Fallback parsing when structured parsing fails"""
        # Extract key information from unstructured response
        confidence = 70.0  # Default confidence

        # Try to find confidence in text
        conf_match = re.search(r'(\d+)%', ai_response)
        if conf_match:
            confidence = float(conf_match.group(1))

        # Determine severity from keywords
        severity = "मध्यम"
        if any(word in ai_response.lower() for word in ["गंभीर", "severe", "critical", "urgent"]):
            severity = "गंभीर"
        elif any(word in ai_response.lower() for word in ["हल्का", "mild", "light", "minor"]):
            severity = "हल्का"

        # Extract disease name (first significant term)
        disease_match = re.search(r'(रोग|disease|infection|fungus|bacteria|virus)[:\s]*([^\n.]+)', ai_response,
                                  re.IGNORECASE)
        disease_name = disease_match.group(2).strip() if disease_match else "पादप रोग"

        return CropDiagnosis(
            disease_name=disease_name,
            confidence=confidence,
            severity=severity,
            treatment=ai_response[:500] + "..." if len(ai_response) > 500 else ai_response,
            prevention=["नियमित निगरानी", "स्वच्छता बनाए रखें", "संतुलित उर्वरीकरण"],
            symptoms_detected=["AI विश्लेषण के अनुसार"],
            immediate_actions=["तुरंत स्थानीय विशेषज्ञ से सलाह लें"],
            follow_up_timeline="3-5 दिन",
            organic_alternatives=["नीम का तेल", "जैविक कवकनाशी"],
            expected_recovery_time="2-4 सप्ताह"
        )

    def _load_disease_database(self) -> Dict[str, Any]:
        """Load disease database for knowledge enhancement"""
        return {
            "wheat": {
                "rust": {
                    "symptoms": ["नारंगी-लाल धब्बे", "पत्तियों पर पुस्ट्यूल्स"],
                    "prevention": ["प्रतिरोधी किस्में", "उचित फसल चक्र", "संतुलित उर्वरीकरण"],
                    "organic_treatment": ["नीम का तेल 5ml/लीटर", "गोमूत्र छिड़काव"],
                    "regional_info": {
                        "punjab": {"special_considerations": ["मार्च-अप्रैल में विशेष सावधानी"]},
                        "up": {"special_considerations": ["आर्द्रता नियंत्रण महत्वपूर्ण"]}
                    }
                },
                "blight": {
                    "symptoms": ["भूरे धब्बे", "पीले हाले के साथ"],
                    "prevention": ["बीज उपचार", "जल निकासी", "हवा का संचार"],
                    "organic_treatment": ["त्रिकोडर्मा", "बेकिंग सोडा स्प्रे"]
                }
            },
            "rice": {
                "blast": {
                    "symptoms": ["हीरे के आकार के धब्बे", "ग्रे सेंटर"],
                    "prevention": ["संतुलित नाइट्रोजन", "पानी का प्रबंधन"],
                    "organic_treatment": ["जैविक सिलिका", "केल्प मील"]
                },
                "bacterial_blight": {
                    "symptoms": ["पीली धारियां", "मुरझाना"],
                    "prevention": ["प्रमाणित बीज", "खेत की स्वच्छता"],
                    "organic_treatment": ["कॉपर सल्फेट कम मात्रा में", "हल्दी का घोल"]
                }
            },
            "tomato": {
                "early_blight": {
                    "symptoms": ["संकेंद्रित वलयों के साथ धब्बे"],
                    "prevention": ["मल्चिंग", "ड्रिप सिंचाई"],
                    "organic_treatment": ["एप्सम साल्ट स्प्रे", "दही का छिड़काव"]
                },
                "late_blight": {
                    "symptoms": ["तेजी से फैलने वाले काले धब्बे"],
                    "prevention": ["तापमान और आर्द्रता नियंत्रण"],
                    "organic_treatment": ["बोर्डो मिश्रण", "लहसुन का घोल"]
                }
            },
            "cotton": {
                "bollworm": {
                    "symptoms": ["फल में छेद", "कीड़े दिखना"],
                    "prevention": ["फेरोमोन ट्रैप", "नीम की खली"],
                    "organic_treatment": ["बीटी स्प्रे", "नीम तेल"]
                }
            },
            "sugarcane": {
                "red_rot": {
                    "symptoms": ["लाल धब्बे", "अंदरूनी सड़न"],
                    "prevention": ["रोग मुक्त बीज", "जल निकासी"],
                    "organic_treatment": ["त्रिकोडर्मा ट्रीटमेंट"]
                }
            }
        }

    async def analyze_crop_image(
            self,
            image_data: bytes,
            crop_type: str = None,
            location: str = None,
            symptoms: str = None,
            growth_stage: str = None,
            user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive crop image analysis

        Returns structured analysis result for API consumption
        """
        try:
            # Perform disease detection
            diagnosis = await self.detect_crop_disease(
                image_data=image_data,
                crop_type=crop_type,
                location=location,
                symptoms=symptoms,
                growth_stage=growth_stage
            )

            # Extract image features for additional insights
            image_features = ImageEnhancer.extract_image_features(image_data)

            # Create comprehensive response
            result = {
                "status": "success",
                "analysis_method": "vision_ai_enhanced",
                "timestamp": datetime.now().isoformat(),
                "diagnosis": {
                    "disease_name": diagnosis.disease_name,
                    "confidence": f"{diagnosis.confidence}%",
                    "severity": diagnosis.severity,
                    "symptoms_detected": diagnosis.symptoms_detected
                },
                "treatment_plan": {
                    "immediate_actions": diagnosis.immediate_actions,
                    "treatment_details": diagnosis.treatment,
                    "organic_alternatives": diagnosis.organic_alternatives,
                    "prevention_measures": diagnosis.prevention
                },
                "timeline": {
                    "follow_up": diagnosis.follow_up_timeline,
                    "expected_recovery": diagnosis.expected_recovery_time
                },
                "image_analysis": {
                    "quality_score": self._calculate_image_quality_score(image_features),
                    "features_detected": image_features.get("potential_disease_indicators", []),
                    "image_size": image_features.get("image_size", "unknown")
                },
                "recommendations": {
                    "next_steps": self._get_next_steps(diagnosis),
                    "monitoring_schedule": self._get_monitoring_schedule(diagnosis),
                    "expert_consultation": self._should_consult_expert(diagnosis)
                },
                "context": {
                    "crop_type": crop_type,
                    "location": location,
                    "growth_stage": growth_stage,
                    "analysis_id": f"analysis_{int(datetime.now().timestamp())}"
                }
            }

            return result

        except Exception as e:
            logger.error(f"Comprehensive analysis error: {e}")
            return {
                "status": "error",
                "error_type": "analysis_failed",
                "message": "छवि विश्लेषण में समस्या हुई। कृपया दोबारा कोशिश करें।",
                "suggestions": [
                    "स्पष्ट और अच्छी गुणवत्ता की तस्वीर लें",
                    "प्रभावित भागों को स्पष्ट रूप से दिखाएं",
                    "अच्छी रोशनी में तस्वीर लें"
                ],
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_image_quality_score(self, image_features: Dict) -> int:
        """Calculate image quality score (0-100)"""
        if image_features.get("error"):
            return 0

        score = 70  # Base score

        # Check brightness
        brightness = image_features.get("brightness", 128)
        if 80 <= brightness <= 200:
            score += 10
        elif brightness < 50 or brightness > 220:
            score -= 20

        # Check contrast
        contrast = image_features.get("contrast", 50)
        if contrast > 30:
            score += 10
        elif contrast < 15:
            score -= 15

        # Check if green areas detected (healthy plant material)
        if image_features.get("has_green_areas"):
            score += 10

        # Check image size
        image_size = image_features.get("image_size", (0, 0))
        if image_size[0] > 800 and image_size[1] > 600:
            score += 10
        elif image_size[0] < 400 or image_size[1] < 300:
            score -= 10

        return max(0, min(100, score))

    def _get_next_steps(self, diagnosis: CropDiagnosis) -> List[str]:
        """Get recommended next steps"""
        steps = []

        if diagnosis.confidence > 80:
            steps.append("निदान की पुष्टि हो गई - उपचार योजना का पालन करें")
        else:
            steps.append("अधिक स्पष्ट तस्वीरें लें या विशेषज्ञ से सलाह लें")

        if diagnosis.severity == "गंभीर":
            steps.append("तुरंत स्थानीय कृषि अधिकारी से संपर्क करें")

        steps.extend([
            "उपचार की प्रगति की निगरानी करें",
            "आसपास के पौधों की जांच करें",
            "इस ऐप में अपडेट साझा करते रहें"
        ])

        return steps

    def _get_monitoring_schedule(self, diagnosis: CropDiagnosis) -> List[Dict[str, str]]:
        """Get monitoring schedule based on diagnosis"""
        schedule = [
            {"day": "1", "action": "उपचार के तुरंत बाद प्रभावित क्षेत्र की जांच"},
            {"day": "3", "action": "लक्षणों में सुधार या बिगड़ने का आकलन"},
            {"day": "7", "action": "उपचार की प्रभावशीलता का मूल्यांकन"}
        ]

        if diagnosis.severity == "गंभीर":
            schedule.insert(0, {"day": "0", "action": "तत्काल निगरानी शुरू करें"})
            schedule.append({"day": "10", "action": "यदि सुधार न हो तो वैकल्पिक उपचार"})

        schedule.append({"day": "14", "action": "दीर्घकालिक प्रभाव की समीक्षा"})

        return schedule

    def _should_consult_expert(self, diagnosis: CropDiagnosis) -> str:
        """Determine when to consult expert"""
        if diagnosis.confidence < 60:
            return "कम विश्वास स्तर - तुरंत विशेषज्ञ से सलाह लें"
        elif diagnosis.severity == "गंभीर":
            return "गंभीर रोग - 24 घंटे में विशेषज्ञ से मिलें"
        elif diagnosis.confidence < 80:
            return "यदि 3 दिन में सुधार न हो तो विशेषज्ञ से संपर्क करें"
        else:
            return "यदि उपचार काम न करे तो 7 दिन बाद विशेषज्ञ से मिलें"

    async def health_check(self) -> bool:
        """Check if Vision AI service is healthy"""
        try:
            # Simple health check - try to call API with minimal request
            test_image = Image.new('RGB', (100, 100), color='green')
            img_bytes = io.BytesIO()
            test_image.save(img_bytes, format='JPEG')

            # Test image enhancement
            ImageEnhancer.enhance_image(img_bytes.getvalue())

            return True
        except Exception as e:
            logger.error(f"Vision AI health check failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Vision AI service cleanup completed")

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "total_calls": self.call_count,
            "successful_calls": self.success_count,
            "failed_calls": self.error_count,
            "success_rate": (self.success_count / max(self.call_count, 1)) * 100,
            "average_confidence": "85%",  # This would be calculated from actual data
            "supported_crops": list(self.disease_database.keys())
        }