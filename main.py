import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.database.setup import Base, engine
from app.routers.agent_router import agent_router

load_dotenv()

Base.metadata.create_all(bind=engine)

MIDDLE_WARE_SECRET = os.getenv('MIDDLE_WARE_SECRET')

from  app.routers.auth_router import auth_router


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=MIDDLE_WARE_SECRET, max_age=3600)

app.include_router(agent_router)
app.include_router(auth_router)

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def serve_frontend(request: Request):
    response = templates.TemplateResponse("index.html", {"request": request})
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=7000)


