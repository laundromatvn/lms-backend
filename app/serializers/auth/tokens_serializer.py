from pydantic import BaseModel
from typing import Optional


class TokensSerializer(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
