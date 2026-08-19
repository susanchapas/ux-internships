import pytest
from pydantic import ValidationError
from schemas import UserCreate, UserRead
from models import Role


def test_user_create_valid():
    u = UserCreate(username="alice", email="alice@example.com", password="pass123")
    assert u.username == "alice"
    assert u.email == "alice@example.com"
    assert u.role == Role.recruiter


def test_user_create_admin():
    u = UserCreate(username="susan", email="susan@example.com", password="pass", role=Role.admin)
    assert u.role == Role.admin


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(username="alice", email="not-an-email", password="pass123")


def test_user_create_missing_fields():
    with pytest.raises(ValidationError):
        UserCreate(username="alice")


def test_user_read_from_attributes():
    class FakeUser:
        id = 1
        username = "alice"
        email = "alice@example.com"
        role = Role.recruiter

    u = UserRead.model_validate(FakeUser())
    assert u.id == 1
    assert u.username == "alice"
    assert u.role == Role.recruiter


def test_user_read_includes_role():
    class FakeAdmin:
        id = 2
        username = "susan"
        email = "susan@example.com"
        role = Role.admin

    u = UserRead.model_validate(FakeAdmin())
    assert u.role == Role.admin
