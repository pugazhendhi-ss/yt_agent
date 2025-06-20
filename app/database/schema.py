from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from .setup import Base  # Import Base from setup.py


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public'}  # Explicitly specify schema

    name = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    alias_id = Column(String(100), primary_key=True, nullable=False)
    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"



