from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Username = Field(min_length=1, max_length=64)
Password = Field(min_length=1, max_length=128)


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Username
    password: str = Password


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(ge=1)
