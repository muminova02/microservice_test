from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import os
import logging

# OpenTelemetry imports - only for Zipkin
try:
    from opentelemetry import trace
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # OpenTelemetry setup with Zipkin only
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Configure Zipkin exporter
    zipkin_exporter = ZipkinExporter(
        endpoint=os.getenv("ZIPKIN_URL", "http://localhost:9411") + "/api/v2/spans",
        service_name="auth-service"
    )

    span_processor = BatchSpanProcessor(zipkin_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    TELEMETRY_ENABLED = True
except ImportError:
    # OpenTelemetry not available, create dummy tracer
    logging.warning("OpenTelemetry dependencies not found. Telemetry disabled.")
    TELEMETRY_ENABLED = False

    # Create dummy tracer for when OpenTelemetry is not available
    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()

    class DummySpan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_attribute(self, key, value):
            pass

    tracer = DummyTracer()

app = FastAPI(title="Auth Service", description="Authentication and Authorization Service")

# Auto-instrument FastAPI if OpenTelemetry is available
if TELEMETRY_ENABLED:
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    LoggingInstrumentor().instrument()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configs
SECRET_KEY = os.getenv("SECRET_KEY", "very-secret-key-should-be-in-env-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Fake users database for demo (real impl would use PostgreSQL)
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

# Helper functions with tracing
def verify_password(plain_password, hashed_password):
    with tracer.start_as_current_span("verify_password"):
        logger.info("Verifying password")
        return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    with tracer.start_as_current_span("get_password_hash"):
        logger.info("Hashing password")
        return pwd_context.hash(password)

def get_user(db, username: str):
    with tracer.start_as_current_span("get_user") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", username)
        logger.info(f"Getting user: {username}")
        if username in db:
            user_dict = db[username]
            return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    with tracer.start_as_current_span("authenticate_user") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", username)
        logger.info(f"Authenticating user: {username}")

        user = get_user(fake_db, username)
        if not user:
            logger.warning(f"User not found: {username}")
            if TELEMETRY_ENABLED:
                span.set_attribute("auth_result", "user_not_found")
            return False

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            if TELEMETRY_ENABLED:
                span.set_attribute("auth_result", "invalid_password")
            return False

        logger.info(f"User authenticated successfully: {username}")
        if TELEMETRY_ENABLED:
            span.set_attribute("auth_result", "success")
        return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    with tracer.start_as_current_span("create_access_token") as span:
        logger.info("Creating access token")
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        if TELEMETRY_ENABLED:
            span.set_attribute("token_expires", expire.isoformat())
        logger.info("Access token created successfully")
        return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    with tracer.start_as_current_span("get_current_user") as span:
        logger.info("Validating current user token")
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                logger.warning("Token validation failed: no username in token")
                if TELEMETRY_ENABLED:
                    span.set_attribute("validation_result", "no_username")
                raise credentials_exception
            token_data = TokenData(username=username)
            if TELEMETRY_ENABLED:
                span.set_attribute("username", username)
        except JWTError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            if TELEMETRY_ENABLED:
                span.set_attribute("validation_result", "jwt_error")
            raise credentials_exception

        user = get_user(fake_users_db, username=token_data.username)
        if user is None:
            logger.warning(f"User not found during token validation: {username}")
            if TELEMETRY_ENABLED:
                span.set_attribute("validation_result", "user_not_found")
            raise credentials_exception

        logger.info(f"Token validated successfully for user: {username}")
        if TELEMETRY_ENABLED:
            span.set_attribute("validation_result", "success")
        return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    with tracer.start_as_current_span("get_current_active_user") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", current_user.username)
        if current_user.disabled:
            logger.warning(f"Inactive user attempted access: {current_user.username}")
            if TELEMETRY_ENABLED:
                span.set_attribute("user_status", "disabled")
            raise HTTPException(status_code=400, detail="Inactive user")
        if TELEMETRY_ENABLED:
            span.set_attribute("user_status", "active")
        return current_user

# Endpoints
@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with tracer.start_as_current_span("login_for_access_token") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", form_data.username)
        logger.info(f"Login attempt for user: {form_data.username}")

        user = authenticate_user(fake_users_db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            if TELEMETRY_ENABLED:
                span.set_attribute("login_result", "failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        logger.info(f"Login successful for user: {form_data.username}")
        if TELEMETRY_ENABLED:
            span.set_attribute("login_result", "success")
        return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register")
async def register(username: str, email: str, password: str, full_name: str = None):
    with tracer.start_as_current_span("register_user") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", username)
            span.set_attribute("email", email)
        logger.info(f"Registration attempt for user: {username}")

        if username in fake_users_db:
            logger.warning(f"Registration failed - username already exists: {username}")
            if TELEMETRY_ENABLED:
                span.set_attribute("registration_result", "username_exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        hashed_password = get_password_hash(password)
        user_dict = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "disabled": False
        }
        fake_users_db[username] = user_dict

        # In real implementation, save to database and publish event to RabbitMQ
        # about new user registration

        logger.info(f"User registered successfully: {username}")
        if TELEMETRY_ENABLED:
            span.set_attribute("registration_result", "success")
        return {"message": "User registered successfully"}

@app.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    with tracer.start_as_current_span("read_users_me") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", current_user.username)
        logger.info(f"User info requested: {current_user.username}")
        return current_user

@app.get("/auth/validate")
async def validate_token(current_user: User = Depends(get_current_active_user)):
    with tracer.start_as_current_span("validate_token") as span:
        if TELEMETRY_ENABLED:
            span.set_attribute("username", current_user.username)
        logger.info(f"Token validation requested for user: {current_user.username}")
        return {"valid": True, "user": current_user}

@app.get("/health")
async def health_check():
    with tracer.start_as_current_span("health_check"):
        logger.info("Health check requested")
        return {"status": "healthy", "service": "auth-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)