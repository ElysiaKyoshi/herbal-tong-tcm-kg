from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
# 节点0, 语义转写节点（doc10：结合历史把省略句补全成完整问题）
from __004__langgraph_more_nodes.nodes.semantic_transcription_node import semantic_transcription_node
# 节点1, 小红书发布意图识别节点导入
from __004__langgraph_more_nodes.nodes.xiaohongshu_publish_intent_node import xiaohongshu_publish_intent_node
# 节点2, 生成标题与正文的节点
from __004__langgraph_more_nodes.nodes.text_generate_node import text_generate_node
# 节点3, 生成图片的节点
from __004__langgraph_more_nodes.nodes.image_generate_node import image_generator_node
# 节点4, 检查标题, 正文, 生成图片路径是否存在的节点
from __004__langgraph_more_nodes.nodes.check_text_image_node import check_text_image_node
# 节点5, 小红书自动发布节点
from __004__langgraph_more_nodes.nodes.auto_publish_xiaohongshu_node import xiaohongshu_auto_publish_node
# 节点6, 生成html页面 节点
from __004__langgraph_more_nodes.nodes.generate_markdown_node import generate_markdown_node
# 节点7, 判断是否是中医问题
from __004__langgraph_more_nodes.nodes.zhongyi_intent_node import zhongyi_intent_node
# 节点8, 大模型直接回答节点
from __004__langgraph_more_nodes.nodes.llm_direct_out_node import llm_direct_out_node
# 节点9: 抽取用户输入的实体
from __004__langgraph_more_nodes.nodes.extract_entity_from_user_input_node import extract_entity_from_user_input_node
# 节点10: 检索相近的实体
from __004__langgraph_more_nodes.nodes.match_entity_from_neo4j_node import match_entity_from_neo4j_node
# 节点11: 生成cypher语句
from __004__langgraph_more_nodes.nodes.generate_neo4j_cypher_node import generate_neo4j_cypher_node
# 节点12: 检查cypher语句
from __004__langgraph_more_nodes.nodes.check_cypher_node import check_cypher_node
# 节点13: 执行cypher语句
from __004__langgraph_more_nodes.nodes.run_cypher_node import run_cypher_node
# 节点14: 大模型根据知识图谱检索结果生成答案
from __004__langgraph_more_nodes.nodes.neo4j_answer_generate_node import neo4j_answer_generate_node


# 状态
from __004__langgraph_more_nodes.agent_state import AgentState
from common.path_utils import get_file_path
from common.output_graph_utils import output_pic_graph

