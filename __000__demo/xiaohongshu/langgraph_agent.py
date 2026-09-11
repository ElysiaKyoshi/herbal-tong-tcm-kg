from langgraph.graph import StateGraph, END

from __000__demo.xiaohongshu.agent.text_generate_agent import XiaohongshuTCMPostAgent
from __000__demo.xiaohongshu.agent.image_generate_agent import XiaohongshuImageGeneratorAgent
from __000__demo.xiaohongshu.agent.auto_publish_xiaohongshu_agent import XiaohongshuAutoPublishAgent
from __000__demo.xiaohongshu.agent_state import AgentState

# 构建 LangGraph 状态图
graph = StateGraph(AgentState)
# 添加各个代理节点到状态图
graph.add_node(XiaohongshuTCMPostAgent.__name__, XiaohongshuTCMPostAgent())
graph.add_node(XiaohongshuImageGeneratorAgent.__name__, XiaohongshuImageGeneratorAgent())
graph.add_node(XiaohongshuAutoPublishAgent.__name__, XiaohongshuAutoPublishAgent())

# 设置进入图节点入口
graph.set_entry_point(XiaohongshuTCMPostAgent.__name__)
graph.add_edge(XiaohongshuTCMPostAgent.__name__, XiaohongshuImageGeneratorAgent.__name__)
graph.add_edge(XiaohongshuImageGeneratorAgent.__name__, XiaohongshuAutoPublishAgent.__name__)
graph.add_edge(XiaohongshuAutoPublishAgent.__name__, END)

# 编译状态图
app = graph.compile()

if __name__ == '__main__':
    result = app.invoke({"input": "关于喝可乐"})
    print(result)