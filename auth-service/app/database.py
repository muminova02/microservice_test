from typing import Dict, Optional

from app.models import UserInDB
from app.telemetry import get_tracer

# In a real application, this would be a database connection
# For this example, we'll use an in-memory dictionary

# Setup
tracer = get_tracer()

# Demo user database
users_db: Dict[str, dict] = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # 'secret'
        "disabled": False,
    }
}


def get_user(username: str) -> Optional[UserInDB]:
    """
    Get a user from the database by username
    """
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("username", username)

        if username in users_db:
            user_dict = users_db[username]
            return UserInDB(**user_dict)

        return None


def create_user(user_data: dict) -> UserInDB:
    """
    Create a new user in the database
    """
    with tracer.start_as_current_span("create_user") as span:
        username = user_data["username"]
        span.set_attribute("username", username)

        # In a real implementation, this would save to a database
        users_db[username] = user_data

        # In a real implementation, this would publish an event to RabbitMQ
        # about new user registration

        return UserInDB(**user_data)


def user_exists(username: str) -> bool:
    """
    Check if a user exists
    """
    with tracer.start_as_current_span("user_exists") as span:
        span.set_attribute("username", username)
        return username in users_db
