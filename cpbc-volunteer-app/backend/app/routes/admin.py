import csv
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Volunteer, VolunteerMinistry, AdminUser
from ..schemas import (
    AdminLogin,
    AdminTokenResponse,
    VolunteerResponse,
    VolunteerListResponse,
    ErrorResponse
)
from ..auth.auth import (
    verify_password,
    create_access_token,
    get_current_admin_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/login",
    response_model=AdminTokenResponse,
    summary="Admin login",
    description="Authenticate admin user and return JWT token",
    responses={401: {"model": ErrorResponse}}
)
async def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    """
    Authenticate admin user with email and password.
    Returns a JWT token for subsequent authenticated requests.
    """
    logger.info(f"Admin login attempt: {login_data.email}")

    admin_user = db.query(AdminUser).filter(
        AdminUser.email == login_data.email,
        AdminUser.is_active == True
    ).first()

    if not admin_user or not verify_password(login_data.password, admin_user.hashed_password):
        logger.warning(f"Failed login attempt for: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": admin_user.email})
    logger.info(f"Admin logged in successfully: {login_data.email}")

    return AdminTokenResponse(access_token=access_token)


@router.get(
    "/volunteers",
    response_model=VolunteerListResponse,
    summary="List all volunteers",
    description="Get a list of all volunteers with their ministry selections. Supports filtering and sorting."
)
async def list_volunteers(
    ministry_area: Optional[str] = Query(None, description="Filter by ministry area"),
    category: Optional[str] = Query(None, description="Filter by ministry category"),
    sort_by: Optional[str] = Query("date", description="Sort by: name, date, or ministry"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    List all volunteers with optional filtering and sorting.

    Filtering options:
    - ministry_area: Filter volunteers who signed up for a specific ministry area
    - category: Filter volunteers who signed up for any ministry in a category

    Sorting options:
    - name: Sort alphabetically by volunteer name
    - date: Sort by signup date (newest first)
    - ministry: Sort by number of ministry selections
    """
    logger.info(f"Admin {current_admin.email} listing volunteers")

    query = db.query(Volunteer)

    # Apply filters
    if ministry_area:
        query = query.join(VolunteerMinistry).filter(
            VolunteerMinistry.ministry_area == ministry_area
        )
    elif category:
        query = query.join(VolunteerMinistry).filter(
            VolunteerMinistry.category == category
        )

    # Apply sorting
    if sort_by == "name":
        query = query.order_by(Volunteer.name)
    elif sort_by == "ministry":
        # Sort by number of ministry selections
        query = query.outerjoin(VolunteerMinistry).group_by(Volunteer.id).order_by(
            func.count(VolunteerMinistry.id).desc()
        )
    else:  # Default: sort by date
        query = query.order_by(Volunteer.signup_date.desc())

    volunteers = query.all()

    return VolunteerListResponse(
        volunteers=volunteers,
        total=len(volunteers)
    )


@router.get(
    "/reports/export",
    summary="Export volunteer data as CSV",
    description="Export all volunteer data to a CSV file"
)
async def export_volunteers_csv(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Export all volunteer data as a CSV file.

    CSV columns:
    - ID, Name, Phone, Email, Signup Date, Ministry Areas, Categories
    """
    logger.info(f"Admin {current_admin.email} exporting volunteer data")

    volunteers = db.query(Volunteer).order_by(Volunteer.signup_date.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "ID",
        "Name",
        "Phone",
        "Email",
        "Signup Date",
        "Ministry Areas",
        "Categories"
    ])

    # Write data rows
    for volunteer in volunteers:
        ministry_areas = ", ".join([m.ministry_area for m in volunteer.ministries])
        categories = ", ".join(set([m.category for m in volunteer.ministries]))

        writer.writerow([
            volunteer.id,
            volunteer.name,
            volunteer.phone,
            volunteer.email,
            volunteer.signup_date.strftime("%Y-%m-%d %H:%M:%S"),
            ministry_areas,
            categories
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=volunteers_export.csv"}
    )
