from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    """
    Base schema shared across user representations.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name (2 to 100 characters)",
        examples=["Jane Doe"]
    )
    email: EmailStr = Field(
        ...,
        description="Unique email address",
        examples=["jane.doe@example.com"]
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 2:
            raise ValueError("Name must be at least 2 characters long (excluding spaces)")
        return trimmed

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserCreate(UserBase):
    """
    Request payload schema for user registration.
    Collects name, email, and password.
    """
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Password (minimum 6 characters)",
        examples=["SecurePass123!"]
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return value


class UserLogin(BaseModel):
    """
    Request payload schema for user login.
    Collects email and password.
    """
    email: EmailStr = Field(
        ...,
        description="Registered email address",
        examples=["jane.doe@example.com"]
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Account password"
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    """
    Safe user output schema.
    NOTE: `hashed_password` is intentionally excluded to ensure security.
    """
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationResponse(BaseModel):
    """
    Response schema returned upon successful registration.
    """
    success: bool = True
    message: str
    user: UserResponse


class TokenResponse(BaseModel):
    """
    Response schema returned upon successful authentication.
    Contains the signed JWT bearer token and user metadata.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse
