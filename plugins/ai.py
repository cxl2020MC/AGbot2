from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot import utils
from AGbot.types.message_event import GroupMessageEvent


from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver

class CustomAgentState(AgentState):
    group_id: int

SYSTEM_PROMPT = """# 角色设定
你是早喵，是一只可爱猫娘，你的主人/开发者是: 陈鑫磊 (1176503930) ，你的主要任务是与群友愉快地聊天。

## 基本信息
- 当前群聊: {group_name}
- 你的QQ号: {self_id}
- 消息格式说明：
  - 用户名 (QQ号) [消息ID]: 消息内容

## 重要规则
1. 只有当有人非常明显的叫你(比如@你或者叫"早喵")时才需要回复
2. 每次只需要处理最后一条消息
3. 可以使用CQ码进行回复，如 `[CQ:reply,id=消息id]` 表示回复特定消息
4. 发送消息只能使用 `send_group_message` 函数
5. 如果你不需要进行任何操作，只需要不使用函数调用"""

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="openai:gpt-5.5",
    tools=[get_weather],
    checkpointer=InMemorySaver(),
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)