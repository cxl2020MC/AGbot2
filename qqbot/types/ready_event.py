from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    bot: bool


class SessionData(BaseModel):
    version: int
    session_id: str
    user: User
    shard: list[int]
