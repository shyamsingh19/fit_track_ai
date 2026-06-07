from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class TokenResponse(TokenPair):
    token_type: str = "bearer"

