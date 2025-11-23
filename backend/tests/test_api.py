"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_db, drop_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database."""
    # Create tables
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)


class TestAuth:
    """Test authentication endpoints."""

    def test_register(self):
        """Test user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_login(self):
        """Test user login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


class TestJobs:
    """Test job endpoints."""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpassword123"},
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_create_job(self, auth_headers):
        """Test job creation."""
        response = client.post(
            "/api/v1/jobs",
            json={
                "title": "Senior Python Developer",
                "description": "Looking for an experienced Python developer with 5+ years of experience. Must have skills in Python, FastAPI, and Docker.",
                "company": "Tech Corp",
                "location": "Remote",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Senior Python Developer"
        assert "required_skills" in data

    def test_get_jobs(self, auth_headers):
        """Test getting jobs."""
        response = client.get("/api/v1/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestHealth:
    """Test health endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
