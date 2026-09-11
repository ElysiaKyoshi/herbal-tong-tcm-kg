from typing import TypedDict

from langgraph.graph import StateGraph, MessagesState, START, END


class MyState(TypedDict):
    input: str
    output: str


# 定义节点逻辑
def call_model(state: MyState):
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
    user_input = "你好，帮我写一个LangGraph的demo"
    final_state = app.invoke({"input": user_input})
    print(final_state)
