from pydantic import BaseModel, Field
from enum import IntEnum


class GroupMessageType(IntEnum):
    TXT = 0
    MARKDOWN = 2
    MEDIA = 7
    CARD = 8


class GroupMessage(BaseModel):
    msg_type: GroupMessageType = GroupMessageType.TXT
    content: str = ""
    markdown: MessageMarkdown | None = None
    keyboard: Keyboard | None = None
    msg_id: str | None = None
    event_id: str | None = None
    msg_seq: int | None = None
    media: MediaInfo | None = None
    message_reference: MessageReference | None = None


class MessageMarkdown(BaseModel):
    content: str
    force_verify_image_resource: bool = False


class MediaInfo(BaseModel):
    file_info: str

class MessageReference(BaseModel):
    message_id: str

# ==========================================
# 定义整型枚举 (IntEnum)
# ==========================================


class PermissionType(IntEnum):
    SPECIFIED_USER = 0  # 指定用户
    ADMIN = 1  # 管理员
    EVERYONE = 2  # 所有人


class ActionType(IntEnum):
    JUMP = 0  # 跳转按钮: http 或 小程序
    CALLBACK = 1  # 回调按钮: 回调后台接口,data 传给后台
    COMMAND = 2  # 指令按钮: 自动在输入框插入 @bot data


class RenderStyle(IntEnum):
    GREY_BORDER = 0  # 灰色线框
    BLUE_BORDER = 1  # 蓝色线框
    WHITE_BG_RED_TEXT = 3  # 白色背景+红色字体 (注: 原文档没有2)
    BLUE_BG_WHITE_TEXT = 4  # 蓝色背景+白色字体


# ==========================================
# 数据模型
# ==========================================


class Modal(BaseModel):
    content: str | None = Field(
        None,
        description="二次确认的提示文本,如果不为空则会进行二次确认。注意:最多40个字符, 不能有 URL",
    )
    confirm_text: str | None = Field(
        None,
        description="二次确认提示确认按钮中展示的文字,可以为空, 默认为“确认”。注意:最多4个字符",
    )
    cancel_text: str | None = Field(
        None,
        description="二次确认提示取消按钮中的文字,可以为空,默认为“取消”。注意:最多4个字符",
    )


class Permission(BaseModel):
    type: PermissionType | None = Field(
        None, description="0=指定用户，1=管理员，2=所有人"
    )
    specify_user_ids: list[str] | None = Field(
        None, description="有权限的用户 id 的列表"
    )
    specify_role_ids: list[str] | None = Field(
        None, description="有权限的身份组 id 的列表 (仅频道可用)"
    )


class Action(BaseModel):
    type: ActionType | None = Field(
        None, description="0: 跳转按钮 1: 回调按钮 2: 指令按钮"
    )
    permission: Permission | None = Field(None, description="操作权限")
    data: str | None = Field(None, description="回调数据。type=1/2时必填")
    unsupport_tips: str | None = Field(None, description="版本过低时提示文案")
    enter: bool | None = Field(
        None,
        description="指令按钮可用，点击按钮后直接自动发送 data，仅单聊可用，默认 false。支持版本 8983",
    )
    reply: bool | None = Field(
        None,
        description="指令按钮可用，指令是否带引用回复本消息，默认 false。支持版本 8983",
    )
    anchor: int | None = Field(
        None,
        description="本字段仅在指令按钮下有效，设置后后会忽略 action.enter 配置。设置为 1 时，点击按钮自动唤起手Q选图器，其他值暂无效果。（仅支持手机端版本 8983+ 的单聊场景，桌面端不支持）",
    )
    modal: Modal | None = Field(None, description="用户点击二次确认操作")


class RenderData(BaseModel):
    label: str | None = Field(None, description="按钮文字，最多 10 字符")
    visited_label: str | None = Field(None, description="点击后文字，不传则保持不变")
    style: RenderStyle | None = Field(
        None,
        description="0: 灰色线框, 1: 蓝色线框 3: 白色背景+红色字体, 4: 蓝色背景+白色字体",
    )


class Button(BaseModel):
    id: str | None = Field(None, description="按钮 ID。同一键盘内唯一")
    render_data: RenderData | None = Field(None, description="按钮渲染")
    action: Action | None = Field(None, description="按钮点击行为")
    group_id: str | None = Field(
        None,
        description="分组ID, 同一分组内有一个按钮操作后，其它按钮则变灰不可点击 注意:只有当 action.type = 1 时才有效",
    )


class Row(BaseModel):
    buttons: list[Button] | None = Field(None, description="行内按钮，从左到右排列")


class KeyboardContent(BaseModel):
    rows: list[Row] | None = Field(None, description="按钮行列表")


class Keyboard(BaseModel):
    id: str | None = Field(
        None, description="内嵌键盘模板 ID。使用平台预设模板时填写此字段"
    )
    content: KeyboardContent | None = Field(
        None, description="自定义键盘布局。与 id 互斥，用于自定义按钮"
    )
