from pydantic import BaseModel, Field


class UserInfoResponse(BaseModel):
    union_openid: str | None = Field(
        None, description="跨应用关联用户openid，当绑定了3方应用时有效"
    )
    username: str = Field(..., description="用户名")
    avatar: str = Field(..., description="用户头像原图")
    allow_proactive_msg: bool = Field(..., description="是否接收主动推送")
