from fastapi import APIRouter, Cookie, Depends, Response, status, HTTPException, Request
from pydantic import EmailStr

from SCHEMA.auth_schema import UserCreateSchema, UserLoginSchema
from DB.dependencies import AuthDep

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreateSchema, auth_service: AuthDep, response: Response):
    return await auth_service.register(email=user_data.email, password=user_data.password, response=response)


@auth_router.post("/login")
async def login_user(user_data: UserLoginSchema, auth_service: AuthDep, response: Response, request: Request):
    return await auth_service.login(email=user_data.email, password=user_data.password, response=response, request=request)


@auth_router.post("/refresh")
async def refresh_access_token(
    response: Response,
    request: Request,
    auth_service: AuthDep,
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token or not refresh_token.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing refresh token")
    token = refresh_token.split(" ")[1]
    return await auth_service.refresh_token(token=token, response=response, request=request)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    response: Response,
    auth_service: AuthDep,
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token or not refresh_token.startswith("Bearer "):
        # If there's no token, the user is already effectively logged out.
        return {"message": "No active session to log out from."}
    token = refresh_token.split(" ")[1]
    return await auth_service.logout(token=token, response=response)