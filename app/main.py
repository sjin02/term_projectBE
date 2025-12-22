from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import all_routers
from app.core.logging import setup_logging

from app.middlewares.logging import logging_middleware
from fastapi import HTTPException
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
)


app = FastAPI(title="Movie API", version=settings.APP_VERSION)

app.middleware("http")(logging_middleware)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.on_event("startup")
def on_startup():
    setup_logging("INFO")

for r in all_routers:
    app.include_router(r)