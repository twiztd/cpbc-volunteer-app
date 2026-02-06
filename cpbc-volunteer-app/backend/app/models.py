from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Volunteer(Base):
    """Volunteer signup information."""
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    signup_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ministries = relationship("VolunteerMinistry", back_populates="volunteer", cascade="all, delete-orphan")
    notes = relationship("VolunteerNote", back_populates="volunteer", cascade="all, delete-orphan")


class VolunteerMinistry(Base):
    """Junction table for volunteer ministry selections (many-to-many)."""
    __tablename__ = "volunteer_ministries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False)
    ministry_area = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)

    volunteer = relationship("Volunteer", back_populates="ministries")


class AdminUser(Base):
    """Admin users for the dashboard."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    password_reset_token = Column(String(64), nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)

    notes = relationship("VolunteerNote", back_populates="admin")


class VolunteerNote(Base):
    """Notes added by admins to volunteers."""
    __tablename__ = "volunteer_notes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    note_text = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    volunteer = relationship("Volunteer", back_populates="notes")
    admin = relationship("AdminUser", back_populates="notes")
