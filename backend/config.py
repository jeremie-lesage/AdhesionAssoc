from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BREVO_API_KEY: str = "YOUR_API_V3_KEY"
    MAIL_FROM: str = "your-email@example.com"
    IBAN: str = "IBAN non configuré sur le serveur"
    BIC: str = "BIC non configuré sur le serveur"
    BANK: str = "BANK non configuré sur le serveur"
    POSTAL_CODE_PREFIX: str = "21"
    # Base des liens envoyés par email (reprise du formulaire). Sans slash final.
    PUBLIC_URL: str = "https://inscription.foyerruralfauverney.fr"
    # Âge à partir duquel un adhérent est compté comme adulte dans les
    # statistiques du tableau de bord (en dessous : enfant).
    ADULT_AGE_THRESHOLD: int = 16

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
