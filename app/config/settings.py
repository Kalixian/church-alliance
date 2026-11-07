from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: Optional[str] = None

    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None

    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    cloudinary_upload_folder: str = "church-alliance/pictures"
    # Unconfirmed direct uploads older than this are removed by `python -m app.storage.cleanup`.
    cloudinary_pending_upload_ttl_hours: int = 24

    # Contact Us form (POST /api/v1/contact): SMTP account used to email each
    # administrator. Same meaning (and env var names) as the static site's
    # deploy/contact.ini keys; recipients come from the database, not settings.
    contact_smtp_host: str = "smtp.gmail.com"
    contact_smtp_port: int = 587
    contact_smtp_user: Optional[str] = None
    contact_smtp_password: Optional[str] = None
    contact_sender: Optional[str] = None
    contact_sender_name: str = "Church Alliance Website"

    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
