from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage


# 定义状态结构
class AgentState(TypedDict):
    input: str
    explanation: str
    output: str


# 初始化 LLM（DeepSeek / OpenAI）
llm = ChatOpenAI(
    api_key="YOUR_API_KEY_HERE",
    base_url="https://api.deepseek.com",
    model="deepseek-chat"
)


# AgentA: 调用LLM解释问题
def agent_a(agent_state: AgentState):
    question = agent_state['input']
    messages = [HumanMessage(content=f"请你通俗解释这个问题：{question}")]
    response = llm.invoke(messages)
    explanation = response.content
    agent_state["explanation"] = explanation
    return agent_state


# AgentB: 调用LLM生成回答
def agent_b(agent_state: AgentState):
    explanation = agent_state["explanation"]
    messages = [HumanMessage(content=f"请根据以下解释来回答原问题：{explanation}")]
    response = llm.invoke(messages)
    output = response.content
    agent_state["output"] = output
    return agent_state


# 构建 LangGraph 状态图
def build_graph():
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent_a", agent_a)
    graph_builder.add_node("agent_b", agent_b)

    graph_builder.add_edge(START, "agent_a")
    graph_builder.add_edge("agent_a", "agent_b")
    graph_builder.add_edge("agent_b", END)
    graph = graph_builder.compile()
    return graph


# 输出graph
graph = build_graph()

# 测试调用
response = graph.invoke({"input": "人工智能能取代人类吗？"})
print("🧠 最终回答：", response["output"])
