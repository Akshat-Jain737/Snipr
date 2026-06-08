from datetime import timedelta,datetime, timezone
from http.client import HTTPResponse
import string
from urllib.parse import urlparse, urlunparse
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import HttpUrl
from sqlmodel import select
from Cashing import rdis
from DB.config import settings
from DB.models import Url
from UTILS.safe_browsing import is_safe
from DB.session import get_session
import dateparser

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def raiseEx(status, details):
    raise HTTPException(status_code=status, detail=details)

def normalize_url(url:str): # https(scheme)://www.example.com(netloc):443(port)
    # parsed.netloc  is "example.com:8080"
    # parsed.hostname is "example.com"

    parsed=urlparse(url)
    print(parsed)
    
    if not parsed.hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid URL: missing hostname')
        
    punycode_host = parsed.hostname.encode("idna").decode("ascii")
    if punycode_host!=parsed.hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='non verified url')
     
    scheme=parsed.scheme.lower()
    netloc=parsed.netloc.lower()
    port=parsed.port
    hostname=parsed.hostname

    if(scheme=='https' and port==443) or (scheme=='http' and port==80):
        netloc=hostname
    
    normalized = urlunparse((
        scheme,
        netloc,
        parsed.path or "/",
        "", # params
        parsed.query,
        ""  # remove fragment
    ))

    return normalized

base62=string.digits+string.ascii_lowercase+string.ascii_uppercase

def encode_base62(id:int):
    arr=[]
    if id==0:
        return base62[0]

    else:
        while(id>0):
            id,rem=divmod(id, 62)
            arr.append(base62[rem])
    
    arr.reverse()

    return ''.join(arr)
    
def decode_base62(encoded: str) -> int:
    num = 0
    for char in encoded:
        num = num * 62 + base62.index(char)
    return num

async def is_url_safe(id:int, session)->bool:
    status_redis = await rdis.get(f'safe:{id}')
    result = await session.exec(select(Url).where(Url.id==id))
    url_data = result.first()

    if url_data is None: # if 
        raiseEx(404, "URL not found")
    # >24hr
    if datetime.now() > url_data.last_checked+timedelta(days=1):
        result=await is_safe(url_data.long_url)
        if not result:
            url_data.status='UNSAFE'
            await rdis.set(f'safe:{id}', 'UNSAFE', ex=86400)
        
        else:
            url_data.status='SAFE'
            await rdis.set(f'safe:{id}', 'SAFE', ex=86400)

        url_data.last_checked=datetime.now()
        session.add(url_data)
        await session.commit()
        return result

    # <24hr
    else:
        if status_redis=='SAFE':
            return True
        # redis not available
        if status_redis is None:
            if url_data.status=='SAFE':
                await rdis.set(f'safe:{id}', 'SAFE', ex=86400)
                return True
            else:
                await rdis.set(f'safe:{id}', 'UNSAFE', ex=86400)
                return False
        else:
            await rdis.set(f'safe:{id}', 'UNSAFE', ex=86400)
            return False
        

def parse_expiry(text: str):
    dt = dateparser.parse(
        text,
        settings={
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        }
    )

    if not dt:
        raise ValueError("Invalid expiry date")

    now = datetime.now(timezone.utc)

    if dt <= now:
        raise ValueError("Expiry must be in the future")

    return dt

# --- Password & Token Utilities ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str, session = Depends(get_session)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        if user_id is None or session_id is None:
            raiseEx(status.HTTP_401_UNAUTHORIZED, "Invalid access token")
        return {"user_id": user_id, "session_id": session_id}
    except jwt.ExpiredSignatureError:
        raiseEx(status.HTTP_401_UNAUTHORIZED, "Access token has expired")
    except JWTError:
        raiseEx(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
