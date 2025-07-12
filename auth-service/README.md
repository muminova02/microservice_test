# Auth Service

Authentication and Authorization service for the microservices platform.

## Features

- JWT Authentication
- User registration and management
- Token validation
- OpenTelemetry integration with Zipkin
- Docker deployment ready

## Project Structure

```
/auth-service
├── app/                # Application package
│   ├── __init__.py     # Package initializer
│   ├── main.py         # Application entrypoint
│   ├── config.py       # Configuration settings
│   ├── database.py     # Database operations
│   ├── models.py       # Pydantic data models
│   ├── security.py     # Security utilities
│   ├── telemetry.py    # OpenTelemetry integration
│   └── routers/        # API routes
│       ├── __init__.py # Package initializer
│       ├── auth.py     # Authentication endpoints
│       └── health.py   # Health check endpoint
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## API Endpoints

- `POST /auth/token` - OAuth2 compatible token login
- `POST /auth/register` - Register a new user
- `GET /auth/me` - Get current user information
- `GET /auth/validate` - Validate token
- `GET /health` - Health check endpoint

## Development

### Local Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker

Build and run with Docker:

```bash
docker build -t auth-service .
docker run -p 8000:8000 auth-service
```

## OpenTelemetry Integration

This service integrates with Zipkin for distributed tracing. To enable telemetry, set the `ZIPKIN_URL` environment variable:

```bash
export ZIPKIN_URL=http://zipkin:9411
```

## Configuration

Configuration is handled through environment variables:

- `SECRET_KEY` - Secret key for JWT encoding
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time in minutes
- `ZIPKIN_URL` - URL for Zipkin tracing server
- `LOG_LEVEL` - Logging level (debug, info, warning, error)
- `HOST` - Host to bind the server to
- `PORT` - Port to bind the server to
