import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.api.applications import router as applications_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("credit_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Приложение запускается...")
    yield
    log.info("Приложение останавливается...")


app = FastAPI(title="Credit Decision Agent", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    log.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.1f}ms)")
    return response


app.include_router(applications_router)


@app.get("/health")
async def health():
    return {"status": "ok"}