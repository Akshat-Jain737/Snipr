import asyncio
# import random
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, Response, status, Request
from sqlmodel import Session, select
from jose import jwt, JWTError

from Cashing import rdis
from DB.config import settings
from DB.models import User, Sessions
from UTILS.utils import create_access_token, create_refresh_token, get_password_hash, raiseEx, verify_password
# from .email_services import Email


class AuthService:
    def __init__(self, session:Session):
        self.session=session

    async def register(self, email: str, password: str, response: Response):
        """
        Registers a new user, saves them to the database with is_verified=False,
        and returns access/refresh tokens.
        """
        # Check if user already exists
        result = await self.session.exec(select(User).where(User.email == email))
        existing_user = result.first()
        if existing_user:
            raiseEx(status.HTTP_400_BAD_REQUEST, "Email already registered")

        hashed_password = get_password_hash(password)

        new_user = User(email=email, hashed_password=hashed_password)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        # # Generate and store OTP
        # otp = "".join(random.choices("0123456789", k=6))
        # await rdis.set(f"otp:{email}", otp, ex=300)  # OTP expires in 5 minutes

        # # Send OTP email
        # await Email(email, otp)

        # Create tokens
        token_data = {"sub": str(new_user.id)}
        access_token = create_access_token(data=token_data, expires_delta=settings.access_token_expires)
        refresh_token = create_refresh_token(data=token_data, expires_delta=settings.refresh_token_expires)
        response.set_cookie(key="refresh_token", value=f"Bearer {refresh_token}", httponly=True)

        return {
            "message": "Registration successful.",
            "access_token": access_token
        }

    async def login(self, email: str, password: str, response: Response, request: Request):
        """
        Authenticates a user and returns new access/refresh tokens.
        """
        # Find user by email
        result = await self.session.exec(select(User).where(User.email == email))
        user = result.first()
        if not user:
            raiseEx(status.HTTP_404_NOT_FOUND, "User with this email does not exist")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raiseEx(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

        # Create a new session and tokens
        new_session = Sessions(
            user_id=user.id,
            device_info=request.headers.get("user-agent", "Unknown"),
            expires_at=datetime.now(timezone.utc) + settings.refresh_token_expires,
            refresh_token="" # Placeholder, will be updated below
        )
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)

        token_data = {"sub": str(user.id), "sid": str(new_session.session_id)}
        access_token = create_access_token(data=token_data, expires_delta=settings.access_token_expires)
        refresh_token = create_refresh_token(data=token_data, expires_delta=settings.refresh_token_expires)

        new_session.refresh_token = refresh_token # Update session with the actual token
        await self.session.commit()

        response.set_cookie(key="refresh_token", value=f"Bearer {refresh_token}", httponly=True)

        return {
            "message": "Login successful.",
            "access_token": access_token,
        }
    
    async def refresh_token(self, token: str, response: Response, request: Request):
        """
        Refreshes the access token using a valid refresh token, implementing token rotation.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            session_id_str = payload.get("sid")
            if user_id is None or session_id_str is None:
                raiseEx(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
            session_id = uuid.UUID(session_id_str)
        except JWTError:
            raiseEx(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")

        # Find the session
        session = await self.session.get(Sessions, session_id)
        if not session:
            raiseEx(status.HTTP_401_UNAUTHORIZED, "Session not found")
        
        # Validate the session
        # Make the stored datetime timezone-aware (it's stored in UTC) before comparing
        is_expired = session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)

        if session.is_revoked or is_expired or session.refresh_token != token:
            raiseEx(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
        
        # Revoke the old session
        session.is_revoked = True
        self.session.add(session)

        # Create a new session and tokens
        new_session = Sessions(
            user_id=int(user_id),
            device_info=request.headers.get("user-agent", "Unknown"),
            expires_at=datetime.now(timezone.utc) + settings.refresh_token_expires,
            refresh_token="" # Placeholder
        )
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)

        new_token_data = {"sub": str(user_id), "sid": str(new_session.session_id)}
        new_access_token = create_access_token(data=new_token_data, expires_delta=settings.access_token_expires)
        new_refresh_token = create_refresh_token(data=new_token_data, expires_delta=settings.refresh_token_expires)

        new_session.refresh_token = new_refresh_token # Update with the new token
        await self.session.commit()

        # Set the new refresh token in the cookie
        response.set_cookie(key="refresh_token", value=f"Bearer {new_refresh_token}", httponly=True)

        return {
            "message": "Token refreshed successfully.",
            "access_token": new_access_token
        }
    
    async def logout(self, token: str, response: Response):
        """
        Logs out the user by revoking their current session and clearing the cookie.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            session_id_str = payload.get("sid")
            if session_id_str is None:
                raiseEx(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
            session_id = uuid.UUID(session_id_str)
        except (JWTError, ValueError):
            # If the token is invalid for any reason, we can't find the session,
            # but we can still clear the cookie to log the user out on the client-side.
            response.delete_cookie(key="refresh_token")
            return {"message": "Logged out successfully"}

        session = await self.session.get(Sessions, session_id)
        if session and not session.is_revoked:
            session.is_revoked = True
            self.session.add(session)
            await self.session.commit()

        response.delete_cookie(key="refresh_token")
        return {"message": "Logged out successfully"}
    