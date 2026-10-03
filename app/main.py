import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, reflections, tasks
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        from sqlalchemy import select, text
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Automatic schema migration for existing PostgreSQL/SQLite deployments
            new_cols = [
                ("requires_approval", "BOOLEAN DEFAULT FALSE"),
                ("approval_status", "VARCHAR(50) DEFAULT 'none'"),
                ("token_cost", "FLOAT DEFAULT 0.0"),
                ("trace_id", "VARCHAR(64)"),
            ]
            for col_name, col_type in new_cols:
                try:
                    await conn.execute(text(f"ALTER TABLE tasks ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                except Exception:
                    try:
                        await conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                    except Exception:
                        pass
            try:
                await conn.execute(text("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'awaiting_approval'"))
                await conn.execute(text("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'rejected'"))
            except Exception:
                pass
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

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts_list)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(reflections.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/api/v1")
@app.get("/api/v1/")
async def api_v1_root() -> dict[str, str]:
    return {"message": f"{settings.APP_NAME} API v1", "status": "online", "docs": "/docs"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


from app.core.errors import ApexException


@app.exception_handler(ApexException)
async def apex_exception_handler(_: Request, exc: ApexException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    print(f"Server error on {request.url}: {error_trace}")
    content: dict = {"detail": str(exc)}
    if settings.DEBUG:
        content["trace"] = error_trace.splitlines()[-3:] if error_trace else []
    return JSONResponse(
        status_code=500,
        content=content,
    )
