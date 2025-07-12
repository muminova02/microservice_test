from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.models import TokenData, UserInDB, UserResponse
from app.database import get_user
from app.telemetry import get_tracer

# Setup
settings = get_settings()
tracer = get_tracer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    with tracer.start_as_current_span("verify_password"):
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage
    """
    with tracer.start_as_current_span("get_password_hash"):
        return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user with username and password
    """
    with tracer.start_as_current_span("authenticate_user") as span:
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("username", username)

        user = get_user(username)
        if not user:
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("auth_result", "user_not_found")
            return None

        if not verify_password(password, user.hashed_password):
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("auth_result", "invalid_password")
            return None

        if settings.TELEMETRY_ENABLED:
            span.set_attribute("auth_result", "success")
        return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    with tracer.start_as_current_span("create_access_token") as span:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )

        if settings.TELEMETRY_ENABLED:
            span.set_attribute("token_expires", expire.isoformat())

        return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Get the current user from the token
    """
    with tracer.start_as_current_span("get_current_user") as span:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")

            if username is None:
                if settings.TELEMETRY_ENABLED:
                    span.set_attribute("validation_result", "no_username")
                raise credentials_exception

            token_data = TokenData(username=username)

            if settings.TELEMETRY_ENABLED:
                span.set_attribute("username", username)

        except JWTError:
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("validation_result", "jwt_error")
            raise credentials_exception

        user = get_user(token_data.username)

        if user is None:
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("validation_result", "user_not_found")
            raise credentials_exception

        if settings.TELEMETRY_ENABLED:
            span.set_attribute("validation_result", "success")

        return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Verify the user is active
    """
    with tracer.start_as_current_span("get_current_active_user") as span:
        if settings.TELEMETRY_ENABLED:
            span.set_attribute("username", current_user.username)

        if current_user.disabled:
            if settings.TELEMETRY_ENABLED:
                span.set_attribute("user_status", "disabled")
            raise HTTPException(status_code=400, detail="Inactive user")

        if settings.TELEMETRY_ENABLED:
            span.set_attribute("user_status", "active")

        return current_user


def user_to_response(user: UserInDB) -> UserResponse:
    """
    Convert a UserInDB to a UserResponse (removing sensitive data)
    """
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled
    )
