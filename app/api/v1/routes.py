from fastapi import APIRouter
from app.api.v1.file_parser_api import file_upload_router
from app.api.v1.tea_pot_api import tea_pot_router

v1_router = APIRouter()
v1_router.include_router(router=file_upload_router)
v1_router.include_router(router=tea_pot_router)
