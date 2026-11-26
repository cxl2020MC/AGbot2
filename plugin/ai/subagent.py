from typing import TYPE_CHECKING, ClassVar

from qqbot.log import logger as log

from . import ai_utils, tool_calls_utils, web_search

if TYPE_CHECKING:
    from .ai import AIPlugin

OOLS = [
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


class SubAgent:
    SubAgentList: ClassVar[list[SubAgent]] = []

    def __init__(self, ai_plugin: AIPlugin, agent_name: str):
        self.agent_name = agent_name
        self.ai_plugin = ai_plugin
        self.ai_chat_manager = ai_utils.AiChatManager(
            f"你是一个名为 {agent_name} 的子代理, 你将根据用户的输入提供帮助和信息。"
        )
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

    async def ask_ai_tools(self, user_input: str):
        response = await self.ask_ai(user_input)
        return (
            response.choices[0].message.content
            if response.choices
            else "发生错误: 模型没有返回响应"
        )
