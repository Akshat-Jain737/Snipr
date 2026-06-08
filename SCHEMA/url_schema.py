from datetime import datetime
import ipaddress
import socket
from urllib.parse import urlparse
from pydantic import BaseModel, Field, HttpUrl, field_validator

class UTM(BaseModel):
    #UTM
    utm_source:str|None=None # reddit, google
    utm_medium:str|None=None# via paid(cpc) or organic
    utm_capaign:str|None=None # purpose
    utm_content:str|None=None # add/link/banner

allowed_scheme={'http', 'https'}
class urlscheme(BaseModel):
    long_url:HttpUrl
    custom_alias:str|None=Field(default='ai.io')
    expiry_time:str|None=Field(default=None)

    @field_validator('long_url')
    @classmethod # without any object run this method
    def validate_url(cls, value):

        # if value.scheme not in allowed_scheme:
        #     raise ValueError("Only HTTP/HTTPS URLs are allowed")

        parsed = urlparse(str(value))
        hostname = parsed.hostname

        # if not hostname:
        #     raise ValueError("Missing hostname")

        try:
            ip = ipaddress.ip_address(socket.gethostbyname(hostname))

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
            ):
                raise ValueError("Private/internal addresses not allowed")

        except socket.gaierror:
            raise ValueError("Host cannot be resolved")
        
        return value


class UpdateURLPayload(BaseModel):
    expiry_time:str