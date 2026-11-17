import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .config import get_settings
from .database import Base, engine
from .migrations import run_lightweight_migrations
from .routers import (
    auth_router,
    incidents,
    objects,
    response_logs,
    response_measures,
    staff,
    vulnerabilities,
    vulnerability_types,
)

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("security_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations(engine)
    logger.info("Приложение запущено, таблицы БД проверены/созданы.")
    yield


app = FastAPI(
    title="School Security Incident Management API",
    description=(
        "REST API для предметной области «Безопасность образовательного "
        "учреждения»: сотрудники, объекты (помещения/корпуса), инциденты, "
        "уязвимости, меры и журнал реагирования."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(IntegrityError)
def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("IntegrityError на %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Нарушено ограничение целостности базы данных"},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Необработанная ошибка на %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера. Пожалуйста, обратитесь к администратору."},
    )

@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "security-incident-api"}


app.include_router(auth_router.router)
app.include_router(objects.router)
app.include_router(staff.router)
app.include_router(vulnerability_types.router)
app.include_router(response_measures.router)
app.include_router(incidents.router)
app.include_router(vulnerabilities.router)
app.include_router(response_logs.router)
