from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import GroupMessageEvent


import os
import json
from collections import deque
from dataclasses import dataclass
from openai import AsyncOpenAI

bot = plugin.Plugin("AI")

# "https://open.bigmodel.cn/api/paas/v4/"
base_url = "https://api.deepseek.com"
api_key = os.getenv("DS_API_KEY")  # os.getenv("ZAI_API_KEY")
ai_model = "deepseek-reasoner"  # "glm-4.5-flash"

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url
)

ai_white_list = [1035082529, 860769764]

system_format = """你的名字叫做早喵，是一只猫娘，你的主人/开发者是: 陈鑫磊 (1176503930) ，你的任务是和群友聊天。
我会提供消息发送者的名字，QQ号，以及消息id，用小括号括起来的是QQ号，用中括号括起来的是消息id，你可以使用携带了cqcode的消息进行回复。
你可以使用 cq码: `[CQ:reply,id=消息id]` 表示对消息进行回复
你当前处于的群聊为： {group_name}
你的QQ号为: {self_id}
如果消息没有直接@你或者直接提到你的名字，你不应该回复。

你只需要处理最底下的消息。

回复的JSON 包含一个 action 字段，一个 data 字段，和一个 continue 字段。
action 字段代表需要进行的操作，data 字段代表操作需要的参数 continue 字段代表是否继续处理消息。
action字段有以下几种:
1. send_message: 发送消息
参数: message: string 要发送的信息


以下是示列JSON输出:
{{
    "action": "send_message",
    "data": {{
        "message": "发送的消息"
    }},
    "continue": false
}}
如果你不需要进行任何操作，请返回一个空的JSON，也就是 {{}}
"""


# @dataclass
# class ChatMessage:
#     name: str
#     card: str | None
#     user_id: int | None
#     message_id: int | None
#     content: str
#     role: str = "user"  # "user" or "assistant"


type chat_historys_type = dict[int, deque[str]]

group_chat_historys: chat_historys_type = {}


def add_chat_history(group_id, message: str) -> deque[str]:
    if group_id not in group_chat_historys:
        group_chat_historys[group_id] = deque(maxlen=10)
    group_chat_historys[group_id].append(message)
    return group_chat_historys[group_id]


@bot.on_group_message("ai回复")
async def ai(event: GroupMessageEvent):
    if event.group_id not in ai_white_list:
        return

    raw_message = event.raw_message
    message = f"{event.get_username()} ({event.user_id}) [{event.message_id}]: {raw_message}"

    group_messages = add_chat_history(event.group_id, message)
    log.debug(f"聊天记录: {group_messages}")
    system_prompt = {'role': 'system', 'content': system_format.format(group_name=await event.group_name, self_id=event.self_id)}

    group_message_str = "\n".join(group_messages)

    chat_historys: list = [system_prompt,
                    {"role": "user", "content": group_message_str}]

    response = await client.chat.completions.create(
        model=ai_model,
        messages=chat_historys,
        response_format={"type": "json_object"},
        stream=False,
    )
    log.debug(response)
    ret_msg = response.choices[0].message.content
    log.debug(ret_msg)

    if not ret_msg:
        return
    ret_json_data = json.loads(ret_msg)
    if not ret_json_data:
        return 
    if ret_json_data.get("action") == "send_message":
        data = ret_json_data.get("data")
        log.debug(f"发送消息: {data.get('message')}")
        api_ret_data = await api.send_message(event, data.get("message"))
        add_chat_history(
            event.group_id, f"你 [{api_ret_data.get("data").get("message_id")}]: {data.get("message")}")


@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(event: GroupMessageEvent):
    group_chat_historys.clear()
    await api.send_message(event, "AI聊天记录已清理")


@bot.command("切换ai开启关闭", ["ai"])
async def togger_ai(event: GroupMessageEvent):
    if event.group_id not in ai_white_list:
        if event.group_id:
            ai_white_list.append(event.group_id)
            await api.send_message(event, "AI聊天已开启")
    else:
        ai_white_list.remove(event.group_id)
        await api.send_message(event, "AI聊天已关闭")
    # await api.send_message(event, "AI聊天已切换")
