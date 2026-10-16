from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend folder (where .env is located)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Application Settings
    Loads configuration values from environment variables or the .env file.
    This keeps sensitive data (like secret keys and credentials) out of the codebase.
    """
    PROJECT_NAME: str = "TaskFlow - Smart Task Management System"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database Settings (Will be used in the next step)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "taskflow_db"

    # JWT Authentication Settings (Will be used in the auth step)
    JWT_SECRET_KEY: str = "default_insecure_key_change_in_env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def DATABASE_URL(self) -> str:
        """
        Constructs the SQLAlchemy database URL.
        Uses quote_plus so special characters in DB_PASSWORD (e.g. '@', '%') are properly escaped.
        """
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{self.DB_USER}:{encoded_password}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate settings as a singleton to use across the application
settings = Settings()
