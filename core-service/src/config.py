from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    POSTGRES_URL_CORE: str
    MAX_GET_SIZE: int
    DEFAULT_GET_SIZE: int

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    INACTIVE_REFRESH_TOKEN_LIFETIME_DAYS: int

    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

settings = Settings()