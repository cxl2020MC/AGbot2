# from datetime import datetime
# from enum import StrEnum
# from typing import Any

from pydantic import BaseModel


class Config(BaseModel):
    appId: str
    clientSecret: str

