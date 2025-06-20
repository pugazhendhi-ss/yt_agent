from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv('YT_DATABASE_URL')

# Create sync engine
engine = create_engine(DATABASE_URL, echo=False)

# Create sync session maker
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Sync dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


