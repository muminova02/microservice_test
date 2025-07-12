from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Token(BaseModel):
    """
    Token response model
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Token payload model
    """
    username: Optional[str] = None


class UserBase(BaseModel):
    """
    Base user model with common attributes
    """
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False


class UserCreate(UserBase):
    """
    User creation model with password
    """
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    """
    User response model without sensitive data
    """
    pass


class UserInDB(UserBase):
    """
    User model for database with hashed password
    """
    hashed_password: str


class TokenValidationResponse(BaseModel):
    """
    Response model for token validation
    """
    valid: bool
    user: Optional[UserResponse] = None


class RegisterResponse(BaseModel):
    """
    Response model for user registration
    """
    message: str
    user: UserResponse


class HealthResponse(BaseModel):
    """
    Response model for health check
    """
    status: str
    service: str
