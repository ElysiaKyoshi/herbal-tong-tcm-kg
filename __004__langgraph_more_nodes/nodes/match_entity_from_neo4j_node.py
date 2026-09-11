import faiss
import numpy as np
import pickle
from langchain_core.runnables import RunnableConfig
from __004__langgraph_more_nodes.agent_state import AgentState
from __005__fastapi.__003__msg_queue import put_msg_sentence_content
from common.config import Config
from common.embedding_model import embedding_model

conf = Config()

# 加载索引和映射
# 注意：faiss 的 C++ 层在 Windows 上用 ANSI fopen 打开文件，项目路径含中文时
# faiss.read_index 会报 "No such file or directory"。改用 Python 读字节流 + 反序列化。
with open(conf.ENTITY_INDEX_PATH, "rb") as _index_file:
    index = faiss.deserialize_index(np.frombuffer(_index_file.read(), dtype="uint8"))
with open(conf.ENTITY_ID2TEXT_PATH, "rb") as f:
    # 保存的是id-->text的映射
    id2text = pickle.load(f)


def search_faiss(query, top_k=3, threshold=0.85):
    """
    在已有的 FAISS 索引中搜索，并设置相似度阈值
    """
    print("开始从faiss索引搜索")

    # 用户的query中的实体名字, 生成查询向量
    query_emb = embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

    # 检索 (返回 L2 距离)
    # dists: 距离
    # ids: 检索到的最相近的topk个id
    dists, ids = index.search(query_emb, top_k)
    # print(f"=================ids:{ids}=====================")
    # print(f"=================dists:{dists}=====================")
    # a = input()
    results = []
    for j, i in enumerate(ids[0]):
        if i == -1:  # 没找到
            continue
        dist = dists[0][j]
        sim = 1.0 - dist / 2.0  # 转换成余弦相似度
        if sim >= threshold: #相似度超过阈值
            results.append({"text": id2text[i], "similarity": float(sim)})
    print("完成从faiss索引搜索")
    return [result['text'] for result in results]


async def match_entity_from_neo4j_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
        对六类实体分别在 FAISS 索引中进行匹配搜索：
        - Effect（功效）
        - Disease（疾病）
        - Symptom（症状）
        - Formula（方剂）
        - Herb（药材）
        - Source（出处）
        """
    user_id = config.get("configurable", {}).get("thread_id")
    # 1.用户输入的实体
    user_input_effects = state.get("user_input_effects", [])
    user_input_diseases = state.get("user_input_diseases", [])
    user_input_symptoms = state.get("user_input_symptoms", [])
    user_input_formulas = state.get("user_input_formulas", [])
    user_input_herbs = state.get("user_input_herbs", [])
    user_input_sources = state.get("user_input_sources", [])

    # 2.匹配到相关联的实体
    matched_effects, matched_diseases, matched_symptoms = [], [], []
    matched_formulas, matched_herbs, matched_sources = [], [], []

    # 分别在 FAISS 中检索
    for eff in user_input_effects:
        matched_effects.extend(search_faiss(eff))

    for dis in user_input_diseases:
        matched_diseases.extend(search_faiss(dis))

    for sym in user_input_symptoms:
        matched_symptoms.extend(search_faiss(sym))

    for form in user_input_formulas:
        matched_formulas.extend(search_faiss(form))

    for herb in user_input_herbs:
        matched_herbs.extend(search_faiss(herb))

    for src in user_input_sources:
        matched_sources.extend(search_faiss(src))

    # 存入 state
    state["matched_effects"] = matched_effects
    state["matched_diseases"] = matched_diseases
    state["matched_symptoms"] = matched_symptoms
    state["matched_formulas"] = matched_formulas
    state["matched_herbs"] = matched_herbs
    state["matched_sources"] = matched_sources

    print("完成实体匹配搜索")
    await put_msg_sentence_content(user_id, "完成实体匹配搜索")
    return state


if __name__ == '__main__':
    import asyncio
    print(asyncio.run(match_entity_from_neo4j_node(
        {'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。',
         'user_input_symptoms': ['咳嗽'],
         'user_input_diseases': ['感冒'],
         'user_input_formulas': ['桂枝汤'],
         'user_input_herbs': ['人参', '黄芪'],
         'user_input_effects': ['补气', '止痛'],
         'user_input_sources': []}, config={"configurable": {"thread_id": "test_user"}})))

    # {'input': '我最近感冒了，有点咳嗽。我打算喝点桂枝汤，里面有人参和黄芪，希望能补气止痛。',
    #  'user_input_symptoms': ['咳嗽'], 'user_input_diseases': ['感冒'], 'user_input_formulas': ['桂枝汤'],
    #  'user_input_herbs': ['人参', '黄芪'], 'user_input_effects': ['补气', '止痛'], 'user_input_sources': [],
    #  'matched_effects': ['补气', '补气血', '补气强身', '止痛', '止血止痛', '消炎止痛'], 'matched_diseases': ['感冒'],
    #  'matched_symptoms': ['咳嗽', '咳'], 'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝附子汤'],
    #  'matched_herbs': ['人参', '黄芪', '红芪'], 'matched_sources': []}