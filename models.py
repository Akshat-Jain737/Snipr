from datetime import datetime

from sqlmodel import SQLModel, Field

class Url(SQLModel,table=True):
    id:int|None=Field(primary_key=True, default=None)
    long_url:str
    short_url:str|None=Field(default=None)
    last_checked:datetime|None 
    status:str|None
    expiry_time:datetime|None

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
