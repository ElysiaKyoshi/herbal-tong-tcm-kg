from typing import TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command


class MyState(TypedDict):
    input: str
    output: str


# 定义节点逻辑
def call_model(state: MyState):
    input_text = state['input']
    #  停止了，等待人工介入
    print("interrupt前")
    a = interrupt("你好啊")
    print("interrupt后" + a)
    state['output'] = input_text + a

    b = interrupt({"hello": "heima"})
    state['output'] = state['output'] + b
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
    final_state = app.invoke({"input": "你是好人！"}, config=config)
    print(final_state)

    person_input = input("请进行人工输入:")
    state = app.invoke(Command(resume=person_input), config=config)
    print(state)

    person_input2 = input("请进行人工输入2:")
    state = app.invoke(Command(resume=person_input2), config=config)
    print(state)
