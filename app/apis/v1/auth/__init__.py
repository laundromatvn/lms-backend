from fastapi import APIRouter

from app.apis.v1.auth import customer


router = APIRouter(prefix="/auth")

router.include_router(customer.router)
