# ============================================================================
# utils/validators.py
# ============================================================================
from typing import List, Optional, Tuple
import re


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_crop_name(crop: str) -> Tuple[bool, Optional[str]]:
    """Validate crop name"""
    if not crop or len(crop.strip()) < 2:
        return False, "Crop name must be at least 2 characters long"

    # List of supported crops
    supported_crops = [
        'wheat', 'rice', 'paddy', 'corn', 'maize', 'tomato', 'potato', 'onion',
        'cotton', 'sugarcane', 'soybean', 'mustard', 'groundnut', 'sunflower',
        'bajra', 'jowar', 'barley', 'gram', 'peas', 'chickpea', 'lentil',
        'okra', 'eggplant', 'brinjal', 'cauliflower', 'cabbage', 'carrot'
    ]

    normalized_crop = normalize_crop_name(crop)
    if normalized_crop not in supported_crops:
        return False, f"Crop '{crop}' not supported. Try: {', '.join(supported_crops[:10])}..."

    return True, None


def validate_location(location: str) -> Tuple[bool, Optional[str]]:
    """Validate location"""
    if not location or len(location.strip()) < 2:
        return False, "Location must be at least 2 characters long"

    # Check for valid characters (letters, spaces, hyphens)
    if not re.match(r'^[a-zA-Z\s\-]+$', location):
        return False, "Location can only contain letters, spaces, and hyphens"

    return True, None


