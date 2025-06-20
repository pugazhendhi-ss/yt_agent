from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import uuid4
import redis
import json
from app.database.schema import User

# Redis setup
redis_client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
MAX_CACHE_KEYS = 30
CACHE_TTL_SECONDS = 1800  # 30 mins


class SqlService:
    """
    SQL Service with sync handling for database operations.
    """
    def get_or_create(self, db: Session, session_id: str, email: str|None = None, name: str|None = None):
        try:
            # Check Redis cache
            cached = redis_client.get(session_id)

            if cached and email:
                # Binding the inbetween login after few chats
                result = db.execute(select(User).where(User.email == email.lower())) # For already existed email
                user = result.scalars().first()
                if user:
                    return self._update_session_id_and_cache(user, session_id, db)

                result = db.execute(select(User).where(User.session_id == session_id))  # For already existed session_id
                user = result.scalars().first()
                if user:
                    return self._update_email_and_cache(user, email, name, db)

            if email:
                result = db.execute(select(User).where(User.email == email.lower())) # For already existed email
                user = result.scalars().first()
                if user:
                    return self._update_session_id_and_cache(user, session_id, db)

                # new email, create new row
                alias_id = str(uuid4())
                new_user = User(session_id=session_id, email=email, name=name, alias_id=alias_id)
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return self._cache_and_return(new_user)

            elif cached:
                return json.loads(cached)

            else:
                # No email provided and session_id not in cache
                result = db.execute(select(User).where(User.session_id == session_id))
                user = result.scalars().first()
                if user:
                    return self._cache_and_return(user)

                # No match, create with only session_id and alias_id
                alias_id = str(uuid4())
                new_user = User(session_id=session_id, alias_id=alias_id)
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return self._cache_and_return(new_user)

        except Exception as e:
            db.rollback()
            raise Exception(f"Database operation failed: {str(e)}")


    def _update_session_id_and_cache(self, user: User, new_session_id: str, db: Session):
        try:
            user.session_id = new_session_id
            db.add(user)
            db.commit()
            db.refresh(user)
            return self._cache_and_return(user)
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to update session_id: {str(e)}")


    def _update_email_and_cache(self, user: User, email_id: str, name: str, db: Session):
        try:
            user.email = email_id
            user.name = name
            db.add(user)
            db.commit()
            db.refresh(user)
            return self._cache_and_return(user)
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to update email_id: {str(e)}")

    def _cache_and_return(self, user: User):
        try:
            data = {
                "session_id": user.session_id,
                "email": user.email,
                "name": user.name,
                "alias_id": user.alias_id,
            }
            self._evict_if_needed()
            redis_client.set(user.session_id, json.dumps(data), ex=CACHE_TTL_SECONDS)
            return data
        except Exception as e:
            # If Redis fails, still return the data
            print(f"Redis cache failed: {e}")
            return {
                "session_id": user.session_id,
                "email": user.email,
                "name": user.name,
                "alias_id": user.alias_id,
            }

    def _evict_if_needed(self):
        try:
            # Get all keys with their last access time
            keys = redis_client.keys("*")
            if len(keys) >= MAX_CACHE_KEYS:
                # Get keys with their idle time (rough LRU approximation)
                key_idle_times = []
                for key in keys:
                    idle_time = redis_client.object("idletime", key)
                    if idle_time is not None:
                        key_idle_times.append((key, idle_time))

                if key_idle_times:
                    # Sort by idle time (highest = least recently used)
                    key_idle_times.sort(key=lambda x: x[1], reverse=True)
                    # Delete the least recently used key
                    redis_client.delete(key_idle_times[0][0])
                else:
                    # Fallback: delete first key if OBJECT IDLETIME fails
                    redis_client.delete(keys[0])
        except Exception as e:
            print(f"Cache eviction failed: {e}")

