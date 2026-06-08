import json
import time
from alembic.util import status
from fastapi import APIRouter, Depends, FastAPI, Query, Request, Response, BackgroundTasks
from httpx import URL
from ai import suggest_keys
from analytics import clicks_background
from DB.session import get_session
from sqlmodel import Session, select
from SCHEMA.url_schema import UTM, UpdateURLPayload, urlscheme
from DB.dependencies import CurrentUser, UrlDep
from Cashing import rdis, rate_limit
url=APIRouter(prefix='/snipr', tags=["URL"])

@url.post('/shorten',dependencies=[Depends(rate_limit)])

async def shorten_url(url_service: UrlDep,long_url:urlscheme,bg_task:BackgroundTasks, current_user: CurrentUser, utm:UTM=Depends()):
   utm_dict = utm.model_dump(exclude_none=True)
   # 2. Build the full HTTP URL safely
   base_url = URL(str(long_url.long_url))
   http_url = str(base_url.copy_merge_params(utm_dict))  
   bg_task.add_task(url_service.utm_analytics(utm, http_url))
   return await url_service.short_url(http_url, long_url.custom_alias, long_url.expiry_time, current_user.id)

@url.get("/{custom_alias}/{short_key}/qr")
def QR_Code(custom_alias: str, short_key: str, request: Request, url_service: UrlDep):
   short_url = f"{request.base_url}snipr/{custom_alias}/{short_key}"
   return url_service.qr_code(short_url)

@url.get("/{custom_alias}/{short_key}/analytics")
def get_url_analytics(custom_alias: str, short_key: str, request: Request, url_service: UrlDep, current_user: CurrentUser):
   short_url = f"{request.base_url}snipr/{custom_alias}/{short_key}"
   return url_service.get_analytics(short_url, current_user.id)

@url.get('/{custom_alias}/{short_key}') # url/mac.b/3
async def redirect(url_service: UrlDep, short_key: str, request: Request, custom_alias: str, background_tasks: BackgroundTasks):
   start_time = time.perf_counter()
   short_url = f"{request.base_url}snipr/{custom_alias}/{short_key}"
   redirect_response = await url_service.redirect(short_key)
   
   all_visited_url = request.cookies.get("visited_url")
   visited_url = set()
   if all_visited_url:
      try:
         visited_url = set(json.loads(all_visited_url))
      except json.JSONDecodeError:
         pass
         
   is_unique = short_url not in visited_url
   if is_unique:
      visited_url.add(short_url)
      redirect_response.set_cookie(
         key="visited_url",
         value=json.dumps(list(visited_url)),
         httponly=False,
         max_age=60*60*24*365  # 1 year
      )

   ip_address = request.client.host if request.client else "Unknown"
   user_agent = request.headers.get("user-agent", "Unknown")
   background_tasks.add_task(clicks_background, short_url, is_unique, ip_address, user_agent)
   
   print(f"Redirect response time: {(time.perf_counter() - start_time) * 1000:.2f} ms")
   return redirect_response

# @url.get("/custom_key")
# def get_custom_key(url:str, current_user: CurrentUser, session: Session = Depends(get_session)):
#     return suggest_keys(url, set(), session=session)

# @url.get("/redis-dump")
# def dump_redis():
#     # Fetch all keys
#     all_keys = rdis.keys('*')
    
#     # Build a dictionary of all keys and their actual values
#     database_dump = {}
#     for key in all_keys:
#         database_dump[key] = rdis.get(key)
#     return {"total_keys": len(all_keys), "data": database_dump}

@url.get("/all-urls")
def get_all_urls(request: Request, url_service: UrlDep, current_user: CurrentUser):
    return url_service.get_all_urls(str(request.base_url), current_user.id)

@url.patch("/{short_key}")
async def update_short_url(
    short_key: str,
    payload: UpdateURLPayload,
    url_service: UrlDep,
    current_user: CurrentUser
):
    return await url_service.update_url(short_key=short_key, expiry_time=payload.expiry_time, user_id=current_user.id)

@url.delete("/{short_key}")
async def delete_short_url(short_key: str, url_service: UrlDep, current_user: CurrentUser):
    return await url_service.delete_url(short_key=short_key, user_id=current_user.id)