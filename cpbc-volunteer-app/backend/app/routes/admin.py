import csv
import io
import logging
import secrets
from datetime import datetime, timedelta
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
    TransferSuperAdminRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VolunteerResponse,
    VolunteerListResponse,
    VolunteerUpdate,
    VolunteerDetailResponse,
    VolunteerNoteCreate,
    VolunteerNoteResponse,
    VolunteerNoteListResponse,
    VolunteerBasicInfo,
    MinistryReportItem,
    MinistryReportResponse,
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
from ..email import send_password_reset_email

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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Send a password reset email to the provided admin email address."
)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset. Generates a token, stores it with 1hr expiry,
    and sends a reset link via email.
    Always returns success to prevent email enumeration.
    """
    email_lower = request_data.email.lower()
    logger.info(f"Password reset requested for: {email_lower}")

    admin_user = db.query(AdminUser).filter(
        func.lower(AdminUser.email) == email_lower,
        AdminUser.is_active == True
    ).first()

    if admin_user:
        token = secrets.token_hex(16)
        admin_user.password_reset_token = token
        admin_user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        send_password_reset_email(admin_user.email, token)

    return MessageResponse(
        message="If an account exists with that email, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
    description="Complete password reset using the token from the reset email.",
    responses={400: {"model": ErrorResponse}}
)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Complete password reset. Validates token and expiry,
    updates password, and clears the token.
    """
    if request_data.password != request_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    if len(request_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )

    admin_user = db.query(AdminUser).filter(
        AdminUser.password_reset_token == request_data.token,
        AdminUser.is_active == True
    ).first()

    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link"
        )

    if not admin_user.password_reset_expires or admin_user.password_reset_expires < datetime.utcnow():
        admin_user.password_reset_token = None
        admin_user.password_reset_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link has expired. Please request a new one."
        )

    admin_user.hashed_password = get_password_hash(request_data.password)
    admin_user.password_reset_token = None
    admin_user.password_reset_expires = None
    db.commit()

    logger.info(f"Password reset completed for {admin_user.email}")

    return MessageResponse(message="Your password has been reset successfully. You can now log in.")


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
    description="Export volunteer data to a CSV file. Supports filtering by ministry area. Ministry areas appear as columns."
)
async def export_volunteers_csv(
    ministry_area: Optional[str] = Query(None, description="Filter by ministry area"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Export volunteer data as a CSV file.

    Ministry areas appear as individual columns with 'X' marks.
    Only ministry columns where at least one volunteer signed up are included.
    Supports filtering by ministry area to export only matching volunteers.
    """
    logger.info(f"Admin {current_admin.email} exporting volunteer data (filter: {ministry_area})")

    query = db.query(Volunteer)

    if ministry_area:
        query = query.join(VolunteerMinistry).filter(
            VolunteerMinistry.ministry_area == ministry_area
        )

    volunteers = query.order_by(Volunteer.signup_date.desc()).all()

    # Collect all ministry areas that have at least one signup among these volunteers
    ministry_columns = set()
    for volunteer in volunteers:
        for m in volunteer.ministries:
            ministry_columns.add(m.ministry_area)

    ministry_columns = sorted(ministry_columns)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header with dynamic ministry columns
    header = ["Name", "Email", "Phone", "Signup Date"] + ministry_columns
    writer.writerow(header)

    # Write data rows
    for volunteer in volunteers:
        volunteer_ministries = {m.ministry_area for m in volunteer.ministries}
        row = [
            volunteer.name,
            volunteer.email,
            volunteer.phone,
            volunteer.signup_date.strftime("%Y-%m-%d"),
        ]
        for ministry in ministry_columns:
            row.append("X" if ministry in volunteer_ministries else "")
        writer.writerow(row)

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
        total=len(admins),
        current_user_is_super_admin=current_admin.is_super_admin
    )


@router.post(
    "/users",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin user",
    description="Create a new admin user. Requires super admin.",
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}
)
async def create_admin_user(
    admin_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Create a new admin user.
    Only accessible by super admin.
    """
    # Check super admin permission
    if not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can create new admin users"
        )

    email_lower = admin_data.email.lower()
    logger.info(f"Super admin {current_admin.email} creating new admin: {email_lower}")

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
        is_active=True,
        is_super_admin=False
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
    description="Update an admin user's status. Requires super admin for activate/deactivate.",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}
)
async def update_admin_user(
    admin_id: int,
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Update an admin user (activate/deactivate).
    Only super admin can activate/deactivate other admins.
    Cannot deactivate yourself or the super admin.
    """
    logger.info(f"Admin {current_admin.email} updating admin ID: {admin_id}")

    # Find the admin to update
    admin_to_update = db.query(AdminUser).filter(AdminUser.id == admin_id).first()

    if not admin_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )

    # Check super admin permission for status changes
    if update_data.is_active is not None and not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can activate/deactivate admin users"
        )

    # Prevent deactivating yourself
    if update_data.is_active is False and admin_to_update.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    # Prevent deactivating the super admin
    if update_data.is_active is False and admin_to_update.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate the super admin account"
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


@router.post(
    "/transfer-super",
    response_model=MessageResponse,
    summary="Transfer super admin role",
    description="Transfer super admin role to another admin. Only super admin can do this.",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def transfer_super_admin(
    transfer_data: TransferSuperAdminRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Transfer super admin role to another admin.
    Only the current super admin can do this.
    """
    # Check super admin permission
    if not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can transfer the super admin role"
        )

    # Cannot transfer to yourself
    if transfer_data.target_admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer super admin role to yourself"
        )

    # Find target admin
    target_admin = db.query(AdminUser).filter(AdminUser.id == transfer_data.target_admin_id).first()

    if not target_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target admin user not found"
        )

    if not target_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer super admin role to an inactive admin"
        )

    # Transfer the role
    current_admin.is_super_admin = False
    target_admin.is_super_admin = True

    db.commit()

    logger.info(f"Super admin role transferred from {current_admin.email} to {target_admin.email}")

    return MessageResponse(message=f"Super admin role transferred to {target_admin.name or target_admin.email}")


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


