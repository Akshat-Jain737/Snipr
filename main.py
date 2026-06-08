from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from ROUTES.auth import auth_router
from ROUTES.url import url

# Disable FastAPI's default Swagger UI and ReDoc to cleanly replace them with Scalar
app = FastAPI()

# Include the router from url.py
app.include_router(auth_router)
app.include_router(url)

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
        custom_css="""
        .dark-mode {
            --scalar-background-1: #000000 !important;
            --scalar-background-2: #0f0f0f !important;
            --scalar-background-3: #1a1a1a !important;
        }
        """,
    )