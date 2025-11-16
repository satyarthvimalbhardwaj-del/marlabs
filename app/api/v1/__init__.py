"""API v1 router aggregator."""
from fastapi import APIRouter
from app.api.v1 import auth, blogs, feature_requests, notifications, websockets

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(auth.router)
api_router.include_router(blogs.router)
api_router.include_router(feature_requests.router)
api_router.include_router(notifications.router)
api_router.include_router(websockets.router)
