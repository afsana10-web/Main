from pydantic import BaseModel, EmailStr
from app.models.user import RoleEnum


class LoginRequest(BaseModel):
    officer_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    officer_id: str
    email: EmailStr
    full_name: str
    password: str
    role: RoleEnum = RoleEnum.OFFICER


class UserOut(BaseModel):
    id: int
    officer_id: str
    email: EmailStr
    full_name: str
    role: RoleEnum
    is_active: bool

    class Config:
        from_attributes = True
