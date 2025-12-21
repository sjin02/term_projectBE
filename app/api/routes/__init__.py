from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.contents import router as contents_router

all_routers = [health_router, auth_router, users_router, contents_router]
