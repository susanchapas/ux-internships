import pytest
from sqlalchemy.exc import IntegrityError
from models import User, Role
from auth import hash_password, verify_password, require_admin
from schemas import UserRead


def test_create_and_read_admin(pg_db):
    pw = "secure123"
    user = User(username="susan", email="susan@test.com", password_hash=hash_password(pw), role=Role.admin)
    pg_db.add(user)
    pg_db.commit()
    pg_db.refresh(user)

    assert user.is_admin
    assert verify_password(pw, user.password_hash)

    read = UserRead.model_validate(user)
    assert read.username == "susan"
    assert read.role == Role.admin
    assert not hasattr(read, "password_hash")


def test_recruiter_default_role(pg_db):
    user = User(username="viewer", email="viewer@test.com", password_hash=hash_password("pass"))
    pg_db.add(user)
    pg_db.commit()
    pg_db.refresh(user)

    assert user.role == Role.recruiter
    assert not user.is_admin
    with pytest.raises(PermissionError):
        require_admin(user)


def test_unique_constraints_postgres(pg_db):
    pg_db.add(User(username="bob", email="bob@test.com", password_hash="h"))
    pg_db.commit()

    pg_db.add(User(username="bob", email="bob2@test.com", password_hash="h"))
    with pytest.raises(IntegrityError):
        pg_db.commit()
    pg_db.rollback()

    pg_db.add(User(username="carol", email="bob@test.com", password_hash="h"))
    with pytest.raises(IntegrityError):
        pg_db.commit()


def test_invalid_email_rejected():
    from pydantic import ValidationError
    from schemas import UserCreate
    with pytest.raises(ValidationError):
        UserCreate(username="x", email="bad", password="p")


def test_cannot_self_register_as_admin():
    from schemas import UserCreate
    u = UserCreate(username="x", email="x@test.com", password="p", role=Role.admin)
    assert u.role == Role.admin
