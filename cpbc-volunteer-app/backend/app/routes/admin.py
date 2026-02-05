import csv
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Volunteer, VolunteerMinistry, AdminUser, VolunteerNote
from ..schemas import (
    AdminLogin,
    AdminTokenResponse,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserUpdate,
    VolunteerResponse,
    VolunteerListResponse,
    VolunteerUpdate,
    VolunteerDetailResponse,
    VolunteerNoteCreate,
    VolunteerNoteResponse,
    VolunteerNoteListResponse,
    MessageResponse,
    ErrorResponse,
    MINISTRY_CATEGORIES
)
from ..auth.auth import (
    verify_password,
    create_access_token,
    get_current_admin_user,
    get_password_hash
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

    email_lower = login_data.email.lower()
    admin_user = db.query(AdminUser).filter(
        func.lower(AdminUser.email) == email_lower,
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


# ==================== Admin User Management ====================

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List all admin users",
    description="Get a list of all admin users. Requires authentication."
)
async def list_admin_users(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    List all admin users.
    Only accessible by authenticated admins.
    """
    logger.info(f"Admin {current_admin.email} listing admin users")

    admins = db.query(AdminUser).order_by(AdminUser.created_at.desc()).all()

    return AdminUserListResponse(
        admins=admins,
        total=len(admins)
    )


@router.post(
    "/users",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin user",
    description="Create a new admin user. Requires authentication.",
    responses={400: {"model": ErrorResponse}}
)
async def create_admin_user(
    admin_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Create a new admin user.
    Only accessible by authenticated admins.
    """
    email_lower = admin_data.email.lower()
    logger.info(f"Admin {current_admin.email} creating new admin: {email_lower}")

    # Check if email already exists (case-insensitive)
    existing_admin = db.query(AdminUser).filter(
        func.lower(AdminUser.email) == email_lower
    ).first()

    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An admin with this email already exists"
        )

    # Create new admin user with lowercase email
    hashed_password = get_password_hash(admin_data.password)

    new_admin = AdminUser(
        email=email_lower,
        hashed_password=hashed_password,
        name=admin_data.name,
        is_active=True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    logger.info(f"Created new admin user: {new_admin.email}")

    return new_admin


@router.patch(
    "/users/{admin_id}",
    response_model=AdminUserResponse,
    summary="Update an admin user",
    description="Update an admin user's status or name. Requires authentication.",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def update_admin_user(
    admin_id: int,
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Update an admin user (activate/deactivate or change name).
    Only accessible by authenticated admins.
    Cannot deactivate yourself.
    """
    logger.info(f"Admin {current_admin.email} updating admin ID: {admin_id}")

    # Find the admin to update
    admin_to_update = db.query(AdminUser).filter(AdminUser.id == admin_id).first()

    if not admin_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )

    # Prevent deactivating yourself
    if update_data.is_active is False and admin_to_update.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    # Update fields
    if update_data.is_active is not None:
        admin_to_update.is_active = update_data.is_active
        action = "activated" if update_data.is_active else "deactivated"
        logger.info(f"Admin {admin_to_update.email} {action} by {current_admin.email}")

    if update_data.name is not None:
        admin_to_update.name = update_data.name

    db.commit()
    db.refresh(admin_to_update)

    return admin_to_update


# ==================== Volunteer Management ====================

@router.get(
    "/volunteers/{volunteer_id}",
    response_model=VolunteerDetailResponse,
    summary="Get a single volunteer",
    description="Get a volunteer with all details including notes.",
    responses={404: {"model": ErrorResponse}}
)
async def get_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get a single volunteer by ID with all details.
    """
    logger.info(f"Admin {current_admin.email} getting volunteer ID: {volunteer_id}")

    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )

    # Build response with notes including admin info
    notes_response = []
    for note in volunteer.notes:
        notes_response.append(VolunteerNoteResponse(
            id=note.id,
            volunteer_id=note.volunteer_id,
            admin_id=note.admin_id,
            admin_name=note.admin.name if note.admin else None,
            admin_email=note.admin.email if note.admin else None,
            note_text=note.note_text,
            created_at=note.created_at
        ))

    return VolunteerDetailResponse(
        id=volunteer.id,
        name=volunteer.name,
        phone=volunteer.phone,
        email=volunteer.email,
        signup_date=volunteer.signup_date,
        created_at=volunteer.created_at,
        updated_at=volunteer.updated_at,
        ministries=volunteer.ministries,
        notes=notes_response
    )


@router.patch(
    "/volunteers/{volunteer_id}",
    response_model=VolunteerResponse,
    summary="Update a volunteer",
    description="Update volunteer info and/or ministry selections.",
    responses={404: {"model": ErrorResponse}}
)
async def update_volunteer(
    volunteer_id: int,
    update_data: VolunteerUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Update a volunteer's info and/or ministry selections.
    """
    logger.info(f"Admin {current_admin.email} updating volunteer ID: {volunteer_id}")

    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )

    # Update basic fields
    if update_data.name is not None:
        volunteer.name = update_data.name
    if update_data.phone is not None:
        volunteer.phone = update_data.phone
    if update_data.email is not None:
        volunteer.email = update_data.email

    # Update ministry selections if provided
    if update_data.ministries is not None:
        # Validate ministry selections
        for ministry in update_data.ministries:
            if ministry.category not in MINISTRY_CATEGORIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {ministry.category}"
                )
            if ministry.ministry_area not in MINISTRY_CATEGORIES[ministry.category]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid ministry area: {ministry.ministry_area}"
                )

        # Delete existing ministry selections
        db.query(VolunteerMinistry).filter(
            VolunteerMinistry.volunteer_id == volunteer_id
        ).delete()

        # Add new ministry selections
        for ministry in update_data.ministries:
            new_ministry = VolunteerMinistry(
                volunteer_id=volunteer_id,
                ministry_area=ministry.ministry_area,
                category=ministry.category
            )
            db.add(new_ministry)

    db.commit()
    db.refresh(volunteer)

    logger.info(f"Updated volunteer {volunteer_id} by {current_admin.email}")

    return volunteer


@router.delete(
    "/volunteers/{volunteer_id}",
    response_model=MessageResponse,
    summary="Delete a volunteer",
    description="Permanently delete a volunteer and all associated data.",
    responses={404: {"model": ErrorResponse}}
)
async def delete_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Delete a volunteer permanently.
    """
    logger.info(f"Admin {current_admin.email} deleting volunteer ID: {volunteer_id}")

    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )

    volunteer_name = volunteer.name
    db.delete(volunteer)
    db.commit()

    logger.info(f"Deleted volunteer {volunteer_id} ({volunteer_name}) by {current_admin.email}")

    return MessageResponse(message=f"Volunteer '{volunteer_name}' has been deleted")


# ==================== Volunteer Notes ====================

@router.get(
    "/volunteers/{volunteer_id}/notes",
    response_model=VolunteerNoteListResponse,
    summary="Get volunteer notes",
    description="Get all notes for a volunteer.",
    responses={404: {"model": ErrorResponse}}
)
async def get_volunteer_notes(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get all notes for a volunteer.
    """
    logger.info(f"Admin {current_admin.email} getting notes for volunteer ID: {volunteer_id}")

    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )

    notes_response = []
    for note in volunteer.notes:
        notes_response.append(VolunteerNoteResponse(
            id=note.id,
            volunteer_id=note.volunteer_id,
            admin_id=note.admin_id,
            admin_name=note.admin.name if note.admin else None,
            admin_email=note.admin.email if note.admin else None,
            note_text=note.note_text,
            created_at=note.created_at
        ))

    return VolunteerNoteListResponse(
        notes=notes_response,
        total=len(notes_response)
    )


@router.post(
    "/volunteers/{volunteer_id}/notes",
    response_model=VolunteerNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a note to a volunteer",
    description="Add a new note to a volunteer.",
    responses={404: {"model": ErrorResponse}}
)
async def add_volunteer_note(
    volunteer_id: int,
    note_data: VolunteerNoteCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Add a note to a volunteer.
    """
    logger.info(f"Admin {current_admin.email} adding note to volunteer ID: {volunteer_id}")

    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )

    new_note = VolunteerNote(
        volunteer_id=volunteer_id,
        admin_id=current_admin.id,
        note_text=note_data.note_text
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    logger.info(f"Added note to volunteer {volunteer_id} by {current_admin.email}")

    return VolunteerNoteResponse(
        id=new_note.id,
        volunteer_id=new_note.volunteer_id,
        admin_id=new_note.admin_id,
        admin_name=current_admin.name,
        admin_email=current_admin.email,
        note_text=new_note.note_text,
        created_at=new_note.created_at
    )
