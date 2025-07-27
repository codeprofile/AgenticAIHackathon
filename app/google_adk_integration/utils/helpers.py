# ============================================================================
# utils/helpers.py
# ============================================================================
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import re



# Configure logging
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import logging
import json
import os
from typing import Any, Dict
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
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
    """Load JSON data from file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logging.error(f"Error loading JSON data from {file_path}: {e}")
        return {}


def save_json_data(data: Dict[str, Any], file_path: str) -> bool:
    """Save JSON data to file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON data to {file_path}: {e}")
        return False


def normalize_crop_name(crop_name: str) -> str:
    """Normalize crop name for consistent usage"""
    if not crop_name:
        return ""

    # Convert to lowercase and strip whitespace
    normalized = crop_name.lower().strip()

    # Handle common variations
    variations = {
        "गेहूं": "wheat",
        "चावल": "rice",
        "धान": "rice",
        "टमाटर": "tomato",
        "प्याज": "onion",
        "आलू": "potato",
        "गन्ना": "sugarcane",
        "कपास": "cotton",
        "सोयाबीन": "soybean",
        "मक्का": "maize",
        "बाजरा": "bajra"
    }

    return variations.get(normalized, normalized)


def format_currency(amount: float, currency: str = "₹") -> str:
    """Format currency amount"""
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format percentage value"""
    return f"{value:+.1f}%"


def get_current_time() -> str:
    """Get current time in Indian format"""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that handles zero division"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ValueError):
        return default


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    return text.strip().replace('\n', ' ').replace('\r', ' ')


def normalize_location(location: str) -> str:
    """Normalize location name"""
    if not location:
        return ""

    # Remove extra spaces and convert to lowercase
    normalized = re.sub(r'\s+', ' ', location.strip().lower())

    # Handle common variations
    location_mapping = {
        'new delhi': 'delhi',
        'ncr': 'delhi',
        'mumbai': 'maharashtra',
        'pune': 'maharashtra',
        'bangalore': 'karnataka',
        'bengaluru': 'karnataka',
        'hyderabad': 'telangana',
        'chennai': 'tamil_nadu',
        'kolkata': 'west_bengal'
    }

    return location_mapping.get(normalized, normalized)



def extract_user_context(message: str, existing_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Extract user context from message"""
    context = existing_context or {}
    message_lower = message.lower()

    # Extract location mentions
    location_patterns = [
        r'from\s+([a-zA-Z\s]+)',
        r'in\s+([a-zA-Z\s]+)',
        r'at\s+([a-zA-Z\s]+)'
    ]

    for pattern in location_patterns:
        match = re.search(pattern, message_lower)
        if match:
            location = match.group(1).strip()
            if len(location) > 2:  # Avoid single letters
                context['location'] = normalize_location(location)
                break

    # Extract crop mentions
    crop_keywords = ['wheat', 'rice', 'paddy', 'corn', 'maize', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane']
    mentioned_crops = [crop for crop in crop_keywords if crop in message_lower]
    if mentioned_crops:
        context['crops'] = list(set(context.get('crops', []) + mentioned_crops))

    return context