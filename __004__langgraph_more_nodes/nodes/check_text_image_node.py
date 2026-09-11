from __004__langgraph_more_nodes.agent_state import AgentState


async def check_text_image_node(state: AgentState):
    """检查是否可以发布小红书"""
    title = state.get("xiaohongshu_tcm_post_title", "")
    content = state.get("xiaohongshu_tcm_post_content", "")
    image_path_list = state.get("xiaohongshu_image_path_list", [])
    if not title:
        state["is_can_publish_xiaohongshu"] = False
        state["output"] = "发布小红书失败，标题缺失！"
        return state
    if not content:
        state["is_can_publish_xiaohongshu"] = False
        state["output"] = "发布小红书失败，内容缺失！"
        return state
    if not image_path_list:
        state["is_can_publish_xiaohongshu"] = False
        state["output"] = "发布小红书失败，图片缺失！"
        return state
    # 代码能运行到这里 , 证明标题, 内容, 图片都是完整的看,可以发布
    state["is_can_publish_xiaohongshu"] = True
    return state

if __name__ == '__main__':
    # 测试1：全部字段齐全，应该可以发布
    state1: AgentState = {
        "xiaohongshu_tcm_post_title": "",
        "xiaohongshu_tcm_post_content": "测试内容",
        "xiaohongshu_image_path_list": ["image1.png", "image2.png"],
    }
    import asyncio
    result = asyncio.run(check_text_image_node(state1))
    print(result)