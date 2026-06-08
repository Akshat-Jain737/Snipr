import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from DB.session import get_session
from SERVICES.auth_services import AuthService
from SERVICES.url_services import URL_Services
from DB.models import Sessions, User
from UTILS.utils import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_url_services(session: Session = Depends(get_session)) -> URL_Services:
    return URL_Services(session=session)

def get_auth_services(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(session=session)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    token_data = decode_access_token(token, session)
    user = await session.get(User, int(token_data["user_id"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    try:
        session_uuid = uuid.UUID(token_data["session_id"])
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session ID format")
    db_session = await session.get(Sessions, session_uuid)
    if not db_session or db_session.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked")
    return user

UrlDep = Annotated[URL_Services, Depends(get_url_services)]
AuthDep = Annotated[AuthService, Depends(get_auth_services)]
CurrentUser = Annotated[User, Depends(get_current_user)]
