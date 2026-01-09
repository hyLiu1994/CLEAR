# app/api/v1/router.py
from fastapi import APIRouter

from . import trajectory, sdkg, vista, update

api_router = APIRouter()

api_router.include_router(trajectory.router)
api_router.include_router(sdkg.router)
api_router.include_router(vista.router)
api_router.include_router(update.router)