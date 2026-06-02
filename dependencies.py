from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

from session import get_session
from url_services import URL_Services

def get_url_services(session: Session = Depends(get_session)) -> URL_Services:
    return URL_Services(session=session)

UrlDep = Annotated[URL_Services, Depends(get_url_services)]
