from typing import TypedDict, NotRequired, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END


class MyState(TypedDict):
    input: str
    output: str
    aaa: Optional[int]


def init_state(state: MyState):
    state["input"] = None
    state["output"] = None
    state["aaa"] = None

# 定义节点逻辑
def call_model(state: MyState):
    print(state)
    input_text = state['input']
    output = state.get('output', "")
    state["aaa"] = 8888
    output += input_text + "---！哈哈哈！---"
    state['output'] = output
    return state


# 构建图
graph_builder = StateGraph(MyState)
graph_builder.add_node(call_model.__name__, call_model)
graph_builder.add_edge(START, call_model.__name__)
graph_builder.add_edge(call_model.__name__, END)

# 使用内存保存器
memory = InMemorySaver()
app = graph_builder.compile(checkpointer=memory)

if __name__ == "__main__":
    # 定义 config
    config = {
        "configurable": {
            "thread_id": "22222"  # 记忆的关键
        }
    }

    # 连续调用几次，模拟多轮对话
    inputs = ["你好", "帮我写一个LangGraph的demo", "记忆在哪里？"]
    for inp in inputs:
        final_state = app.invoke({"input": inp}, config=config)
        print("当前输出:", final_state)

    # # 展示记忆内容
    # print("\n==== 展示记忆 ====")
    # history = memory.list(thread_id="22222")
    # for i, item in enumerate(history, 1):
    #     print(f"Step {i}: {item}")
