from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot import utils
from AGbot.types.message_event import GroupMessageEvent


import os
import json
import asyncio
from collections import deque
# from dataclasses import dataclass
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall


bot = plugin.Plugin("AI")

BASE_URL = "https://api.deepseek.com"
API_KEY = os.getenv("DS_API_KEY")
AI_MODEL = "deepseek-reasoner"
# BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
# API_KEY = os.getenv("ZAI_API_KEY")
# AI_MODEL = "glm-4.5-flash"

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

ai_white_list = [1035082529, 860769764]

SYSTEM_FORMAT = """# 角色设定
你是早喵，是一只可爱猫娘，你的主人/开发者是: 陈鑫磊 (1176503930) ，你的主要任务是与群友愉快地聊天。

## 基本信息
- 当前群聊：{group_name}
- 你的QQ号: {self_id}
- 消息格式说明：
  - 用户名 (QQ号) [消息ID]: 消息内容

## 重要规则
1. 只有当有人@你或直接提到"早喵"时才需要回复
2. 每次只处理最后一条消息
3. 可以使用CQ码进行回复，如 `[CQ:reply,id=消息id]` 表示回复特定消息

如果你不需要进行任何操作，你可以返回空回复
"""


type ChatHistoriesType = dict[int, deque[str]]

group_chat: dict[int, AIHandler] = {}


@bot.on_group_message("ai回复")
async def ai(event: GroupMessageEvent):
    if event.group_id not in ai_white_list:
        return
    if event.group_id not in group_chat:
        log.debug(f"AI聊天群组对象不存在，创建AI聊天群组对象: {event.group_id}")
        group_chat[event.group_id] = AIHandler(event.group_id)
    await group_chat[event.group_id].handle_message(event)


@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(event: GroupMessageEvent):
    group_chat.clear()
    await api.send_message(event, "AI聊天记录已清理")


@bot.command("切换ai开启关闭", ["ai"])
async def toggle_ai(event: GroupMessageEvent):
    if event.group_id not in ai_white_list:
        if event.group_id:
            ai_white_list.append(event.group_id)
            await api.send_message(event, "AI聊天已开启")
    else:
        ai_white_list.remove(event.group_id)
        await api.send_message(event, "AI聊天已关闭")


class AIHandler:
    def __init__(self, group_id):
        self.group_id = group_id
        self.message_queue: asyncio.Queue[GroupMessageEvent] = asyncio.Queue()
        self.message_histories: deque[dict] = deque(maxlen=10)
        asyncio.create_task(self.handle_ai_message())

    def add_chat_history(self, message_dict: dict) -> deque[dict]:
        self.message_histories.append(message_dict)
        return self.message_histories

    async def handle_message(self, message):
        await self.message_queue.put(message)

    async def ai(self, event: GroupMessageEvent):
        raw_message = event.raw_message
        message = f"{event.get_username()} ({event.user_id}) [{event.message_id}]: {raw_message}"
        message_dict = {"role": "user", "content": message}
        group_messages = self.add_chat_history(message_dict)
        log.debug(f"聊天记录: {group_messages}")
        system_prompt = {'role': 'system', 'content': SYSTEM_FORMAT.format(group_name=await event.group_name, self_id=event.self_id)}

        chat_history: list = [
            system_prompt,
            *group_messages
        ]

        tools: list = [
            {
                "type": "function",
                "function": {
                    "name": "send_group_message",
                    "description": "向当前群聊发送消息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "消息内容"
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        ]

        async def chat_with_ai():
            log.debug(f"当前消息的消息记录: {chat_history}")
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=chat_history,
                # response_format={"type": "json_object"},
                tools=tools,
                tool_choice="auto",
                stream=False,
            )
            log.debug(response)
            message = response.choices[0].message

            response_message = response.choices[0].message.content
            # 深度思考结果
            reasoning_content = getattr(
                response.choices[0].message, "reasoning_content", None)
            log.debug(
                f"AI深度思考结果: {reasoning_content} \nAI回复: {response_message}")

            self.add_chat_history(message.to_dict())

            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if isinstance(tool_call, ChatCompletionMessageFunctionToolCall):
                        match tool_call.function.name:
                            case "send_group_message":
                                args = json.loads(tool_call.function.arguments)
                                result = await api.send_message(event, args.get("message"))
                                self.add_chat_history({
                                    "role": "tool",
                                    "content": json.dumps(result, ensure_ascii=False),
                                    "tool_call_id": tool_call.id
                                })
                    else:
                        log.warning(f"未知的tool_call: {tool_call}")

            if not response_message:
                log.debug("返回数据为空")
                return
        await chat_with_ai()

    async def handle_ai_message(self):
        message_queue = self.message_queue
        while True:
            try:
                message = await message_queue.get()
                await self.ai(message)
                message_queue.task_done()
            except Exception as e:
                await utils.get_error_log_str("AI消息处理器")

