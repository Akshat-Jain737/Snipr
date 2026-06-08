import httpx
from sqlmodel import Session, select
from user_agents import parse

from DB.models import Analytics, Analytics_2
from DB.session import engine

async def clicks_background(short_url: str, is_unique: bool, ip_address: str, user_agent_str: str):
    with Session(engine) as session:
        url_data = await session.exec(select(Analytics).where(Analytics.short_url==short_url)).first()
        if url_data is None:
            url_data = Analytics(short_url=short_url)

        url_data.total_clicks += 1
        if is_unique:
            url_data.unique_clicks += 1

        # Parse User-Agent
        user_agent = parse(user_agent_str)
        browser = user_agent.browser.family
        os_name = user_agent.os.family
        device = "Mobile" if user_agent.is_mobile else ("Tablet" if user_agent.is_tablet else "Desktop")

        # Parse IP for Geolocation
        country, region, city = "Unknown", "Unknown", "Unknown"
        if ip_address and ip_address not in ("127.0.0.1", "::1", "localhost", "Unknown"):
            try:
                # Since background tasks are sync by default, we can run a sync network call.
                response = httpx.get(f"http://ip-api.com/json/{ip_address}", timeout=3.0)
                if response.status_code == 200:
                    geo_data = response.json()
                    if geo_data.get("status") == "success":
                        country = geo_data.get("country", "Unknown")
                        region = geo_data.get("regionName", "Unknown")
                        city = geo_data.get("city", "Unknown")
            except Exception:
                pass  # Fallback to Unknown if the API fails

        # Find existing aggregated record or create a new one
        analytics_2_data = await session.exec(
            select(Analytics_2).where(
                Analytics_2.short_url == short_url,
                Analytics_2.country == country,
                Analytics_2.region == region,
                Analytics_2.city == city,
                Analytics_2.browser == browser,
                Analytics_2.os == os_name,
                Analytics_2.device == device
            )
        ).first()

        if analytics_2_data is None:
            analytics_2_data = Analytics_2(
                short_url=short_url, country=country, region=region, city=city,
                browser=browser, os=os_name, device=device,
                total_clicks=0, unique_clicks=0
            )

        analytics_2_data.total_clicks += 1
        if is_unique:
            analytics_2_data.unique_clicks += 1

        session.add(url_data)
        await session.add(analytics_2_data)
        await session.commit()
