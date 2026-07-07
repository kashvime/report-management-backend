# Reads env vars from .env and makes them available to app as a settings object.
# Any time the app needs configuration details, it imports it from here. 

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    DATABASE_URL: str
    
    # Root directory for uploaded dataset files; tests point this at a temp dir.
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(env_file=".env")  # tells Pydantic which file to find the variables from

# create an instance that app uses (import settings)
settings = Settings()
 