# ==================== Ministry Reports ====================

@router.get(
    "/reports/by-ministry",
    response_model=MinistryReportResponse,
    summary="Get volunteers grouped by ministry",
    description="Get all ministries with volunteer counts and volunteer lists."
)
async def get_ministry_report(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get all ministries with their volunteers.
    """
    logger.info(f"Admin {current_admin.email} generating ministry report")

    ministries = []
    all_volunteer_ids = set()

    # Iterate through all ministry categories and areas
    for category, areas in MINISTRY_CATEGORIES.items():
        for ministry_area in areas:
            # Get volunteers for this ministry
            volunteer_ministries = db.query(VolunteerMinistry).filter(
                VolunteerMinistry.ministry_area == ministry_area,
                VolunteerMinistry.category == category
            ).all()

            volunteers = []
            for vm in volunteer_ministries:
                volunteer = vm.volunteer
                all_volunteer_ids.add(volunteer.id)
                volunteers.append(VolunteerBasicInfo(
                    id=volunteer.id,
                    name=volunteer.name,
                    email=volunteer.email,
                    phone=volunteer.phone,
                    signup_date=volunteer.signup_date
                ))

            ministries.append(MinistryReportItem(
                ministry_area=ministry_area,
                category=category,
                volunteer_count=len(volunteers),
                volunteers=volunteers
            ))

    return MinistryReportResponse(
        ministries=ministries,
        total_ministries=len(ministries),
        total_volunteers=len(all_volunteer_ids)
    )


@router.get(
    "/reports/by-ministry/{ministry_name}",
    response_model=MinistryReportItem,
    summary="Get volunteers for a specific ministry",
    description="Get full volunteer details for a specific ministry area.",
    responses={404: {"model": ErrorResponse}}
)
async def get_ministry_volunteers(
    ministry_name: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get volunteers for a specific ministry area.
    """
    logger.info(f"Admin {current_admin.email} getting volunteers for ministry: {ministry_name}")

    # Find the category for this ministry
    category = None
    for cat, areas in MINISTRY_CATEGORIES.items():
        if ministry_name in areas:
            category = cat
            break

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ministry area '{ministry_name}' not found"
        )

    # Get volunteers for this ministry
    volunteer_ministries = db.query(VolunteerMinistry).filter(
        VolunteerMinistry.ministry_area == ministry_name,
        VolunteerMinistry.category == category
    ).all()

    volunteers = []
    for vm in volunteer_ministries:
        volunteer = vm.volunteer
        volunteers.append(VolunteerBasicInfo(
            id=volunteer.id,
            name=volunteer.name,
            email=volunteer.email,
            phone=volunteer.phone,
            signup_date=volunteer.signup_date
        ))

    return MinistryReportItem(
        ministry_area=ministry_name,
        category=category,
        volunteer_count=len(volunteers),
        volunteers=volunteers
    )


@router.get(
    "/reports/export-all",
    summary="Export all ministries to CSV",
    description="Export all ministries with their volunteers as a CSV file."
)
async def export_all_ministries_csv(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Export all ministries with volunteers to CSV.
    """
    logger.info(f"Admin {current_admin.email} exporting all ministries report")

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Category",
        "Ministry Area",
        "Volunteer Name",
        "Email",
        "Phone",
        "Signup Date"
    ])

    # Write data for each ministry
    for category, areas in MINISTRY_CATEGORIES.items():
        for ministry_area in areas:
            volunteer_ministries = db.query(VolunteerMinistry).filter(
                VolunteerMinistry.ministry_area == ministry_area,
                VolunteerMinistry.category == category
            ).all()

            if volunteer_ministries:
                for vm in volunteer_ministries:
                    volunteer = vm.volunteer
                    writer.writerow([
                        category,
                        ministry_area,
                        volunteer.name,
                        volunteer.email,
                        volunteer.phone,
                        volunteer.signup_date.strftime("%Y-%m-%d")
                    ])
            else:
                # Include empty ministries
                writer.writerow([
                    category,
                    ministry_area,
                    "",
                    "",
                    "",
                    ""
                ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_ministries_report.csv"}
    )


@router.get(
    "/reports/export-ministry/{ministry_name}",
    summary="Export single ministry to CSV",
    description="Export volunteers for a specific ministry as a CSV file.",
    responses={404: {"model": ErrorResponse}}
)
async def export_ministry_csv(
    ministry_name: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Export volunteers for a specific ministry to CSV.
    """
    logger.info(f"Admin {current_admin.email} exporting ministry report: {ministry_name}")

    # Find the category for this ministry
    category = None
    for cat, areas in MINISTRY_CATEGORIES.items():
        if ministry_name in areas:
            category = cat
            break

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ministry area '{ministry_name}' not found"
        )

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Name",
        "Email",
        "Phone",
        "Signup Date"
    ])

    # Get volunteers for this ministry
    volunteer_ministries = db.query(VolunteerMinistry).filter(
        VolunteerMinistry.ministry_area == ministry_name,
        VolunteerMinistry.category == category
    ).all()

    for vm in volunteer_ministries:
        volunteer = vm.volunteer
        writer.writerow([
            volunteer.name,
            volunteer.email,
            volunteer.phone,
            volunteer.signup_date.strftime("%Y-%m-%d")
        ])

    output.seek(0)

    # Sanitize filename
    safe_name = ministry_name.replace("/", "-").replace("\\", "-")

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={safe_name}_volunteers.csv"}
    )
