import io
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi.responses import RedirectResponse, StreamingResponse
import qrcode
from sqlmodel import Session, select
import string
from fastapi import HTTPException, status
from pydantic import HttpUrl
from SCHEMA.url_schema import UTM, urlscheme
from Cashing import rdis
from DB.models import UTMAnalytics, Url, Analytics, Analytics_2
from UTILS.safe_browsing import is_safe
from UTILS.utils import decode_base62, encode_base62, normalize_url, parse_expiry, raiseEx, is_url_safe

class URL_Services:
    def __init__(self, session:Session):
        self.session=session
    
    async def _add(self,obj):
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

    async def short_url(self, long_url:str, custom_alias:str, expiry_time:str|None, user_id: int):

        is_valid_url=normalize_url(long_url)

        is_available=await self.session.exec(select(Url).where(Url.long_url==is_valid_url)).first()

        if is_available:
            raiseEx(status.HTTP_400_BAD_REQUEST, 'url already exists')

        result=await is_safe(is_valid_url)

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Unsafe URL detected,can't shorten it",
            )
        
        # if safe
        if expiry_time:
            exp=parse_expiry(expiry_time)
        else:
            exp=None

        new_url=Url(long_url=is_valid_url, last_checked=datetime.now(), status='SAFE', expiry_time=exp, user_id=user_id)
        await self._add(new_url)
        short_code=encode_base62(new_url.id)


        cache_key=f'safe:{new_url.id}'
        rdis.set(cache_key, 'SAFE', ex=86400) # 24 hrs
        
        short_url=f'localhost:8000/snipr/{custom_alias}/{short_code}'
        return {"url": short_url, 'expiry_time': exp.strftime("%b %-d, %Y, %-I:%M %p") if exp else None}
    
