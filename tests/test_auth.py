import pytest
from auth import hash_password, verify_password, require_admin, register_user, login_user, get_current_user, logout, _sessions, get_engine
from models import User, Role, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def clean_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def auth_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("auth._engine", engine)
    return engine


def test_hash_returns_string():
    h = hash_password("secret123")
    assert isinstance(h, str)
    assert h != "secret123"


def test_verify_correct_password():
    h = hash_password("mypassword")
    assert verify_password("mypassword", h)


def test_verify_wrong_password():
    h = hash_password("mypassword")
    assert not verify_password("wrongpassword", h)


def test_different_hashes_for_same_password():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2
    assert verify_password("same", h1)
    assert verify_password("same", h2)


def test_require_admin_passes_for_admin(db):
    user = User(username="susan", email="s@example.com", password_hash="h", role=Role.admin)
    db.add(user)
    db.commit()
    require_admin(user)


def test_require_admin_rejects_recruiter(db):
    user = User(username="recruiter", email="r@example.com", password_hash="h", role=Role.recruiter)
    db.add(user)
    db.commit()
    with pytest.raises(PermissionError):
        require_admin(user)


def test_register_user(auth_db):
    user = register_user("alice", "alice@example.com", "pass123")
    assert user.username == "alice"
    assert user.role == Role.recruiter
    assert user.password_hash != "pass123"


def test_register_admin(auth_db):
    user = register_user("susan", "susan@example.com", "pass", role=Role.admin)
    assert user.role == Role.admin
    assert user.is_admin


def test_register_duplicate_username(auth_db):
    register_user("alice", "a1@example.com", "pass")
    with pytest.raises(Exception):
        register_user("alice", "a2@example.com", "pass")


def test_login_success(auth_db):
    register_user("alice", "alice@example.com", "pass123")
    result = login_user("alice", "pass123")
    assert result is not None
    user, token = result
    assert user.username == "alice"
    assert len(token) > 0


def test_login_wrong_password(auth_db):
    register_user("alice", "alice@example.com", "pass123")
    assert login_user("alice", "wrong") is None


def test_login_nonexistent_user(auth_db):
    assert login_user("nobody", "pass") is None


def test_session_flow(auth_db):
    register_user("alice", "alice@example.com", "pass")
    _, token = login_user("alice", "pass")
    user = get_current_user(token)
    assert user is not None
    assert user.username == "alice"
    logout(token)
    assert get_current_user(token) is None
