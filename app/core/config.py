from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    APP_VERSION: str = "0.1.0"
    BUILD_TIME: str = "local"

    class Config:
        env_file = ".env"


settings = Settings()
