from pydantic import BaseModel, Field


class GroupInfo(BaseModel):
    """
    群组信息模型
    """
    group_openid: str = Field(..., description="群 OpenID")
    group_name: str = Field(..., description="群名称")
    group_finger_memo: str = Field(..., description="群简介")
    group_class_text: str = Field(..., description="群分类")
    group_tags: list[str] = Field(..., description="群标签列表")
    group_member_num: int = Field(..., description="群成员人数")
