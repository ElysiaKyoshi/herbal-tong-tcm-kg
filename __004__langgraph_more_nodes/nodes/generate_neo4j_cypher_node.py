"""
Generate Neo4j Cypher Node
config实例化, 获取元数据
从state状态中, 获取用户的输入, 节点10匹配到的实体
根据输入, 匹配的实体, 元数据--->生成cypher语句--->把cypher语句保存到state状态中
"""
import json
from __004__langgraph_more_nodes.agent_state import AgentState
from __005__fastapi.__003__msg_queue import put_msg_sentence_content
from common.config import Config
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from common.llm import my_llm

conf = Config()


async def generate_neo4j_cypher_node(state: AgentState, config: RunnableConfig) -> AgentState:
    print("开始生成neo4j的cypher语句")
    user_id = config.get("configurable", {}).get("thread_id")
    await put_msg_sentence_content(user_id, "开始生成neo4j的cypher语句")

    user_input = state["input"]

    # 从 state 取出所有匹配到的实体
    matched_effects = state.get("matched_effects", [])
    matched_diseases = state.get("matched_diseases", [])
    matched_symptoms = state.get("matched_symptoms", [])
    matched_formulas = state.get("matched_formulas", [])
    matched_herbs = state.get("matched_herbs", [])
    matched_sources = state.get("matched_sources", [])

    meta_data = conf.TCM_METADATA  # 知识图谱元数据（节点、关系定义等）

    # 格式化匹配到的实体，确保只保留文本内容
    def format_entities(entities):
        if isinstance(entities, list):
            return [e["text"] if isinstance(e, dict) else str(e) for e in entities]
        return []

    effects_list = format_entities(matched_effects)
    diseases_list = format_entities(matched_diseases)
    symptoms_list = format_entities(matched_symptoms)
    formulas_list = format_entities(matched_formulas)
    herbs_list = format_entities(matched_herbs)
    sources_list = format_entities(matched_sources)

    # 构建提示词
    prompt = f"""
    你是一个 Neo4j Cypher 查询语句生成助手。
    请基于中医知识图谱，结合用户输入和已匹配实体，生成最合适的查询语句。

    用户输入：{user_input}

    匹配到的实体：
    - effects（功效）: {effects_list}
    - diseases（疾病）: {diseases_list}
    - symptoms（症状）: {symptoms_list}
    - formulas（方剂）: {formulas_list}
    - herbs（药材）: {herbs_list}
    - sources（出处）: {sources_list}

    知识图谱元数据（节点与关系定义）：
    {meta_data}

    要求：
    1. 根据用户输入语义、匹配到的实体及元数据，生成 1~N 条合适的 Cypher 查询。
    2. 输出必须是严格的 JSON 格式：
    {{
        "cypher": [
            "MATCH ... RETURN ...",
            "MATCH ... RETURN ..."
        ]
    }}
    3. 不得包含任何解释或额外文字。
    """

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        cypher_data = json.loads(raw_output)
    except json.JSONDecodeError:
        cypher_data = {"cypher": []}

    # 保存结果到 state
    state["cypher_query"] = cypher_data.get("cypher", [])

    print(f"完成生成neo4j的cypher语句{state['cypher_query']}")
    await put_msg_sentence_content(user_id, f"完成生成neo4j的cypher语句{state['cypher_query']}")
    return state

if __name__ == '__main__':
    import asyncio
    result = asyncio.run(generate_neo4j_cypher_node(state={'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。',
     'user_input_symptoms': ['咳嗽'], 'user_input_diseases': ['感冒'], 'user_input_formulas': ['桂枝汤'],
     'user_input_herbs': ['人参', '黄芪'], 'user_input_effects': ['补气', '止痛'], 'user_input_sources': [],
     'matched_effects': ['补气', '补气血', '补气强身', '止痛', '止血止痛', '消炎止痛'], 'matched_diseases': ['感冒'],
     'matched_symptoms': ['咳嗽', '咳'], 'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝附子汤'],
     'matched_herbs': ['人参', '黄芪', '红芪'], 'matched_sources': []}, config={"configurable": {"thread_id": "test_user"}}))
    print(result)

    # 完成生成neo4j的cypher语句[
    #     "MATCH (f:Formula {name: '桂枝汤'}), (h1:Herb {name: '人参'}), (h2:Herb {name: '黄芪'}), (e:Effect {name: '止痛'}) RETURN f, h1, h2, e", "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom {name: '咳嗽'}) RETURN d, s", "MATCH (h:Herb) WHERE h.name IN ['人参', '黄芪'] MATCH (h)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['补气', '止痛'] RETURN h, e"]
    # {'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。',
    #  'user_input_symptoms': ['咳嗽'], 'user_input_diseases': ['感冒'], 'user_input_formulas': ['桂枝汤'],
    #  'user_input_herbs': ['人参', '黄芪'], 'user_input_effects': ['补气', '止痛'], 'user_input_sources': [],
    #  'matched_effects': ['补气', '补气血', '补气强身', '止痛', '止血止痛', '消炎止痛'], 'matched_diseases': ['感冒'],
    #  'matched_symptoms': ['咳嗽', '咳'], 'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝附子汤'],
    #  'matched_herbs': ['人参', '黄芪', '红芪'], 'matched_sources': [], 'cypher_query': [
    #     "MATCH (f:Formula {name: '桂枝汤'}), (h1:Herb {name: '人参'}), (h2:Herb {name: '黄芪'}), (e:Effect {name: '止痛'}) RETURN f, h1, h2, e",
    #     "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom {name: '咳嗽'}) RETURN d, s",
    #     "MATCH (h:Herb) WHERE h.name IN ['人参', '黄芪'] MATCH (h)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['补气', '止痛'] RETURN h, e"]}
