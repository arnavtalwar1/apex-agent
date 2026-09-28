from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api import auth, reflections, tasks
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.core.security import get_password_hash
        from app.models.user import User

        async with AsyncSessionLocal() as session:
            existing = (await session.execute(select(User).where(User.email == "test@example.com"))).scalar_one_or_none()
            if not existing:
                session.add(User(
                    email="test@example.com",
                    hashed_password=get_password_hash("password123"),
                    full_name="Demo User",
                ))
                await session.commit()
    except Exception as err:
        print(f"Database initialization warning: {err}")
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

origins = settings.origins_list
if "*" in origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

hosts = settings.hosts_list
if "*" in hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )
else:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=hosts,
    )

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(reflections.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
