from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    MINIO_URL: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME_CORE: str
    MINIO_MAX_FILE_SIZE: int

    POSTGRES_URL_CORE: str
    MAX_GET_SIZE: int
    DEFAULT_GET_SIZE: int

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    INACTIVE_REFRESH_TOKEN_LIFETIME_DAYS: int

    SUPERUSER_USERNAME: str
    SUPERUSER_EMAIL: str
    SUPERUSER_PASSWORD: str
    SUPERUSER_AUTO_CREATE: bool

    USER_HISTORY_LIFETIME_DAYS: int

    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

settings = Settings()