def build_graph():
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node(semantic_transcription_node.__name__, semantic_transcription_node)
    graph_builder.add_node(xiaohongshu_publish_intent_node.__name__, xiaohongshu_publish_intent_node)
    graph_builder.add_node(text_generate_node.__name__, text_generate_node)
    graph_builder.add_node(image_generator_node.__name__, image_generator_node)
    graph_builder.add_node(check_text_image_node.__name__, check_text_image_node)
    graph_builder.add_node(xiaohongshu_auto_publish_node.__name__, xiaohongshu_auto_publish_node)
    graph_builder.add_node(generate_markdown_node.__name__, generate_markdown_node)

    graph_builder.add_node(zhongyi_intent_node.__name__, zhongyi_intent_node)
    graph_builder.add_node(llm_direct_out_node.__name__, llm_direct_out_node)


    # 知识图谱问答的RAG节点
    graph_builder.add_node(extract_entity_from_user_input_node.__name__, extract_entity_from_user_input_node)
    graph_builder.add_node(match_entity_from_neo4j_node.__name__, match_entity_from_neo4j_node)
    graph_builder.add_node(generate_neo4j_cypher_node.__name__, generate_neo4j_cypher_node)
    graph_builder.add_node(check_cypher_node.__name__, check_cypher_node)
    graph_builder.add_node(run_cypher_node.__name__, run_cypher_node)
    graph_builder.add_node(neo4j_answer_generate_node.__name__, neo4j_answer_generate_node)





    # 入口：先做语义转写（结合历史对话），再进入意图识别
    graph_builder.add_edge(START, semantic_transcription_node.__name__)
    graph_builder.add_edge(semantic_transcription_node.__name__, xiaohongshu_publish_intent_node.__name__)
    def is_xiaohongshu_publish_intent(state: AgentState):
        if state['is_xiaohongshu_publish_intent']:
            return "publish_xiaohongshu_intent"
        else:
            # 改为是否中医问题的节点
            return "zhongyi_intent"

    graph_builder.add_conditional_edges(xiaohongshu_publish_intent_node.__name__,
                                        is_xiaohongshu_publish_intent,
                                        path_map={
                                           "publish_xiaohongshu_intent": text_generate_node.__name__,
                                            "zhongyi_intent": zhongyi_intent_node.__name__
                                        })
    def zhongyi_intent_router(state: AgentState):
        if state['is_zhongyi_intent']:
            return "direct_9_extract_entity_from_user_input"  #改这里, 指向9号节点
        else:
            return "llm_direct"
    graph_builder.add_conditional_edges(zhongyi_intent_node.__name__,
                                        zhongyi_intent_router,
                                        path_map={
                                            "direct_9_extract_entity_from_user_input": extract_entity_from_user_input_node.__name__,
                                            "llm_direct": llm_direct_out_node.__name__
                                        })

    graph_builder.add_edge(llm_direct_out_node.__name__, END)

    graph_builder.add_edge(text_generate_node.__name__,image_generator_node.__name__)
    graph_builder.add_edge(image_generator_node.__name__, check_text_image_node.__name__)
    def check_text_image_router(state:AgentState):
        if state['is_can_publish_xiaohongshu']:
            return "publish_xiaohongshu"
        else:
            return END
    graph_builder.add_conditional_edges(check_text_image_node.__name__,
                                        check_text_image_router,
                                        path_map={
                                           "publish_xiaohongshu": xiaohongshu_auto_publish_node.__name__,
                                            END: END
                                        })
    graph_builder.add_edge(xiaohongshu_auto_publish_node.__name__, generate_markdown_node.__name__)
    graph_builder.add_edge(generate_markdown_node.__name__, END)

    # 9号节点连接10号节点
    graph_builder.add_edge(extract_entity_from_user_input_node.__name__, match_entity_from_neo4j_node.__name__)
    # 10号链接11号
    graph_builder.add_edge(match_entity_from_neo4j_node.__name__, generate_neo4j_cypher_node.__name__)
    # 11号链接12号
    graph_builder.add_edge(generate_neo4j_cypher_node.__name__, check_cypher_node.__name__)
    # 12号进入条件边, 如果检查OK, 进入13号节点运行cypher; 如果不行, 就重新生成cypher, 跳转到11号节点

    def check_cypher_router(state:AgentState):
        if state['is_all_validate_cypher']:
            # cypyer语句正常, 跳到执行cypher节点
            return "run_cypher"
        elif state.get('cypher_retry_count', 0) >= 3:
            # 生成cypher语句重试次数超过3次了, 不再继续生成cypher,无法查询数据库, 跳到答案生成节点
            return "generate_answer"
        else:
            # cypyer语句不正常, 同时重试次数也没有超过3次, 跳到生成cypher节点
            return "generate_neo4j_cypher"

    graph_builder.add_conditional_edges(check_cypher_node.__name__, check_cypher_router,
                                        path_map={
                                          "run_cypher": run_cypher_node.__name__ ,
                                          "generate_neo4j_cypher":generate_neo4j_cypher_node.__name__,
                                          "generate_answer": neo4j_answer_generate_node.__name__
                                        })
    graph_builder.add_edge(run_cypher_node.__name__, neo4j_answer_generate_node.__name__)

    graph_builder.add_edge(neo4j_answer_generate_node.__name__, END)


    # 用 InMemorySaver 按 thread_id 保存会话状态，实现多轮记忆（doc10）
    memory = InMemorySaver()
    graph_builder = graph_builder.compile(memory)
    return graph_builder


graph = build_graph()
output_pic_graph(graph, get_file_path("__004__langgraph_more_nodes/graph.png"))


async def zhongyi_response(input: str, user_id: str = "default"):
    """user_id 同时作为 LangGraph 的 thread_id：同一 user_id 的多轮提问共享历史。"""
    config = {"configurable": {"thread_id": user_id}}
    result = await graph.ainvoke({"input": input}, config)
    return result["output"]

if __name__ == '__main__':
    import asyncio
    # asyncio.run(zhongyi_response("我想发布小红书, 关于中医方面的", "user_001"))
    result = asyncio.run(zhongyi_response("我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。", "user_001"))
    print("Langgraph基于知识图谱问答的生成结果:")
    print(result)
    pass
