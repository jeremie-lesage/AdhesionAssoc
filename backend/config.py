from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAIL_USERNAME: str = "your-email@example.com"
    MAIL_PASSWORD: str = "your-password"
    MAIL_FROM: str = "your-email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    IBAN: str = "IBAN non configuré sur le serveur"
    BIC: str = "BIC non configuré sur le serveur"
    BANK: str = "BANK non configuré sur le serveur"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
