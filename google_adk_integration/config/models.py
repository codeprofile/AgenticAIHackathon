# app/google_adk_integration/config/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    agent_used: Optional[str] = None
    tools_called: Optional[List[str]] = None
    confidence: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class UserContext(BaseModel):
    """User context model"""
    location: Optional[str] = None
    state: Optional[str] = None
    crops: Optional[List[str]] = None
    farming_type: Optional[str] = "general"
    language: str = "hi"
    experience_level: str = "intermediate"


# app/google_adk_integration/utils/helpers.py
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import re


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def extract_user_context(message: str, existing_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Extract user context from message"""
    context = existing_context or {}
    message_lower = message.lower()

    # Extract location mentions
    location_patterns = [
        r'from\s+([a-zA-Z\s]+)',
        r'in\s+([a-zA-Z\s]+)',
        r'से\s+([a-zA-Z\s]+)',
        r'में\s+([a-zA-Z\s]+)'
    ]

    for pattern in location_patterns:
        match = re.search(pattern, message_lower)
        if match:
            location = match.group(1).strip()
            if len(location) > 2:
                context['location'] = location
                break

    # Extract crop mentions
    crop_keywords = ['wheat', 'rice', 'paddy', 'corn', 'maize', 'tomato', 'potato', 'onion',
                     'गेहूं', 'चावल', 'मक्का', 'टमाटर', 'आलू', 'प्याज']
    mentioned_crops = [crop for crop in crop_keywords if crop in message_lower]
    if mentioned_crops:
        context['crops'] = list(set(context.get('crops', []) + mentioned_crops))

    return context
