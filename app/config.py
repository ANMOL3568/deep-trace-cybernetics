from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    # An explicit URL remains supported for Docker, CI and SQLite previews.
    database_url: str = Field(default='', repr=False)
    db_host: str = 'localhost'
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = 'DeepTrace'
    db_user: str = 'postgres'
    db_password: str = Field(default='', repr=False)
    jwt_secret: str = Field(min_length=32)
    cors_origins: list[str] = ['http://localhost:5173']
    access_token_minutes: int = Field(default=30, ge=1, le=1440)
    seed_password: str = Field(default='DemoPassword123!', min_length=12)

    @model_validator(mode='after')
    def build_database_url(self):
        if not self.database_url.strip():
            self.database_url = URL.create(
                'postgresql+psycopg', username=self.db_user,
                password=self.db_password, host=self.db_host,
                port=self.db_port, database=self.db_name,
            ).render_as_string(hide_password=False)
        return self


settings = Settings()
