from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    RegistrationResponse,
    TokenResponse
)
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.api.deps import get_current_user

# Initialize the Authentication API router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Validates user details, hashes password with bcrypt, and stores new user in MySQL."
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    User Registration Endpoint:
    1. Validates incoming payload via Pydantic schema (UserCreate).
    2. Queries MySQL to reject duplicate email addresses.
    3. Hashes the plain-text password using bcrypt.
    4. Persists the new user record into the 'users' table.
    5. Returns the newly created user (excluding password) with HTTP 201 Created.
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please choose another email."
        )

    hashed_pw = get_password_hash(user_in.password)

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_pw
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while creating your account. Please try again."
        ) from exc

    return RegistrationResponse(
        success=True,
        message="User account created successfully! You can now proceed to log in.",
        user=new_user
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain JWT access token",
    description="Verifies credentials against MySQL database and returns a signed JWT access token."
)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    User Login Endpoint:
    1. Looks up the user by email in MySQL.
    2. Verifies provided password against the stored bcrypt hash using constant-time comparison.
    3. If invalid, returns a generic 401 Unauthorized (to prevent email enumeration).
    4. If valid, generates a signed JWT access token containing the user's ID as the subject.
    5. Returns the token along with safe user metadata.
    """
    # 1. Lookup user by email (credentials.email is normalized to lowercase by Pydantic)
    user = db.query(User).filter(User.email == credentials.email).first()

    # 2. Verify existence and password match
    # Note: verify_password uses constant-time bcrypt comparison to prevent timing attacks
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials and try again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 3. Create signed JWT access token
    access_token = create_access_token(subject=user.id)

    # 4. Return token response
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Protected endpoint demonstrating token verification. Requires Authorization Bearer header."
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Protected Endpoint:
    Returns the profile of the user currently authenticated via JWT.
    Demonstrates route protection and session verification.
    """
    return current_user
