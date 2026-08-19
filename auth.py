import secrets
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pathlib import Path
from models import Base, User, Role

DB_PATH = Path(__file__).parent / "data.db"
_engine = None
_sessions = {}


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}")
        Base.metadata.create_all(_engine)
    return _engine


def get_db():
    return Session(get_engine())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def require_admin(user) -> None:
    if user.role != Role.admin:
        raise PermissionError("Admin access required")


def register_user(username: str, email: str, password: str, role: Role = Role.recruiter) -> User:
    with get_db() as session:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def login_user(username: str, password: str) -> tuple[User, str] | None:
    with get_db() as session:
        user = session.query(User).filter_by(username=username).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        token = secrets.token_urlsafe(32)
        _sessions[token] = user.id
        session.expunge(user)
        return user, token


def get_current_user(token: str) -> User | None:
    user_id = _sessions.get(token)
    if user_id is None:
        return None
    with get_db() as session:
        user = session.get(User, user_id)
        if user:
            session.expunge(user)
        return user


def logout(token: str) -> None:
    _sessions.pop(token, None)