# ============================================================================
# app/google_adk_integration/utils/helpers.py
# ============================================================================
import logging
import json
import os
from typing import Dict, Any, List
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file with fallback"""
    try:
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Could not load {file_path}: {e}")

    # Return mock data if file not found
    return get_mock_market_data()


def normalize_crop_name(crop_name: str) -> str:
    """Normalize crop name for consistent matching"""
    if not crop_name:
        return ""

    # Mapping common Hindi/English crop names
    crop_mapping = {
        # Hindi to English
        "गेहूं": "wheat",
        "चावल": "rice",
        "धान": "rice",
        "मक्का": "maize",
        "टमाटर": "tomato",
        "आलू": "potato",
        "प्याज": "onion",
        "गन्ना": "sugarcane",
        "कपास": "cotton",
        "सोयाबीन": "soybean",
        "बाजरा": "millet",
        "ज्वार": "sorghum",
        "अरहर": "pigeon_pea",
        "चना": "chickpea",
        "मूंग": "green_gram",
        "सरसों": "mustard",
        "तिल": "sesame",
        "मूंगफली": "groundnut",
        "सूरजमुखी": "sunflower",

        # English variations
        "wheat": "wheat",
        "rice": "rice",
        "maize": "maize",
        "corn": "maize",
        "tomato": "tomato",
        "potato": "potato",
        "onion": "onion",
        "sugarcane": "sugarcane",
        "cotton": "cotton",
        "soybean": "soybean"
    }

    normalized = crop_name.lower().strip()
    return crop_mapping.get(normalized, normalized)


def get_mock_market_data() -> Dict[str, Any]:
    """Get mock market data when real data is not available"""
    return {
        "wheat": {
            "unit": "क्विंटल",
            "base_price": 2100,
            "markets": [
                {
                    "location": "नई दिल्ली मंडी",
                    "current_price": 2150,
                    "min_price": 2100,
                    "max_price": 2200,
                    "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                    "variety": "PBW 343",
                    "grade": "FAQ"
                },
                {
                    "location": "मुंबई मंडी",
                    "current_price": 2180,
                    "min_price": 2150,
                    "max_price": 2220,
                    "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                    "variety": "HD 2967",
                    "grade": "FAQ"
                }
            ]
        },
        "rice": {
            "unit": "क्विंटल",
            "base_price": 3000,
            "markets": [
                {
                    "location": "हरियाणा मंडी",
                    "current_price": 3200,
                    "min_price": 3100,
                    "max_price": 3300,
                    "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                    "variety": "Basmati",
                    "grade": "FAQ"
                }
            ]
        },
        "tomato": {
            "unit": "क्विंटल",
            "base_price": 40,
            "markets": [
                {
                    "location": "पुणे मंडी",
                    "current_price": 45,
                    "min_price": 35,
                    "max_price": 55,
                    "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                    "variety": "Local",
                    "grade": "FAQ"
                }
            ]
        },
        "onion": {
            "unit": "क्विंटल",
            "base_price": 30,
            "markets": [
                {
                    "location": "नाशिक मंडी",
                    "current_price": 35,
                    "min_price": 30,
                    "max_price": 40,
                    "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                    "variety": "Local",
                    "grade": "FAQ"
                }
            ]
        },
        "potato": {
            "unit": "क्विंटल",
            "base_price": 25,
            "markets": [
                {
                    "location": "आगरा मंडी",
                    "current_price": 28,
                    "min_price": 25,
                    "max_price": 32,
                    "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                    "variety": "Local",
                    "grade": "FAQ"
                }
            ]
        }
    }


def format_currency(amount: float, currency: str = "₹") -> str:
    """Format currency amount"""
    if amount >= 100000:
        return f"{currency}{amount / 100000:.1f} लाख"
    elif amount >= 1000:
        return f"{currency}{amount / 1000:.1f}K"
    else:
        return f"{currency}{amount:.0f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default


def validate_numeric_input(value: Any, min_value: float = None, max_value: float = None) -> tuple[bool, str]:
    """Validate numeric input with optional range checking"""
    try:
        num_value = float(value)

        if min_value is not None and num_value < min_value:
            return False, f"Value must be at least {min_value}"

        if max_value is not None and num_value > max_value:
            return False, f"Value must be at most {max_value}"

        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid numeric value"


def clean_text_input(text: str) -> str:
    """Clean and normalize text input"""
    if not text:
        return ""

    # Remove extra whitespaces
    cleaned = " ".join(text.split())

    # Remove special characters but keep Hindi characters
    import re
    cleaned = re.sub(r'[^\w\s\u0900-\u097F]', '', cleaned)

    return cleaned.strip()


# ============================================================================
# app/google_adk_integration/utils/validators.py
# ============================================================================
import re
from typing import Tuple


def validate_crop_name(crop_name: str) -> Tuple[bool, str]:
    """Validate crop name input"""
    if not crop_name:
        return False, "फसल का नाम आवश्यक है"

    if not crop_name.strip():
        return False, "फसल का नाम खाली नहीं हो सकता"

    if len(crop_name.strip()) < 2:
        return False, "फसल का नाम कम से कम 2 अक्षर का होना चाहिए"

    # Check for valid characters (allow Hindi, English, numbers, spaces, hyphens)
    if not re.match(r'^[\u0900-\u097Fa-zA-Z0-9\s\-]+$', crop_name):
        return False, "फसल के नाम में केवल अक्षर, संख्या और हाइफन होना चाहिए"

    return True, ""


def validate_location(location: str) -> Tuple[bool, str]:
    """Validate location input"""
    if not location:
        return True, ""  # Location is optional

    if not location.strip():
        return False, "स्थान खाली नहीं हो सकता"

    if len(location.strip()) < 2:
        return False, "स्थान का नाम कम से कम 2 अक्षर का होना चाहिए"

    # Check for valid characters
    if not re.match(r'^[\u0900-\u097Fa-zA-Z0-9\s\-,\.]+$', location):
        return False, "स्थान के नाम में अमान्य चिह्न हैं"

    return True, ""


def validate_quantity(quantity: str) -> Tuple[bool, str, float]:
    """Validate quantity input"""
    if not quantity:
        return False, "मात्रा आवश्यक है", 0.0

    try:
        qty = float(quantity)
        if qty <= 0:
            return False, "मात्रा शून्य से अधिक होनी चाहिए", 0.0
        if qty > 10000:  # Reasonable upper limit
            return False, "मात्रा बहुत अधिक है", 0.0
        return True, "", qty
    except ValueError:
        return False, "मात्रा एक वैध संख्या होनी चाहिए", 0.0


def validate_price(price: str) -> Tuple[bool, str, float]:
    """Validate price input"""
    if not price:
        return False, "कीमत आवश्यक है", 0.0

    try:
        prc = float(price)
        if prc < 0:
            return False, "कीमत नकारात्मक नहीं हो सकती", 0.0
        if prc > 100000:  # Reasonable upper limit
            return False, "कीमत बहुत अधिक है", 0.0
        return True, "", prc
    except ValueError:
        return False, "कीमत एक वैध संख्या होनी चाहिए", 0.0


def validate_coordinates(latitude: str, longitude: str) -> Tuple[bool, str, float, float]:
    """Validate GPS coordinates"""
    try:
        lat = float(latitude)
        lng = float(longitude)

        # Check valid latitude range
        if not (-90 <= lat <= 90):
            return False, "अक्षांश -90 से 90 के बीच होना चाहिए", 0.0, 0.0

        # Check valid longitude range
        if not (-180 <= lng <= 180):
            return False, "देशांतर -180 से 180 के बीच होना चाहिए", 0.0, 0.0

        # Check if coordinates are in India (approximate bounds)
        if not (6 <= lat <= 37 and 68 <= lng <= 97):
            return False, "निर्देशांक भारत के बाहर हैं", 0.0, 0.0

        return True, "", lat, lng

    except ValueError:
        return False, "निर्देशांक वैध संख्या होने चाहिए", 0.0, 0.0


def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, str]:
    """Validate date range"""
    try:
        from datetime import datetime

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if start > end:
            return False, "शुरुआती तारीख अंतिम तारीख के बाद नहीं हो सकती"

        if (end - start).days > 365:
            return False, "तारीख की सीमा 1 साल से अधिक नहीं हो सकती"

        return True, ""

    except ValueError:
        return False, "तारीख का प्रारूप YYYY-MM-DD होना चाहिए"


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address"""
    if not email:
        return False, "ईमेल आवश्यक है"

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "अमान्य ईमेल पता"

    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate Indian phone number"""
    if not phone:
        return False, "फोन नंबर आवश्यक है"

    # Remove all non-digit characters
    clean_phone = re.sub(r'\D', '', phone)

    # Check for valid Indian mobile number patterns
    if re.match(r'^[6-9]\d{9}$', clean_phone):  # 10 digit mobile
        return True, ""
    elif re.match(r'^91[6-9]\d{9}$', clean_phone):  # With country code
        return True, ""
    else:
        return False, "अमान्य भारतीय मोबाइल नंबर"


def validate_quality(quality: str) -> tuple[bool, str]:
    """Validate quality input"""
    valid_qualities = ["premium", "high", "medium", "low", "poor"]

    if not quality:
        return False, "गुणवत्ता की जानकारी आवश्यक है"

    if quality.lower() not in valid_qualities:
        return False, f"गुणवत्ता इनमें से कोई एक होनी चाहिए: {', '.join(valid_qualities)}"

    return True, ""


def validate_vehicle_type(vehicle_type: str) -> tuple[bool, str]:
    """Validate vehicle type input"""
    valid_vehicles = ["truck", "tempo", "tractor", "pickup"]

    if not vehicle_type:
        return False, "वाहन का प्रकार आवश्यक है"

    if vehicle_type.lower() not in valid_vehicles:
        return False, f"वाहन का प्रकार इनमें से कोई एक होना चाहिए: {', '.join(valid_vehicles)}"

    return True, ""


def validate_prediction_days(days: Any) -> tuple[bool, str]:
    """Validate prediction days input"""
    try:
        day_count = int(days)

        if day_count <= 0:
            return False, "दिनों की संख्या 0 से अधिक होनी चाहिए"

        if day_count > 90:  # Max 3 months prediction
            return False, "अधिकतम 90 दिन का पूर्वानुमान उपलब्ध है"

        return True, ""
    except (ValueError, TypeError):
        return False, "दिनों की संख्या एक वैध संख्या होनी चाहिए"


def validate_distance(distance_km: Any) -> tuple[bool, str]:
    """Validate distance input"""
    try:
        dist = float(distance_km)

        if dist <= 0:
            return False, "दूरी 0 से अधिक होनी चाहिए"

        if dist > 500:  # 500 km max search radius
            return False, "अधिकतम खोज दूरी 500 किमी है"

        return True, ""
    except (ValueError, TypeError):
        return False, "दूरी एक वैध संख्या होनी चाहिए"


def validate_user_input(message: str) -> Tuple[bool, Optional[str]]:
    """Validate user input message"""
    if not message or len(message.strip()) < 1:
        return False, "Message cannot be empty"

    if len(message) > 1000:
        return False, "Message too long (max 1000 characters)"

    # Check for potentially harmful content
    harmful_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>'
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, message, re.IGNORECASE | re.DOTALL):
            return False, "Message contains potentially harmful content"

    return True, None