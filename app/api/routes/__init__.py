from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.contents import router as contents_router
from app.api.routes.admin import router as admin_router
from app.api.routes.genres import router as genres_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.bookmarks import router as bookmarks_router

all_routers = [health_router, auth_router, users_router, admin_router, contents_router, genres_router, reviews_router, bookmarks_router]
