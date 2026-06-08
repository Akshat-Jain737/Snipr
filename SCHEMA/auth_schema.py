from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str