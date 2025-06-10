import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from db.init_db import init_db
from db.session import AsyncSessionLocal
from models.user import User, GenderEnum
from sqlalchemy import text


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    if os.path.exists("app.db"):
        os.remove("app.db")
    await init_db()
    yield
    if os.path.exists("app.db"):
        os.remove("app.db")


@pytest_asyncio.fixture(autouse=True)
async def clear_users():
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM users"))
        await session.commit()
    yield


async def create_user(email: str, password: str):
    async with AsyncSessionLocal() as session:
        user = User(
            username="testuser",
            email=email,
            password=password,
            gender=GenderEnum.male,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.mark.asyncio
async def test_login_success(setup_database):
    user = await create_user("valid@example.com", "secret")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"email": user.email, "password": "secret"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["id"] == user.id
    assert data["username"] == user.username


@pytest.mark.asyncio
async def test_login_invalid_credentials(setup_database):
    await create_user("valid@example.com", "secret")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"email": "valid@example.com", "password": "wrong"},
        )
    assert response.status_code == 401
