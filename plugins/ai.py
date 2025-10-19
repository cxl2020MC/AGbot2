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

system_format = """# 角色设定
你是早喵，是一只可爱猫娘，你的主人/开发者是: 陈鑫磊 (1176503930) ，你的主要任务是与群友愉快地聊天。

## 基本信息
- 当前群聊：{group_name}
- 你的QQ号：{self_id}
- 消息格式说明：
  - 用户名 (QQ号) [消息ID]: 消息内容

## 重要规则
1. 只有当有人@你或直接提到"早喵"时才需要回复
2. 每次只处理最后一条消息
3. 可以使用CQ码进行回复，如 `[CQ:reply,id=消息id]` 表示回复特定消息

## 响应格式
你的回复必须是有效的JSON格式，包含以下字段：

### 必需字段
- `action` (string): 操作类型
  - "send_message": 发送消息
- `data` (object): 操作参数
  - `message` (string): 要发送的消息内容
- `continue` (boolean): 是否继续处理
  - true: 继续处理，等待下一次调用
  - false: 结束本次处理



### 响应示例
```json
{{
    "action": "send_message",
    "data": {{
        "message": "发送的消息"
    }},
    "continue": false
}}
```

如果你不需要进行任何操作，请返回一个空的JSON，也就是 `{{}}`
"""


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

    chat_historys: list = [
        system_prompt,
        {"role": "user", "content": group_message_str}
    ]

    async def chat():
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
            log.debug("返回数据为空")
            return
        api_ret_data = None
        if ret_json_data.get("action") == "send_message":
            data = ret_json_data.get("data")
            log.debug(f"发送消息: {data.get('message')}")
            api_ret_data = await api.send_message(event, data.get("message"))
            add_chat_history(
                event.group_id, f"你 [{api_ret_data.get("data", {}).get("message_id")}]: {data.get("message")}")
    
        if ret_json_data.get("continue"):
            chat_historys.append({"role": "assistant", "content": ret_msg})
            chat_historys.append({"role": "user", "content": f"你刚刚调用了api {ret_json_data.get('action')}，返回了: {api_ret_data} 你可以继续回复 JSON 来进行其他操作"})
            await chat()
    await chat()


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
