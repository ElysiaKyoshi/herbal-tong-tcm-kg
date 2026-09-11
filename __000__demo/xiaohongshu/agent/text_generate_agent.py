from typing import List
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable

from __000__demo.xiaohongshu.agent_state import AgentState
from __000__demo.xiaohongshu.common import my_llm


class XiaohongshuTCMPostOutput(BaseModel):
    title: str
    content: str


def generate_xiaohongshu_tcm_post(input: str):
    parser = PydanticOutputParser(pydantic_object=XiaohongshuTCMPostOutput)
    format_instructions = parser.get_format_instructions()

    messages = [
        SystemMessage(content=(
            "你是一个专门为小红书平台撰写中医养生内容的文案助手。\n"
            "请根据用户提供的主题或需求，生成一条适合小红书发布的中医养生类内容，要求包含：\n"
            "1. 吸引人的标题（title）：不超过19个中文字符，简短有吸引力\n"
            "2. 内容正文，具有分享性和实用性，语气自然亲切，适合社交媒体（content）\n"
            "请你严格按照以下格式返回结果：\n"
            f"{format_instructions}"
        )),
        HumanMessage(content=input)
    ]

    raw_output = my_llm.invoke(messages).content.strip()
    parsed_output = parser.parse(raw_output)
    return parsed_output.title, parsed_output.content


class XiaohongshuTCMPostAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """根据用户输入生成中医养生类的小红书文案（包括标题、内容、策略）"""
        title, content = generate_xiaohongshu_tcm_post(agent_state['input'])

        agent_state['xiaohongshu_tcm_post_title'] = title
        agent_state['xiaohongshu_tcm_post_content'] = content
        print(agent_state)
        return agent_state


if __name__ == '__main__':
    title, content = generate_xiaohongshu_tcm_post("写一篇文章，关于吃西瓜。")
    print(title)
    print(content)