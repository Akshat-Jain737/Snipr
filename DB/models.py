import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    urls: list["Url"] = Relationship(back_populates="user")
    sessions: list["Sessions"] = Relationship(back_populates="user")


class Sessions(SQLModel, table=True):
    session_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    refresh_token: str = Field(index=True)
    device_info: str | None = None
    is_revoked: bool = Field(default=False)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: User = Relationship(back_populates="sessions")


class Url(SQLModel,table=True):
    id:int|None=Field(primary_key=True, default=None)
    long_url:str
    user_id: int | None = Field(default=None, foreign_key="user.id")
    short_key:str|None=Field(default=None)
    last_checked:datetime|None 
    status:str|None
    expiry_time:datetime|None
    user: User | None = Relationship(back_populates="urls")


class Analytics(SQLModel, table=True):
    id:int|None=Field(primary_key=True, default=None)
    short_url:str
    total_clicks:int=Field(default=0)
    unique_clicks:int=Field(default=0)

class Analytics_2(SQLModel,table=True):
    id:int|None=Field(primary_key=True, default=None)
    short_url:str
    country:str
    region:str
    city:str
    browser:str
    os:str
    device:str
    total_clicks:int
    unique_clicks:int

class UTMAnalytics(SQLModel,table=True):
    id:int|None=Field(primary_key=True, default=None)
    long_url:str
    utm_source:str|None=Field(default=None) 
    utm_medium:str|None=Field(default=None)
    utm_capaign:str|None=Field(default=None) 
    utm_content:str|None=Field(default=None) 
