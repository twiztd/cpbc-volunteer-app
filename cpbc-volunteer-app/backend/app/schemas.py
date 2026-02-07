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
    "Missions": [
        "Guatemala Mission Trip",
        "El Salvador Mission Trip",
        "3:18 Church (Third Saturday)",
        "5 Loaves 2 Fish (Thursday before 1st Saturday)"
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


class VolunteerUpdate(BaseModel):
    """Request schema for updating a volunteer."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    ministries: Optional[list[MinistrySelection]] = None


# Volunteer Note Schemas
class VolunteerNoteCreate(BaseModel):
    """Request schema for creating a note on a volunteer."""
    note_text: str


class VolunteerNoteResponse(BaseModel):
    """Response schema for a volunteer note."""
    id: int
    volunteer_id: int
    admin_id: Optional[int]
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class VolunteerNoteListResponse(BaseModel):
    """Response schema for listing volunteer notes."""
    notes: list[VolunteerNoteResponse]
    total: int


class VolunteerDetailResponse(BaseModel):
    """Response schema for a volunteer with notes."""
    id: int
    name: str
    phone: str
    email: str
    signup_date: datetime
    created_at: datetime
    updated_at: datetime
    ministries: list[VolunteerMinistryResponse]
    notes: list[VolunteerNoteResponse]

    class Config:
        from_attributes = True


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
    is_super_admin: bool

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """Response schema for listing admin users."""
    admins: list[AdminUserResponse]
    total: int
    current_user_is_super_admin: bool


class AdminUserUpdate(BaseModel):
    """Request schema for updating an admin user."""
    is_active: Optional[bool] = None
    name: Optional[str] = None


class TransferSuperAdminRequest(BaseModel):
    """Request schema for transferring super admin role."""
    target_admin_id: int


class ForgotPasswordRequest(BaseModel):
    """Request schema for initiating password reset (email only)."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for completing password reset with token."""
    token: str
    password: str
    confirm_password: str


# Ministry Report Schemas
class VolunteerBasicInfo(BaseModel):
    """Basic volunteer info for reports."""
    id: int
    name: str
    email: str
    phone: str
    signup_date: datetime

    class Config:
        from_attributes = True


class MinistryReportItem(BaseModel):
    """Single ministry report with volunteer list."""
    ministry_area: str
    category: str
    volunteer_count: int
    volunteers: list[VolunteerBasicInfo]


class MinistryReportResponse(BaseModel):
    """Response schema for ministry reports."""
    ministries: list[MinistryReportItem]
    total_ministries: int
    total_volunteers: int


# Generic Response Schemas
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