#-----------------------------------------------------------------------------#

    async def redirect(self, short_key):
        try:
            id=decode_base62(short_key)
        except Exception:
            raiseEx(404, "wrong")

        is_safe_url = await is_url_safe(id, self.session) 
        if not is_safe_url:
            raise HTTPException(
                status_code=400,
                detail="Unsafe URL detected",
            )

        is_Rdis = await rdis.get(f'URL:{id}')

        url_long = is_Rdis

        if url_long is None: # redis None --> DB
            url_data = await self.session.exec(select(Url).where(Url.id==id)).first()

            if url_data is not None:
                now_utc = datetime.now(timezone.utc)
                if url_data.expiry_time is not None and url_data.expiry_time.replace(tzinfo=timezone.utc) < now_utc:
                    raiseEx(404, "link expired")
                else:  
                    url_long = url_data.long_url
                    cache_ttl=3600
                    if url_data.expiry_time is not None:
                        time_left = int((url_data.expiry_time.replace(tzinfo=timezone.utc) - now_utc).total_seconds())
                        if time_left > 0:
                            cache_ttl = min(3600, time_left)        
                    rdis.set(f'URL:{id}', url_long, ex=cache_ttl)

        return RedirectResponse(
            url=url_long,
            status_code=302
        )


    def qr_code(self,short_link):
        qr = qrcode.make(short_link)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="image/png"
        )

    async def get_analytics(self, short_url: str, user_id: int):
        basic_analytics = await  self.session.exec(
            select(Analytics).where(Analytics.short_url == short_url)
        ).first()

        if not basic_analytics:
            raise HTTPException(status_code=404, detail="Analytics not found for this URL")
        
        url_id=decode_base62(short_url.split("/")[-1])
        url_record=self.session.get(Url, url_id)
        if not url_record:
            raiseEx(404, "not exist")
        
        if url_record.user_id != user_id:
            raiseEx(404, "not exist")
        
        long_url=url_record.long_url
        utm_analytics_records = await self.session.exec(
            select(UTMAnalytics).where(UTMAnalytics.long_url == long_url)
        ).all()

        detailed_analytics_records = await self.session.exec(
            select(Analytics_2).where(Analytics_2.short_url == short_url)
        ).all()

        def aggregate_by_dimension(dimension_name, records):
            agg_dict = {}
            if dimension_name.startswith("utm"):
                for record in records:
                    key = getattr(record, dimension_name)
                    if key: # Only count if a UTM value exists
                        agg_dict[key] = agg_dict.get(key, 0) + 1
                return agg_dict
            else:
                for record in records:
                    key = getattr(record, dimension_name)
                    if key not in agg_dict:
                        agg_dict[key] = {"total_clicks": 0, "unique_clicks": 0}
                    agg_dict[key]["total_clicks"] += record.total_clicks
                    agg_dict[key]["unique_clicks"] += record.unique_clicks
                return agg_dict

        return {
            "summary": basic_analytics,
            "by_country": aggregate_by_dimension("country", detailed_analytics_records),
            "by_region": aggregate_by_dimension("region", detailed_analytics_records),
            "by_city": aggregate_by_dimension("city", detailed_analytics_records),
            "by_browser": aggregate_by_dimension("browser", detailed_analytics_records),
            "by_os": aggregate_by_dimension("os", detailed_analytics_records),
            "by_device": aggregate_by_dimension("device", detailed_analytics_records),
            "by_utm_source": aggregate_by_dimension("utm_source", utm_analytics_records),
            "by_utm_medium": aggregate_by_dimension("utm_medium", utm_analytics_records),
            "by_utm_campaign": aggregate_by_dimension("utm_capaign", utm_analytics_records),
            "by_utm_content": aggregate_by_dimension("utm_content", utm_analytics_records),
        }
    

    async def get_all_urls(self, base_url: str, user_id: int):
        urls = await self.session.exec(select(Url).where(Url.user_id == user_id)).all()
        response = []
        for u in urls:
            short_code = encode_base62(u.id)
            # Custom alias is not stored in the DB, defaulting to ai.io
            short_url = f"{base_url}snipr/ai.io/{short_code}"
            response.append({
                "id": u.id,
                "long_url": u.long_url,
                "short_url": short_url,
                "status": u.status,
                "expiry_time": u.expiry_time,
            })
        return {"total_urls": len(urls), "urls": response}
    

    async def utm_analytics(self,utm:UTM, long_url:str):
        utm_data=UTMAnalytics(**utm.model_dump(exclude={"id", "long_url"}))
        utm_data.long_url=long_url
        await self._add(utm_data)
  
        return

    async def update_url(self, short_key: str, expiry_time: str | None, user_id: int):
        try:
            url_id = decode_base62(short_key)
        except Exception:
            raiseEx(status.HTTP_404_NOT_FOUND, "Invalid short key")

        url_record = await self.session.get(Url, url_id)
        if not url_record:
            raiseEx(status.HTTP_404_NOT_FOUND, "URL not found")

        if url_record.user_id != user_id:
            raiseEx(status.HTTP_403_FORBIDDEN, "You do not have permission to update this URL")

        if expiry_time:
            new_expiry = parse_expiry(expiry_time)
            url_record.expiry_time = new_expiry
        else:
            url_record.expiry_time = None

        self.session.add(url_record)
        await self.session.commit()
        await self.session.refresh(url_record)

        await rdis.delete(f'URL:{url_id}')

        return {"message": "URL updated successfully", "url": url_record}

    async def delete_url(self, short_key: str, user_id: int):
        try:
            url_id = decode_base62(short_key)
        except Exception:
            raiseEx(status.HTTP_404_NOT_FOUND, "Invalid short key")

        url_record = await self.session.get(Url, url_id)
        if not url_record:
            raiseEx(status.HTTP_404_NOT_FOUND, "URL not found")

        if url_record.user_id != user_id:
            raiseEx(status.HTTP_403_FORBIDDEN, "You do not have permission to delete this URL")

        await self.session.delete(url_record)
        await self.session.commit()

        await rdis.delete(f'URL:{url_id}', f'safe:{url_id}')

        return {"message": "URL deleted successfully"}