import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the project root is importable
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.db.base import Base
from app.main import app
from app.db.database import get_db
from app.config import settings
from app.storage import (
    StorageUnavailableError,
    StoredImage,
    UploadSignature,
    UploadVerificationError,
    get_image_storage,
)


class FakeImageStorage:
    """In-memory stand-in for CloudinaryImageStorage."""

    def __init__(self):
        self.confirmed: list[str] = []
        self.deleted: list[str] = []
        self.fail_deletes = False

    @staticmethod
    def signature_for(public_id: str, version: int) -> str:
        return f"signed:{public_id}:{version}"

    def create_upload_signature(self) -> UploadSignature:
        return UploadSignature(upload_url="https://upload.example.test", fields={"signature": "upload-signature"})

    def verify_upload(self, public_id: str, version: int, signature: str) -> StoredImage:
        if signature != self.signature_for(public_id, version):
            raise UploadVerificationError("Upload signature is invalid")
        return StoredImage(public_id=public_id, url=f"https://images.example.test/v{version}/{public_id}")

    def confirm(self, public_id: str) -> None:
        self.confirmed.append(public_id)

    def delete(self, public_ids) -> None:
        if self.fail_deletes:
            raise StorageUnavailableError("Could not delete images from Cloudinary")
        self.deleted.extend(public_ids)


engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def image_storage():
    return FakeImageStorage()


@pytest.fixture()
def client(db_session, image_storage, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_image_storage] = lambda: image_storage
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", "test-secret-key-for-testing")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    return settings
