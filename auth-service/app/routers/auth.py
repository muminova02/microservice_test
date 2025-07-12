from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import get_settings
from app.models import (
    Token, 
    UserInDB, 
    UserCreate, 
    UserResponse, 
    RegisterResponse,
    TokenValidationResponse
)
from app.security import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    get_password_hash,
    user_to_response
)
from app.database import create_user, user_exists
from app.telemetry import get_tracer, logger

# Setup
settings = get_settings()
tracer = get_tracer()
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    with tracer.start_as_current_span("login_for_access_token") as span:
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("username", form_data.username)

        logger.info(f"Login attempt for user: {form_data.username}")

        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("login_result", "failed")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )

        logger.info(f"Login successful for user: {form_data.username}")
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("login_result", "success")

        return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=RegisterResponse)
async def register(user_data: UserCreate):
    """
    Register a new user
    """
    with tracer.start_as_current_span("register_user") as span:
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("username", user_data.username)
            span.set_attribute("email", user_data.email)

        logger.info(f"Registration attempt for user: {user_data.username}")

        if user_exists(user_data.username):
            logger.warning(f"Registration failed - username already exists: {user_data.username}")
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("registration_result", "username_exists")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create the user dict for database
        user_dict = user_data.dict()
        user_dict.pop("password")
        user_dict["hashed_password"] = hashed_password

        # Save to database
        created_user = create_user(user_dict)

        logger.info(f"User registered successfully: {user_data.username}")
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("registration_result", "success")

        # Convert to response model
        user_response = user_to_response(created_user)

        return {
            "message": "User registered successfully",
            "user": user_response
        }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information
    """
    with tracer.start_as_current_span("read_users_me") as span:
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("username", current_user.username)

        logger.info(f"User info requested: {current_user.username}")

        return user_to_response(current_user)


@router.get("/validate", response_model=TokenValidationResponse)
async def validate_token(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Validate the current token and return user information
    """
    with tracer.start_as_current_span("validate_token") as span:
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("username", current_user.username)

        logger.info(f"Token validation requested for user: {current_user.username}")

        return {
            "valid": True,
            "user": user_to_response(current_user)
        }
