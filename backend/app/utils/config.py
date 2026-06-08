from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./career_copilot.db"
    PROJECT_NAME: str = "AI Career Copilot"
    API_V1_STR: str = "/api"

settings = Settings()
