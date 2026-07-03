import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    email: str = Field(..., env='EMAIL')
    app_password: str = Field(..., env='APP_PASSWORD')
    gemini_api_keys: str = Field(default="", env='GEMINI_API_KEYS')
    
    @property
    def get_gemini_api_keys_list(self) -> list[str]:
        if not self.gemini_api_keys:
            return []
        return [k.strip() for k in self.gemini_api_keys.split(',') if k.strip()]
    
    google_sheets_credentials_file: str = Field(default="credentials.json", env='GOOGLE_SHEETS_CREDENTIALS_FILE')
    google_sheets_workbook_name: str = Field(default="JobHunterData", env='GOOGLE_SHEETS_WORKBOOK_NAME')
    
    timezone: str = Field(default="Asia/Kolkata", env='TIMEZONE')
    schedule_time: str = Field(default="19:00", env='SCHEDULE_TIME')
    max_jobs_per_source: int = Field(default=10, env='MAX_JOBS_PER_SOURCE')
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
