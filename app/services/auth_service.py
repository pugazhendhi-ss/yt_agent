import os
from fastapi import Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.services.sql_service import SqlService

load_dotenv()
oauth = OAuth()

# Load from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BASE_URL = os.getenv("PROJECT_BASE_URL")
CHAT_UI_URL = os.getenv("CHAT_UI_URL")

# OAuth config
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)


def get_sql_service():
    return SqlService()



class AuthService:
    def __init__(self):
        self.redirect_uri = f"{BASE_URL}/api/v1/google/callback"
        self.google_userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"

    async def redirect_login(self, request: Request):
        # session_id = request.query_params.get("session_id")

        session_id = request.session.get("session_id")
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id

        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")
        # Store session_id in session or your DB
        request.session["oauth_session_id"] = session_id
        return await oauth.google.authorize_redirect(
            request,
            redirect_uri=self.redirect_uri,
            state=session_id
        )

    async def google_user_info(self, request: Request, db: Session):
        try:
            token = await oauth.google.authorize_access_token(request)
            response = await oauth.google.get(self.google_userinfo_url, token=token)
            user_info = response.json()

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"OAuth failed: {e}")

        session_id = request.query_params.get("state") or request.session.get("oauth_session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id in callback")

        email=user_info.get("email")
        name=user_info.get("name")

        sql_service = get_sql_service()
        sql_service.get_or_create(db=db, session_id=session_id, email=email, name=name)
        print(f"""User logged in:
                            NAME: {name}
                           EMAIL: {email}""")
        response = RedirectResponse(url=CHAT_UI_URL)
        response.set_cookie(key="user_name", value=name, max_age=3600, httponly=False)
        return response


















