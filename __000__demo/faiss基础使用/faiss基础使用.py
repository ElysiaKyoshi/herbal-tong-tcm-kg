import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

from common.embedding_model import embedding_model


def build_faiss_index(sentences, index_path="faiss.index", mapping_path="id2text.pkl"):
    """
    基于字符串列表构建 FAISS 索引并保存
    :param sentences: List[str] 输入的文本列表
    :param index_path: FAISS 索引保存路径
    :param mapping_path: id->原始文本映射保存路径
    """
    # 1. 加载预训练文本向量模型

    # 2. 生成向量
    embeddings = embedding_model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
    print("embeddings.shape:", embeddings.shape)
    # 3. 构建 FAISS 索引
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)  # L2距离,欧式距离
    index.add(embeddings)

    # 4. 保存索引
    faiss.write_index(index, index_path)

    # 5. 保存 id -> 原始文本 映射
    id2text = {i: s for i, s in enumerate(sentences)}
    with open(mapping_path, "wb") as f:
        pickle.dump(id2text, f)

    print(f"✅ 索引已保存到 {index_path}, 映射保存到 {mapping_path}")


def search_faiss(query, index_path="faiss.index", mapping_path="id2text.pkl", top_k=3, threshold=0.85):
    """
    在已有的 FAISS 索引中搜索，并设置相似度阈值
    """
    # 加载索引和映射
    index = faiss.read_index(index_path)
    with open(mapping_path, "rb") as f:
        id2text = pickle.load(f)

    # 生成查询向量
    query_emb = embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

    # 检索 (返回 L2 距离)
    dists, ids = index.search(query_emb, top_k)

    results = []
    for j, i in enumerate(ids[0]):
        if i == -1:  # 没找到
            continue
        dist = dists[0][j]
        sim = 1.0 - dist / 2.0  # 转换成余弦相似度
        if sim >= threshold:
            results.append((id2text[i], sim))

    return results


if __name__ == "__main__":
    # 示例数据
    sentences = [
        "苹果公司发布了新款iPhone",
        "谷歌推出了最新的AI模型",
        "特斯拉在中国市场销量大增",
        "微软宣布收购一家游戏公司"
    ]

    # 构建并保存索引
    build_faiss_index(sentences)

    # 查询
    query = "微软宣布收购一家游戏公司哈哈哈"
    results = search_faiss(query)
    print("🔍 查询结果:")
    for text, score in results:
        print(f"  {text} (score={score:.4f})")
