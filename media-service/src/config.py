from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MINIO_URL: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str 
    MINIO_BUCKET_NAME: str
    MINIO_MAX_FILE_SIZE: int
    MINIO_COVER_ROOT: str

    POSTGRES_URL_MEDIA: str

    MAX_GET_SIZE: int
    DEFAULT_GET_SIZE: int

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

settings = Settings()