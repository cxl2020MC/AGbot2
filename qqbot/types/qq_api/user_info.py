from pydantic import BaseModel, Field


class UserInfoResponse(BaseModel):
    """
    获取用户信息响应体
    """

    id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    avatar: str = Field(..., description="头像 URL")
    # bot: bool = Field(..., description="是否为机器人") # cnm tx 什么叫做文档里面有这个字段，实际上没有

    union_openid: str | None = Field(default=None, description="跨应用统一用户 OpenID")
    union_user_account: str | None = Field(
        default=None, description="跨应用统一用户账号"
    )

    # 根据「响应示例」补充的额外字段
    share_url: str | None = Field(default=None, description="分享链接")
    welcome_msg: str | None = Field(default=None, description="欢迎加入群聊语")


# {
#     "id": "1483093736789806323",
#     "username": "AGbot",
#     "avatar": "http://thirdqq.qlogo.cn/g?b=oidb&k=I9r2CcLwgCHr1gFgq6Monw&kti=auxA6gwBHsI&s=0&t=1793007049",
#     "union_openid": "81F2D5B5ABC2F97AA249B9443E932F3D",
#     "union_user_account": "",
#     "share_url": "https://qun.qq.com/qunpro/robot/qunshare?robot_uin=3889000629&robot_appid=102072641&biz_type=0",
#     "welcome_msg": "",
# }

