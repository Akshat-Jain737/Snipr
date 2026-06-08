import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_SAFE_BROWSING_API_KEY environment variable not set.")

endpoint = (
            f"https://safebrowsing.googleapis.com/v4/"
            f"threatMatches:find?key={api_key}"
)

async def is_safe(url: str) -> bool:
        payload = {
            "client": {
                "clientId": "url-shortener",
                "clientVersion": "1.0.0",
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }

        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                endpoint,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        # No matches = safe
        return "matches" not in data