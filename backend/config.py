from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_ACCOUNT_ID: str = ""

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    RESEND_API_KEY: str

    JWT_SECRET: str
    ADMIN_EMAIL: str

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    CHROMADB_PATH: str = "/data/chromadb"

    ENVIRONMENT: str = "development"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_TOPIC_CHARS: int = 500
    WS_AUTH_TIMEOUT_SECONDS: int = 10

    MAX_DEBATES_PER_HOUR: int = 5
    MAX_SIMULTANEOUS_DEBATES: int = 2
    MAX_DEBATES_PER_DAY: int = 20
    MAX_LOGIN_ATTEMPTS_PER_IP: int = 10
    LOGIN_ATTEMPT_WINDOW_MINUTES: int = 15

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v

    @field_validator("FRONTEND_URL", "BACKEND_URL")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://, got '{v}'")
        return v.rstrip("/")

    @model_validator(mode="after")
    def validate_jwt_secret_strength(self) -> "Settings":
        if len(self.JWT_SECRET) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [self.FRONTEND_URL]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()