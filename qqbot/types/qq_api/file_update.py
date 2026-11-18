from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field


class ApiType(StrEnum):
    GROUP = "groups"
    USER = "users"


class FileType(IntEnum):
    # 1=图片, 2=视频, 3=语音, 4=文件
    图片 = 1
    视频 = 2
    语音 = 3
    文件 = 4


class FileUpdateRequest(BaseModel):
    file_type: FileType = Field(..., description="文件类型")
    url: str | None = Field(
        default=None,
        description="文件的 URL，需以 http 开头，平台会下载并转存 分片上传合并时可为空",
    )
    file_name: str | None = Field(
        default=None, description="文件名 (分片上传或者二进制上传时必填）"
    )
    srv_send_msg: bool = Field(
        default=False,
        description="true=直接发送消息并占用主动消息频次，返回中包含消息 ID false=仅返回 file_info，用于后续发送消息接口的 media 字段",
    )
    upload_id: str | None = Field(
        default=None,
        description="分片上传任务 ID。来自 UploadPrepare 响应的 upload_id， 传入后走分片上传合并路径，url 可为空",
    )
    file_data: str | None = Field(
        default=None,
        # 官方文档写的直接上传二进制数据，实际上是base64编码后的数据（tx nmsl）
        description="直接上传Base64数据。 直接上传Base64数据有大小限制，需要在5M以内，如果超过则需要使用URL上传或者分片上传。",
    )


class FileUpdateResult(BaseModel):
    file_uuid: str = Field(..., description="文件唯一 ID")
    file_info: str = Field(
        ...,
        description="文件信息，用于发送消息接口的 media.file_info 字段。 内部为序列化的二进制数据，开发者无需解析，直接透传即可",
    )
    ttl: int = Field(
        ..., description="file_info 有效期（秒）。到期后需重新上传。 0 表示可长期使用"
    )
    id: str | None = Field(
        None, description="发送消息的唯一 ID。仅 srv_send_msg=true 时返回"
    )
    raw_url: str | None = Field(
        default=None,
        description="文件下载链接（COS 预签名 GET URL），有效期与 ttl 一致 仅分片上传合并（upload_id 路径）且 file_type 为图片/视频/语音时返回； URL 直传和文件类型(file_type=4)不返回此字段",
    )


class FileUpdatePrepareRequest(BaseModel):
    file_type: FileType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小，单位字节")
    file_name: str = Field(..., description="文件名")
    md5: str = Field(..., description="文件的 MD5 值")
    sha1: str = Field(..., description="文件的 SHA1 值")
    md5_10m: str = Field(..., description="文件的前 10002432 字节（约 10MB） 的 MD5 值")


class FileUpdatePrepareResponse(BaseModel):
    upload_id: str = Field(..., description="上传 ID")
    block_size: int = Field(..., description="分块大小，单位字节")
    parts: list[FileUploadPart] = Field(..., description="分片信息列表")
    upload_config: FileUploadConfig = Field(..., description="上传配置")


class FileUploadPart(BaseModel):
    # cnm tx 官方文档写的 index 从 0 开始，但实际上是从 1 开始的
    index: int = Field(..., description="分片序号，从 1 开始")
    presigned_url: str = Field(
        ..., description="预签名上传 URL，客户端通过 HTTP PUT 将分片数据上传到此 URL"
    )
    block_size: int = Field(..., description="该分块的大小（字节）")


class FileUploadConfig(BaseModel):
    concurrency: int = Field(1, description="上传并发数，默认 1")
    retry_timeout: int = Field(300, description="重试超时时间（秒），默认 300（5分钟）")
    retry_delay: int = Field(1, description="重试延迟（秒），默认 1")


class FileUploadPartFinish(BaseModel):
    upload_id: str = Field(..., description="上传任务 ID，来自预上传响应")
    part_index: int = Field(..., description="分片序号，对应 UploadPart.index")
    # 我不明白为啥文档这里类型是str
    block_size: int = Field(..., description="该分块的实际大小（字节）")
    md5: str = Field(..., description="该分片的 MD5 校验值")
