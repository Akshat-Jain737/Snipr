from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession 

from DB.config import settings

engine = create_async_engine(settings.database_url, echo=True, future=True)

async_session_maker = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session():
    async with async_session_maker() as session:
        yield session