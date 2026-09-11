from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, MessagesState, START, END


class MyState(TypedDict):
    input: str
    output: str


# 定义节点逻辑
def call_model(state: MyState, config: RunnableConfig):
    # 从 config 中取参数
    user_id = config.get("configurable", {}).get("user_id", "unknown")
    prefix = config.get("configurable", {}).get("prefix", ">>>")
    print("user_id:", user_id)
    print("prefix:", prefix)

    input = state['input']
    state['output'] = input + "！哈哈哈！"
    return state


# 构建图
graph_builder = StateGraph(MyState)
graph_builder.add_node(call_model.__name__, call_model)

# 添加边
graph_builder.add_edge(START, call_model.__name__)
graph_builder.add_edge(call_model.__name__, END)

# 编译成可运行的图
app = graph_builder.compile()

# 测试
if __name__ == "__main__":
    # 定义 config
    config = {
        "configurable": {
            "thread_id": "22222"
        }
    }
    user_input = "你好，帮我写一个LangGraph的demo"
    final_state = app.invoke({"input": user_input}, config=config)
    print(final_state)
