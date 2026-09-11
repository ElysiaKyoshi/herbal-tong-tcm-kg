from typing import TypedDict, List


class AgentState(TypedDict):
    # 输入
    input: str
    # 语义转写结果（doc10：由 semantic_transcription_node 结合历史生成）
    input_semantic_trans: str
    # 判断是否有发小红书的意图
    is_xiaohongshu_publish_intent: bool
    # 生成小红书标题和正文
    xiaohongshu_tcm_post_title: str
    xiaohongshu_tcm_post_content: str
    # 生成小红书图片
    xiaohongshu_image_path_list: List[str]
    xiaohongshu_tcm_tip: str
    # 是否可以发布小红书
    is_can_publish_xiaohongshu: bool
    # 小红书markdown输出结果
    xiaohongshu_markdown_output: str
    # 是否跟中医有关系
    is_zhongyi_intent: bool
    # 直接回答
    direct_out: str
    # 用户输入的实体抽取
    user_input_effects: List[str]
    user_input_diseases: List[str]
    user_input_symptoms: List[str]
    user_input_formulas: List[str]
    user_input_herbs: List[str]
    user_input_sources: List[str]
    # 匹配的实体
    matched_effects: List[str]
    matched_diseases: List[str]
    matched_symptoms: List[str]
    matched_formulas: List[str]
    matched_herbs: List[str]
    matched_sources: List[str]
    # cypher查询语句
    cypher_query: List[str]
    is_all_validate_cypher: bool
    # 生成cypher语句的重试次数
    cypher_retry_count: int
    cypher_results: List[dict]
    neo4j_answer: str
    # 输出
    output: str
    # 多轮对话历史（doc10）：user / assistant 消息，随 thread_id 一起持久化
    history_messages: List[dict]
