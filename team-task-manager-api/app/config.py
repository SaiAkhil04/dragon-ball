"""Minimal environment-based application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./task_manager.db")
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "local-development-only-change-this-secret-before-deploying"
)
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
JWT_ALGORITHM = "HS256"
