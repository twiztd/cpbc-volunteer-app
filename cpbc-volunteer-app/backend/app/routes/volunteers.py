import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Volunteer, VolunteerMinistry, AdminUser
from ..schemas import (
    VolunteerCreate,
    VolunteerResponse,
    MinistryAreasResponse,
    MessageResponse,
    MINISTRY_CATEGORIES
)
from ..email import send_volunteer_notification_email, ADMIN_NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/volunteers",
    response_model=VolunteerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a volunteer signup",
    description="Public endpoint for volunteers to submit their signup form"
)
async def create_volunteer(volunteer_data: VolunteerCreate, db: Session = Depends(get_db)):
    """
    Create a new volunteer signup.

    This endpoint:
    1. Validates the ministry selections against known categories
    2. Creates the volunteer record
    3. Creates ministry selection records
    4. Sends email notification to admins (fails gracefully)
    """
    logger.info(f"New volunteer signup: {volunteer_data.email}")

    # Validate ministry selections
    for ministry in volunteer_data.ministries:
        if ministry.category not in MINISTRY_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {ministry.category}"
            )
        if ministry.ministry_area not in MINISTRY_CATEGORIES[ministry.category]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ministry area '{ministry.ministry_area}' for category '{ministry.category}'"
            )

    try:
        # Create volunteer record
        db_volunteer = Volunteer(
            name=volunteer_data.name,
            phone=volunteer_data.phone,
            email=volunteer_data.email
        )
        db.add(db_volunteer)
        db.flush()  # Get the ID without committing

        # Create ministry selection records
        for ministry in volunteer_data.ministries:
            db_ministry = VolunteerMinistry(
                volunteer_id=db_volunteer.id,
                ministry_area=ministry.ministry_area,
                category=ministry.category
            )
            db.add(db_ministry)

        db.commit()
        db.refresh(db_volunteer)

        logger.info(f"Volunteer created successfully: ID {db_volunteer.id}")

        # Send email notification (fails gracefully)
        try:
            # Determine notification recipients
            if ADMIN_NOTIFICATION_EMAIL:
                to_emails = [ADMIN_NOTIFICATION_EMAIL]
            else:
                super_admin = db.query(AdminUser).filter(
                    AdminUser.is_super_admin == True,
                    AdminUser.is_active == True
                ).first()
                to_emails = [super_admin.email] if super_admin else []

            ministries = [
                {"ministry_area": m.ministry_area, "category": m.category}
                for m in db_volunteer.ministries
            ]
            send_volunteer_notification_email(
                to_emails=to_emails,
                volunteer_name=db_volunteer.name,
                volunteer_email=db_volunteer.email,
                volunteer_phone=db_volunteer.phone,
                ministries=ministries,
            )
        except Exception as e:
            logger.error(f"Failed to send volunteer notification: {str(e)}")

        return db_volunteer

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating volunteer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your signup. Please try again."
        )


@router.get(
    "/ministry-areas",
    response_model=MinistryAreasResponse,
    summary="Get ministry categories and areas",
    description="Returns the list of all ministry categories and their areas for the signup form"
)
async def get_ministry_areas():
    """Return the list of ministry categories and areas."""
    logger.info("Ministry areas requested")
    return MinistryAreasResponse(categories=MINISTRY_CATEGORIES)
