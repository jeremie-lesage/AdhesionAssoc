from pydantic import BaseModel
from pydantic_settings import BaseSettings

class EmailSettings(BaseSettings):
    MAIL_USERNAME: str = "your-email@example.com"
    MAIL_PASSWORD: str = "your-password"
    MAIL_FROM: str = "your-email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = EmailSettings()
