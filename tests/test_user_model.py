import pytest
from sqlalchemy.exc import IntegrityError
from models import User, Role
from auth import hash_password


def test_create_user_defaults_to_recruiter(db):
    user = User(username="alice", email="alice@example.com", password_hash=hash_password("pass"))
    db.add(user)
    db.commit()
    assert user.id is not None
    assert user.role == Role.recruiter
    assert not user.is_admin


def test_create_admin(db):
    user = User(username="susan", email="susan@example.com", password_hash=hash_password("pass"), role=Role.admin)
    db.add(user)
    db.commit()
    assert user.role == Role.admin
    assert user.is_admin


def test_unique_username(db):
    db.add(User(username="alice", email="a1@example.com", password_hash="h1"))
    db.commit()
    db.add(User(username="alice", email="a2@example.com", password_hash="h2"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_unique_email(db):
    db.add(User(username="bob", email="same@example.com", password_hash="h1"))
    db.commit()
    db.add(User(username="charlie", email="same@example.com", password_hash="h2"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_password_not_stored_plain(db):
    pw = "supersecret"
    h = hash_password(pw)
    user = User(username="dave", email="dave@example.com", password_hash=h)
    db.add(user)
    db.commit()
    assert user.password_hash != pw
    assert user.password_hash == h
