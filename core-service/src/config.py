from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    POSTGRES_URL_CORE: str
    MAX_GET_SIZE: int
    DEFAULT_GET_SIZE: int

    JWT_SECRET_KEY: str

    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

settings = Settings()