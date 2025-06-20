from fastapi import APIRouter, Depends
from app.models.agent_model import ChatPayload
from fastapi import Request
from app.services.agent_service import Agent
from app.services.sql_service import SqlService
from sqlalchemy.orm import Session
from app.database.setup import get_db


agent_router = APIRouter(prefix='/api/v1', tags=["Agent"])

def get_agent():
    return Agent()

def get_sql_service():
    return SqlService()


@agent_router.post("/assistant")
def assistant(
        request: Request,
        query: str,
        agent_service: Agent = Depends(get_agent),
        sql_service: SqlService = Depends(get_sql_service),
        db: Session = Depends(get_db)
):
    print(f"User's query ---> {query}")

    session_id = request.session.get("session_id")

    if session_id:
        print(f"session ID from cookie: {session_id}")

    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        print(f"Newly generated session ID: {session_id}")


    session_info = sql_service.get_or_create(db, session_id)

    chat_payload = ChatPayload(id=session_id, query=query)

    chat_payload.id = session_info.get("alias_id")
    print(f"session_info: {session_info}")
    return agent_service.chat(chat_payload)



