"""
Pytest configuration and shared fixtures for JobHunter AI tests.
Uses SQLite in-memory DB; isolates each test via transaction rollback.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token

# ── Shared SQLite engine for the whole session ────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test_jobhunter.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Create all tables once per test session, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    import os, time
    db_file = "./test_jobhunter.db"
    for _ in range(3):
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
            break
        except PermissionError:
            time.sleep(0.5)


@pytest.fixture(scope="function")
def db():
    """
    Per-test DB session using SAVEPOINT for rollback isolation.
    The session is committed so app's override can read the data.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override app dependency to use this session
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def client(db):
    """HTTP test client — depends on db so the override is active."""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user(db):
    """Create a committed test user in the test DB."""
    from app.models.user import User, UserProfile, JobPreferences
    from app.core.security import hash_password

    # Remove any existing test user
    existing = db.query(User).filter(User.email == "test@jobhunter.ai").first()
    if existing:
        return existing

    user = User(
        email="test@jobhunter.ai",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_verified=True,
        onboarding_completed=True,
    )
    db.add(user)
    db.flush()

    db.add(UserProfile(
        user_id=user.id,
        technical_skills=["Python", "React", "FastAPI"],
        soft_skills=["Leadership", "Communication"],
        current_title="Senior Engineer",
        total_experience_years=5.0,
    ))
    db.add(JobPreferences(
        user_id=user.id,
        preferred_titles=["Software Engineer", "Staff Engineer"],
        remote_ok=True,
        full_time=True,
    ))
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Return Authorization headers for the test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_groq():
    """Mock all Groq _call_groq calls."""
    with patch("app.services.ai.groq_client._call_groq") as mock:
        mock.return_value = {
            "content": '{"result": "mocked_response", "score": 75}',
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "latency_ms": 200,
        }
        yield mock


@pytest.fixture
def mock_groq_resume():
    """Mock Groq resume analysis response."""
    with patch("app.services.ai.groq_client._call_groq") as mock:
        mock.return_value = {
            "content": """{
                "personal_info": {"name": "John Smith", "email": "john@example.com", "phone": null, "location": "NYC", "linkedin": null, "portfolio": null},
                "professional_summary": "Experienced software engineer with 5 years Python experience.",
                "experience": [
                    {"company": "Acme Corp", "title": "Senior Engineer", "start_date": "2020-01", "end_date": null, "is_current": true, "location": "Remote", "description": "Built APIs", "achievements": ["Led migration to microservices"]}
                ],
                "education": [{"institution": "MIT", "degree": "BS Computer Science", "field": "CS", "start_year": 2015, "end_year": 2019, "gpa": "3.8"}],
                "skills": {"technical": ["Python", "React", "PostgreSQL", "FastAPI"], "soft": ["Leadership", "Communication"]},
                "certifications": [],
                "projects": [{"name": "Open Source Project", "description": "A Python lib", "technologies": ["Python"], "url": "https://github.com/..."}],
                "achievements": ["Led team of 5 engineers", "Reduced API latency by 40%"],
                "keywords": ["Python", "API", "React", "PostgreSQL", "FastAPI"],
                "total_experience_years": 5,
                "quality_score": 78
            }""",
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 500,
            "completion_tokens": 300,
            "total_tokens": 800,
            "latency_ms": 1200,
        }
        yield mock
