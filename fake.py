from datetime import datetime, timezone
import dateparser

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

    return dt.strftime("%b %-d, %Y, %-I:%M %p")

print(parse_expiry("12 hrs"))