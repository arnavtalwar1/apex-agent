from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


db_url = settings.async_database_url
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
engine = create_async_engine(db_url, echo=settings.DEBUG, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
	pass


async def get_db() -> AsyncIterator[AsyncSession]:
	async with AsyncSessionLocal() as session:
		yield session
