from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import all_routers

app = FastAPI(title="Movie API", version=settings.APP_VERSION)

for r in all_routers:
    app.include_router(r)