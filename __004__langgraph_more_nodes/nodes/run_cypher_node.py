from langchain_core.runnables import RunnableConfig
from __004__langgraph_more_nodes.agent_state import AgentState
from __005__fastapi.__003__msg_queue import put_msg_sentence_content
from common.neo4j_manager import neo4j_client


async def run_cypher_node(state: AgentState, config: RunnableConfig):
    print("开始运行大模型cypher语句")
    user_id = config.get("configurable", {}).get("thread_id")
    await put_msg_sentence_content(user_id, "开始运行大模型cypher语句")
    cypher_query_list = state.get("cypher_query", [])
    query_results = []

    for cypher_query in cypher_query_list:
        result_list = neo4j_client.run_cypher(cypher_query)
        query_results.append({
            "query": cypher_query,
            "result": result_list
        })

    # 存入 state
    state["cypher_results"] = query_results
    print("完成运行大模型cypher语句")
    await put_msg_sentence_content(user_id, "完成运行大模型cypher语句")
    return state

if __name__ == '__main__':
    import asyncio
    result = asyncio.run(run_cypher_node({'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。', 'user_input_symptoms': ['咳嗽'], 'user_input_diseases': ['感冒'], 'user_input_formulas': ['桂枝汤'], 'user_input_herbs': ['人参', '黄芪'], 'user_input_effects': ['补气', '止痛'], 'user_input_sources': [], 'matched_effects': ['补气', '补气血', '补气强身', '止痛', '止血止痛', '消炎止痛'], 'matched_diseases': ['感冒'], 'matched_symptoms': ['咳嗽', '咳'], 'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝附子汤'], 'matched_herbs': ['人参', '黄芪', '红芪'], 'matched_sources': [], 'cypher_query': ["MATCH (f:Formula {name: '桂枝汤'}), (h1:Herb {name: '人参'}), (h2:Herb {name: '黄芪'}), (e:Effect {name: '止痛'}) RETURN f, h1, h2, e", "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom {name: '咳嗽'}) RETURN d, s", "MATCH (h:Herb) WHERE h.name IN ['人参', '黄芪'] MATCH (h)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['补气', '止痛'] RETURN h, e"], 'is_all_validate_cypher': True}, config={"configurable": {"thread_id": "test_user"}})
)
    print(result)
    # {'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。',
    #  'user_input_symptoms': ['咳嗽'], 'user_input_diseases': ['感冒'], 'user_input_formulas': ['桂枝汤'],
    #  'user_input_herbs': ['人参', '黄芪'], 'user_input_effects': ['补气', '止痛'], 'user_input_sources': [],
    #  'matched_effects': ['补气', '补气血', '补气强身', '止痛', '止血止痛', '消炎止痛'], 'matched_diseases': ['感冒'],
    #  'matched_symptoms': ['咳嗽', '咳'], 'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝附子汤'],
    #  'matched_herbs': ['人参', '黄芪', '红芪'], 'matched_sources': [], 'cypher_query': [
    #     "MATCH (f:Formula {name: '桂枝汤'}), (h1:Herb {name: '人参'}), (h2:Herb {name: '黄芪'}), (e:Effect {name: '止痛'}) RETURN f, h1, h2, e",
    #     "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom {name: '咳嗽'}) RETURN d, s",
    #     "MATCH (h:Herb) WHERE h.name IN ['人参', '黄芪'] MATCH (h)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['补气', '止痛'] RETURN h, e"],
    #  'is_all_validate_cypher': True, 'cypher_results': [{
    #                                                         'query': "MATCH (f:Formula {name: '桂枝汤'}), (h1:Herb {name: '人参'}), (h2:Herb {name: '黄芪'}), (e:Effect {name: '止痛'}) RETURN f, h1, h2, e",
    #                                                         'result': [{'f': {'effect': '解肌发表，调和营卫',
    #                                                                           'usage': '现在常用于半身汗出，效果颇佳；成人遗尿，加龙骨、牡蛎；以及遗精早泄等证',
    #                                                                           'name': '桂枝汤',
    #                                                                           'indication': '外感风寒表虚证。头痛发热，汗出恶风，鼻鸣干呕，苔白不渴，脉浮缓或浮弱者'},
    #                                                                     'h1': {'dosage': '3克', 'meridian': '脾经、肺经',
    #                                                                            'taboo': '实证、热证忌服。不宜与藜芦同用',
    #                                                                            'effect': '大补元气，固脱生津，安神',
    #                                                                            'name': '人参',
    #                                                                            'alias': '棒锤、山参、园参、参叶',
    #                                                                            'processing': '糖参类：除去芦头，切段即可；红参类：除去芦头，切段。或以湿布包襄，润软后切片，晾干',
    #                                                                            'indication': '劳伤虚损，食少，倦怠，反胃吐食，大便滑泄，虚咳喘促，自汗暴脱，惊悸，健忘，眩晕头痛，阳痿，尿频，消渴，妇女崩漏，小儿慢惊，及久虚不复，一切气血津液不足之证',
    #                                                                            'property_flavor': '甘微苦，温'},
    #                                                                     'h2': {'dosage': '内服：煎汤，9～30g',
    #                                                                            'meridian': '归肺经、脾经',
    #                                                                            'origin': '为豆科黄芪属植物膜荚黄芪Astragalus membranaceus （Fisch.） Bunge 及内蒙古黄芪A. mongholicus Bunge的根',
    #                                                                            'effect': '补气固表，利尿托毒，排脓，敛疮生肌',
    #                                                                            'name': '黄芪',
    #                                                                            'processing': '蜜黄芪：将黄芪片加炼熟的蜂蜜与少许开水，拌匀稍闷，放锅内炒至黄色并不粘手时，取出晾凉（每100斤用炼熟的蜂蜜25斤）',
    #                                                                            'indication': '用于气虚乏力，食少便溏，中气下陷，久泻脱肛，便血崩漏，表虚自汗，气虚水肿，痈疽难溃，久溃不敛，血虚痿黄，内热消渴；慢性肾炎蛋白尿，糖尿病',
    #                                                                            'property_flavor': '甘，温'},
    #                                                                     'e': {'name': '止痛'}}]}, {
    #                                                         'query': "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom {name: '咳嗽'}) RETURN d, s",
    #                                                         'result': []}, {
    #                                                         'query': "MATCH (h:Herb) WHERE h.name IN ['人参', '黄芪'] MATCH (h)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['补气', '止痛'] RETURN h, e",
    #                                                         'result': [{'h': {'dosage': '3克', 'meridian': '脾经、肺经',
    #                                                                           'taboo': '实证、热证忌服。不宜与藜芦同用',
    #                                                                           'effect': '大补元气，固脱生津，安神',
    #                                                                           'name': '人参',
    #                                                                           'alias': '棒锤、山参、园参、参叶',
    #                                                                           'processing': '糖参类：除去芦头，切段即可；红参类：除去芦头，切段。或以湿布包襄，润软后切片，晾干',
    #                                                                           'indication': '劳伤虚损，食少，倦怠，反胃吐食，大便滑泄，虚咳喘促，自汗暴脱，惊悸，健忘，眩晕头痛，阳痿，尿频，消渴，妇女崩漏，小儿慢惊，及久虚不复，一切气血津液不足之证',
    #                                                                           'property_flavor': '甘微苦，温'},
    #                                                                     'e': {'name': '补气'}}]}]}
