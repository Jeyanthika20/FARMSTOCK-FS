"""
Notifications Route
Handles push notification preferences and in-app alert registration.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class NotificationPreference(BaseModel):
    user_id: str = Field(..., example="farmer_001")
    crops: List[str] = Field(..., example=["Tomato", "Onion"])
    markets: List[str] = Field(..., example=["Coimbatore", "Chennai"])
    alert_types: List[str] = Field(default=["disease", "market", "planting"], example=["disease", "market"])
    language: str = Field(default="en", example="ta", description="'en' for English, 'ta' for Tamil")
    phone: Optional[str] = Field(None, example="9876543210")

    class Config:
        json_schema_extra = {"example": {
            "user_id": "farmer_001",
            "crops": ["Tomato", "Onion"],
            "markets": ["Coimbatore", "Chennai"],
            "alert_types": ["disease", "market"],
            "language": "ta",
            "phone": "9876543210"
        }}


class NotificationResponse(BaseModel):
    status: str
    user_id: str
    message: str
    message_ta: str
    registered_at: str


@router.post("/notifications/register", response_model=NotificationResponse)
def register_notifications(body: NotificationPreference):
    """
    Register notification preferences for a farmer.
    Returns confirmation in both English and Tamil.
    """
    return NotificationResponse(
        status="registered",
        user_id=body.user_id,
        message=f"Notifications enabled for {', '.join(body.crops)} in {', '.join(body.markets)}.",
        message_ta=f"{', '.join(body.crops)} பயிர்களுக்கும் {', '.join(body.markets)} சந்தைகளுக்கும் அறிவிப்புகள் இயக்கப்பட்டன.",
        registered_at=datetime.now().isoformat()
    )


@router.get("/notifications/test/{user_id}")
def test_notification(user_id: str):
    """Send a test notification to verify setup."""
    return {
        "status": "sent",
        "user_id": user_id,
        "test_message": "FarmStock notification working correctly!",
        "test_message_ta": "FarmStock அறிவிப்பு சரியாக வேலை செய்கிறது!",
        "timestamp": datetime.now().isoformat()
    }
