from fastapi import APIRouter
from api.endpoints import db

router = APIRouter()

router.include_router(db.router, prefix="/db", tags=['db'])