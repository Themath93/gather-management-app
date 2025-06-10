from fastapi import APIRouter
from .endpoints import user, auth, group, attendance

api_router = APIRouter()
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])  # ← auth 등록
api_router.include_router(group.router, prefix="/groups", tags=["groups"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
