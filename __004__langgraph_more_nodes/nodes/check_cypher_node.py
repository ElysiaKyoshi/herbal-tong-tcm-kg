from langchain_core.runnables import RunnableConfig
from __004__langgraph_more_nodes.agent_state import AgentState
from __005__fastapi.__003__msg_queue import put_msg_sentence_content
from common.neo4j_manager import neo4j_client


async def check_cypher_node(state:AgentState, config: RunnableConfig):
    print("开始检查cypher语句")
    user_id = config.get("configurable", {}).get("thread_id")
    await put_msg_sentence_content(user_id, "开始检查cypher语句")
    cypher_query_list = state["cypher_query"]
    state['is_all_validate_cypher'] = True
    for cypher_query in cypher_query_list:
        if not neo4j_client.validate_cypher(cypher_query):
            state['is_all_validate_cypher'] = False
            break
    if not state['is_all_validate_cypher']:
        state['cypher_retry_count'] = state.get('cypher_retry_count', 0) + 1
        if state['cypher_retry_count'] >= 3:
            state['cypher_results'] = []
    print(f"完成检查cypher语句:{state['is_all_validate_cypher']}, 重试次数:{state.get('cypher_retry_count', 0)}")
    await put_msg_sentence_content(user_id, f"完成检查cypher语句:{state['is_all_validate_cypher']}, 重试次数:{state.get('cypher_retry_count', 0)}")
    return state


if __name__ == '__main__':
    import asyncio
    result = asyncio.run(check_cypher_node({'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。',
     'user_input_symptoms': ['咳嗽'], 'user_input_diseases': ['感冒'], 'user_input_formulas': ['桂枝汤'],
     'user_input_herbs': ['人参', '黄芪'], 'user_input_effects': ['补气', '止痛'], 'user_input_sources': [],
     'matched_effects': ['补气', '补气血', '补气强身', '止痛', '止血止痛', '消炎止痛'], 'matched_diseases': ['感冒'],
     'matched_symptoms': ['咳嗽', '咳'], 'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝附子汤'],
     'matched_herbs': ['人参', '黄芪', '红芪'], 'matched_sources': [], 'cypher_query': [
        "MATCH (f:Formula {name: '桂枝汤'}), (h1:Herb {name: '人参'}), (h2:Herb {name: '黄芪'}), (e:Effect {name: '止痛'}) RETURN f, h1, h2, e",
        "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom {name: '咳嗽'}) RETURN d, s",
        "MATCH (h:Herb) WHERE h.name IN ['人参', '黄芪'] MATCH (h)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['补气', '止痛'] RETURN h, e"]},
     config={"configurable": {"thread_id": "test_user"}})
)
    print(result)