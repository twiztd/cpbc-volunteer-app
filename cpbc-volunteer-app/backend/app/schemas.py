from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Ministry Categories Configuration
MINISTRY_CATEGORIES = {
    "Children's Ministry": [
        "Childcare and/or Teaching",
        "VBS"
    ],
    "Hospitality": [
        "Greeters",
        "Make Contact with Visitors",
        "Kitchen Cleanup"
    ],
    "Media": [
        "Sound, etc.",
        "Social Media"
    ],
    "Mission Trips": [
        "BBQ Fundraisers"
    ],
    "Member Care": [
        "Meal Trains for members in need",
        "Help for Elderly/Widows"
    ],
    "Community Outreach": [
        "Trunk or Treat",
        "Easter Event",
        "New Outreach Programs"
    ],
    "Building/Grounds": [
        "Maintenance",
        "Security"
    ],
    "Recurring Service Events": [
        "318 Church (Third Saturday)",
        "5 Loaves 2 Fish (Thursday before 1st Saturday)"
    ]
}


# Volunteer Schemas
class MinistrySelection(BaseModel):
    """A single ministry area selection with its parent category."""
    ministry_area: str
    category: str


class VolunteerCreate(BaseModel):
    """Request schema for creating a volunteer signup."""
    name: str
    phone: str
    email: EmailStr
    ministries: list[MinistrySelection]


class VolunteerMinistryResponse(BaseModel):
    """Response schema for a ministry selection."""
    id: int
    ministry_area: str
    category: str

    class Config:
        from_attributes = True


class VolunteerResponse(BaseModel):
    """Response schema for a volunteer."""
    id: int
    name: str
    phone: str
    email: str
    signup_date: datetime
    created_at: datetime
    updated_at: datetime
    ministries: list[VolunteerMinistryResponse]

    class Config:
        from_attributes = True


class VolunteerListResponse(BaseModel):
    """Response schema for listing volunteers."""
    volunteers: list[VolunteerResponse]
    total: int


# Ministry Area Schemas
class MinistryAreasResponse(BaseModel):
    """Response schema for ministry categories and areas."""
    categories: dict[str, list[str]]


# Admin Schemas
class AdminLogin(BaseModel):
    """Request schema for admin login."""
    email: EmailStr
    password: str


class AdminTokenResponse(BaseModel):
    """Response schema for successful admin login."""
    access_token: str
    token_type: str = "bearer"


class AdminUserCreate(BaseModel):
    """Request schema for creating an admin user."""
    email: EmailStr
    password: str
    name: Optional[str] = None


class AdminUserResponse(BaseModel):
    """Response schema for an admin user."""
    id: int
    email: str
    name: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Generic Response Schemas
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
