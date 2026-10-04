from collections.abc import AsyncIterator
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncIterator[AsyncSession]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


import os
from app.core.config import settings

os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"
settings.OPENAI_API_KEY = "sk-test-dummy-key"


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, monkeypatch) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    monkeypatch.setattr("app.api.tasks.AsyncSessionLocal", TestSessionLocal)
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def auth_user(db_session: AsyncSession) -> tuple[User, dict[str, str]]:
    user = User(
        email="agent_tester@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Agent Tester",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


@pytest.fixture(autouse=True)
def offline_providers(monkeypatch):
    """Unit tests must never invoke paid providers or public search services."""
    from langchain_core.runnables import RunnableLambda
    from langchain_core.messages import AIMessage
    import app.agents.executor as executor
    import app.agents.planner as planner
    import app.agents.reflector as reflector
    import app.agents.supervisor as supervisor

    def unexpected_inference(_):
        raise AssertionError("Mock RunnableSequence.invoke before testing LLM output")

    def fake_llm(**kwargs):
        return RunnableLambda(unexpected_inference)

    for module in (executor, planner, reflector, supervisor):
        monkeypatch.setattr(module, "get_llm", fake_llm)
