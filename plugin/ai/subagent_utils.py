import asyncio
from typing import TYPE_CHECKING, ClassVar
lazy import traceback

from pydantic import BaseModel, Field

from qqbot.log import logger as log

from . import ai_utils, tool_calls_utils, web_search

if TYPE_CHECKING:
    from .ai import AIPlugin

TOOLS = [
    tool_calls_utils.Tool(
        name="web_search",
        description="搜索网页内容，返回搜索结果",
        model=web_search.WebSearchToolParam,
        function=web_search.web_search_tool_call,
    ),
    tool_calls_utils.Tool(
        name="web_fetch",
        description="获取网页内容，返回网页内容",
        model=web_search.WebFetchToolParam,
        function=web_search.web_fetch_tool_call,
    ),
]


class AskAIToolParam(BaseModel):
    agent_name: str = Field(..., description="子代理名称")
    user_input: str = Field(..., description="你想向AI提问的问题")


class SubAgent:
    SubAgentList: ClassVar[list[SubAgent]] = []

    def __init__(self, ai_plugin: AIPlugin, agent_name: str):
        self.agent_name = agent_name
        self.ai_plugin = ai_plugin
        self.ai_chat_manager = ai_utils.AiChatManager(
            f"你是一个名为 {agent_name} 的子代理, 你将根据用户的输入提供帮助和信息。你的最终输出会被发送给主代理, 你应该尽量提供有用的建议和信息, 并且在需要时调用工具函数。请注意, 你不能直接与用户交互, 你只能通过主代理与用户交互。请确保你的回答简洁明了, 并且尽量避免使用模糊或不确定的语言。",
            tool_calls=TOOLS,
        )
        self.ask_ai_tasks: set[asyncio.Task] = set()
        type(self).SubAgentList.append(self)

    def get_agent_name(self):
        return self.agent_name

    async def ask_ai(self, user_input: str):
        log.info(f"子代理 {self.agent_name} 收到用户输入: {user_input}")
        await self.ai_chat_manager.add_user_message(user_input)
        response = await self.ai_chat_manager.handle_ai(
            await self.ai_chat_manager.get_messages()
        )
        log.info(f"子代理 {self.agent_name} 的 AI 响应: {response}")
        return response

    async def ask_ai_worker(self, user_input: str):
        try:
            response = await self.ask_ai(user_input)
            message = response.choices[0].message.content
            message = (
                f"你之前委托的 `ask_ai` 工具函数的 {self.agent_name} 的 AI 响应: {message}"
                if message
                else f"你之前委托的 `ask_ai` 工具函数 {self.agent_name} 未返回任何内容。"
            )
        except Exception:  # noqa: BLE001
            log.exception(f"子代理 {self.agent_name} 的 AI 响应处理失败")
            message = f"你之前委托的 `ask_ai` 工具函数 {self.agent_name} 的 AI 响应处理失败 {traceback.format_exc()}"
        await self.ai_plugin.handle_message(
            ai_utils.AiRawMessages(content=ai_utils.make_user_message(message))
        )
        self.ask_ai_tasks.discard(asyncio.current_task())
        type(self).SubAgentList.remove(self)

    async def ask_ai_tools(self, tool_param: AskAIToolParam):
        task = asyncio.create_task(self.ask_ai_worker(tool_param.user_input))
        self.ask_ai_tasks.add(task)
        return "请求已发送到 AI 工具处理。请稍等片刻，AI 工具正在处理您的请求，不要尝试多次请求。请求完成后，您将收到结果"

    # async def ask_ai_tools_with_function_call(self, user_input: str):
