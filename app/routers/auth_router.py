from fastapi import APIRouter, Request, Depends

from app.services.auth_service import AuthService
from sqlalchemy.orm import Session
from app.database.setup import get_db

auth_router = APIRouter(prefix="/api/v1", tags=["Auth"])

def get_auth_service():
    return AuthService()


@auth_router.get("/google/login")
async def login_via_google(request: Request,
                           auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.redirect_login(request)


@auth_router.get("/google/callback")
async def google_auth_callback(request: Request,
                               db: Session = Depends(get_db),
                               auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.google_user_info(request, db)


