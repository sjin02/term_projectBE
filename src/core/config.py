from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    APP_VERSION: str = "0.1.0"
    BUILD_TIME: str = "local"
    TMDB_API_KEY: str = ""
    TMDB_API_BASE: str = "https://api.themoviedb.org/3"
    GOOGLE_CLIENT_ID: str = ""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
