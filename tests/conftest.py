"""
Pytest configuration and fixtures.
Provides common test fixtures and setup.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.
    Creates all tables before test and drops them after.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database session override.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.USER,
        is_active=1
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("AdminPassword123"),
        role=UserRole.ADMIN,
        is_active=1
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_approver(db_session: AsyncSession) -> User:
    """Create a test approver user."""
    approver = User(
        email="approver@example.com",
        username="approveruser",
        hashed_password=get_password_hash("ApproverPassword123"),
        role=UserRole.L1_APPROVER,
        is_active=1
    )
    db_session.add(approver)
    await db_session.commit()
    await db_session.refresh(approver)
    return approver


@pytest.fixture
async def user_token(client: AsyncClient, test_user: User) -> str:
    """Get authentication token for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
async def admin_token(client: AsyncClient, test_admin: User) -> str:
    """Get authentication token for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
async def approver_token(client: AsyncClient, test_approver: User) -> str:
    """Get authentication token for approver user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "approver@example.com",
            "password": "ApproverPassword123"
        }
    )
    return response.json()["access_token"]
