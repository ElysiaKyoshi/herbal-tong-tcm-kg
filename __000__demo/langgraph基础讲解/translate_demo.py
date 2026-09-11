from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable

# ========== 1) 配置 LLM ==========
# 这里保留你当前的 DeepSeek 配置，便于直接运行
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key="YOUR_API_KEY_HERE"
)


# ========== 2) 定义状态 ==========
class AgentState(TypedDict, total=False):
    # 输入
    input: str
    # 是否是翻译
    is_translate_or_not: bool
    # 翻译结果
    translate_result: str
    # 翻译内容
    translate_content: str
    # QA结果
    qa_result: str
    # 输出
    output: str


# 3.1 意图判断（规则式，简单直观）
class IntentDetectorAgent(Runnable):
    def invoke(self, state: AgentState, config: dict = None) -> AgentState:
        """判断用户输入是翻译文章还是普通回答"""
        messages = [
            SystemMessage(content=(
                "你是一个意图分类助手，用来判断用户输入是'翻译任务'还是'普通回答任务'。\n"
                "翻译任务的特征：用户明确要求翻译文章、句子、单词，或要求将中文翻译成英文/英文翻译成中文。\n"
                "普通回答任务的特征：用户是直接提问、咨询信息、讨论话题，而不是要求翻译。\n"
                "请你只回答：翻译 或 普通回答，不要补充其他内容。"
            )),
            HumanMessage(content=state['input'])
        ]

        response = llm.invoke(messages).content.strip()

        if "翻译" in response:
            state['is_translate_or_not'] = True
        else:
            state['is_translate_or_not'] = False
        print("意图判断结果：", state)

        return state

class ExtractTranslateContentAgent(Runnable):
    def invoke(self, state: AgentState, config: dict = None) -> AgentState:
        """判断用户输入是翻译文章还是普通回答"""
        messages = [
            SystemMessage(content=(
                "你是一个信息抽取助手。你的任务是：\n"
                "1. 从用户输入中抽取出需要翻译的原始内容。\n"
                "2. 保持原文，不要翻译、不做解释、不补充内容。\n"
                "3. 如果用户输入不包含需要翻译的内容，就返回空字符串。\n\n"
                "⚠️ 注意：你绝对不能对内容进行翻译，只能提取。"
            )),
            HumanMessage(content=state['input'])
        ]

        response = llm.invoke(messages).content.strip()

        state["translate_content"] = response
        print("意图判断结果：", state)

        return state


# 3.2 翻译节点：中↔英自动互译，仅输出译文
class TranslateAgent(Runnable):
    def invoke(self, state: AgentState, config: dict = None) -> AgentState:
        text = state["translate_content"]
        prompt = (
            "你是翻译助手。请先自动识别语言，然后在中文与英文之间互译。"
            "只输出译文本身，不要额外解释。\n"
            f"待翻译内容：{text}"
        )
        resp = llm.invoke([HumanMessage(content=prompt)]).content
        state["translate_result"] = resp
        state["output"] = resp
        print("翻译结果：", state)
        # 按你的状态定义回写
        return state


# 3.3 普通回答节点：简洁要点式回答
class QAAgent(Runnable):
    def invoke(self, state: AgentState, config: dict = None) -> AgentState:
        q = state["input"]
        prompt = (
            "请用中文，以3-5条要点简洁回答下面的问题；如需步骤，用1,2,3编号；"
            "不确定就直说不确定并给出可验证途径。\n"
            f"问题：{q}"
        )
        resp = llm.invoke([HumanMessage(content=prompt)]).content
        state["qa_result"] = resp
        return {**state, "qa_result": resp, "output": resp}


graph = StateGraph(AgentState)
# 节点
graph.add_node("intent_detector_agent", IntentDetectorAgent())
graph.add_node("translate_agent", TranslateAgent())
graph.add_node("qa_agent", QAAgent())
graph.add_node("extract_translate_content_agent", ExtractTranslateContentAgent())

# 添加边
graph.set_entry_point("intent_detector_agent")


def intent_detector_agent_control(state: AgentState):
    if state['is_translate_or_not']:
        return "extract_translate_content_agent"
    else:
        return "qa_agent"


graph.add_conditional_edges("intent_detector_agent", intent_detector_agent_control)

graph.add_edge("extract_translate_content_agent", "translate_agent")
graph.add_edge("translate_agent", END)
graph.add_edge("qa_agent", END)

app = graph.compile()

if __name__ == '__main__':
    # result1 = app.invoke({"input": "你好"})
    # print(result1["output"])


    # result2 = app.invoke({"input": "请翻译以下内容：我在深圳很开心。"})
    # print(result2["output"])

    result3 = app.invoke({"input": "解释下什么是大模型"})
    print(result3["output"])