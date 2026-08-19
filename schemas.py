from pydantic import BaseModel, EmailStr
from models import Role


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Role = Role.recruiter


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: Role

    model_config = {"from_attributes": True}
