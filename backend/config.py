from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BREVO_API_KEY: str = "YOUR_API_V3_KEY"
    MAIL_FROM: str = "your-email@example.com"
    IBAN: str = "IBAN non configuré sur le serveur"
    BIC: str = "BIC non configuré sur le serveur"
    BANK: str = "BANK non configuré sur le serveur"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
