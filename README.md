# 草本通 · 中医药知识图谱问答系统

> 中医药领域的知识图谱问答（KGQA）系统：**爬虫采集 → 大模型实体关系抽取 → Neo4j 图谱 + FAISS 向量检索 → LangGraph 多智能体问答（多轮记忆 + 流式输出） → FastAPI + Streamlit**，并附 **QLoRA 微调**（让本地小模型直出抽取结果）。

本项目是课程实训项目的**完整复现与修正版**：从零跑通了全部模块，并修掉了原始参考代码中若干真实缺陷（见[§6](#6-相对课程文档的修正)）。

---

## ⚠️ 内容范围与免责声明

- 本仓库**只包含本人编写的项目源码**，**不包含**课程视频、课程笔记、讲师参考代码、爬取语料、抽取结果、图谱数据、向量索引与模型权重。
- 仓库中出现的接口地址、参数与提示词仅用于学习；**所有密钥一律通过 `.env` 提供**（见 `.env.example`），仓库内不含任何真实凭据。
- 中医药内容仅作技术演示，**不构成医疗建议**。

---

## 1. 功能特性

| 模块 | 说明 |
|---|---|
| 数据采集 | `requests` + `BeautifulSoup` 抓取中医百科的方剂/中药目录与详情 |
| 实体关系抽取 | DeepSeek + LangChain + Pydantic 结构化输出，批量遍历语料落 JSON |
| 知识图谱 | `MERGE` 实体/关系导入 Neo4j（实测规模：**10,745 节点 / 25,835 关系**） |
| 向量检索 | `bge-large-zh-v1.5` + FAISS，对六类实体做语义近似匹配 |
| 多智能体问答 | LangGraph 14 个节点：意图识别 → 实体抽取 → 向量匹配 → 生成/校验/执行 Cypher → 图谱答案；非中医问题走大模型直答 |
| 多轮记忆 | `InMemorySaver` + `thread_id`，语义转写节点把「它还能治什么病？」补全为完整问题 |
| 流式输出 | 各节点通过 `asyncio.Queue` 推送思考过程，FastAPI 行式 JSON 流 → Streamlit 逐段渲染 |
| 小红书链路 | 文案生成 → 即梦生图 → Playwright 自动发布 → 生成 HTML 汇总（需人工登录，默认不启用） |
| 模型微调 | QLoRA 微调 Qwen2.5 系列，使小模型直接输出知识图谱 JSON |

## 2. 系统架构

```
中医百科(zhongyibaike.com)
      │  requests + BeautifulSoup
      ▼
 语料 txt ──► DeepSeek + LangChain 实体关系抽取 ──► JSON
      │                                              │
      │                                              ▼
      │                              Neo4j（实体/关系/属性）  +  FAISS（bge 向量）
      │                                              │
      ▼                                              ▼
              ┌───────────── LangGraph 多智能体 ─────────────┐
              │ START → 语义转写（结合历史）→ 意图识别        │
              │   ├─ 中医问题 → 抽实体 → FAISS 匹配 → 生成   │
              │   │            Cypher → 校验 →（重试≤3）执行  │
              │   │            → 依据图谱结果生成答案        │
              │   ├─ 非中医   → 大模型直答                   │
              │   └─ 小红书   → 文案 → 生图 → 发布 → markdown │
              └───────────────────────┬─────────────────────┘
                                      ▼
                     FastAPI（/process 流式 + /picture 静态）
                                      ▼
                          Streamlit 对话界面（含多轮/思考过程）
```

图谱结构（自动生成，见 `__004__langgraph_more_nodes/graph.png`）：

- 实体 6 类：`Formula` `Herb` `Disease` `Symptom` `Effect` `Source`
- 关系 6 类：`HAS_INGREDIENT` `TREATS_DISEASE` `ALLEVIATES_SYMPTOM` `HAS_EFFECT` `HAS_SYMPTOM` `FROM_SOURCE`

## 3. 目录结构

```
common/                       公共模块（配置/LLM/Neo4j/向量模型/路径/绘图）
__000__demo/                  各技术点小样（FAISS、LangGraph、FastAPI、爬虫、提示词库）
__001__clawler/               爬虫：方剂/中药 目录与详情
__002__extract_information/   实体关系抽取（DeepSeek + LangChain + Pydantic）
__003__create_neo4j_database/ 图谱导入、元数据导出、FAISS 索引构建
__004__langgraph_more_nodes/  LangGraph 图定义 + agent_state + 14 个节点
__005__fastapi/               后端接口与消息队列（流式）
__006__streamlit/             对话前端
__007__fine_tune/             QLoRA 微调：数据集配置与 LLaMA-Factory 训练 yaml
__008__graphrag/              GraphRAG 试验（可选）
__009__lightrag/              LightRAG 接口调用（可选）
```

## 4. 快速开始

### 4.1 环境

```bash
conda create -n ctm_kg python=3.10 -y
conda activate ctm_kg
pip install -r requirements.txt
playwright install chromium        # 仅小红书自动发布需要
```

外部依赖：**Neo4j**（4.4+/5.x/2026.x 均可，实测 2026.03.1）、**bge-large-zh-v1.5** 本地权重目录、一个 DeepSeek 兼容的大模型端点。

### 4.2 配置

```bash
cp .env.example .env    # 然后填入自己的 key / 密码 / 模型路径
```

### 4.3 数据管线（仓库不含数据，需自行生成）

```bash
python __001__clawler/__001__get_formula_menu_list.py     # 方剂目录
python __001__clawler/__002__get_formula_detail_info.py   # 方剂详情
python __001__clawler/__003__get_herb_menu_list.py        # 中药目录
python __001__clawler/__004__get_herb_detail_list.py      # 中药详情
python __002__extract_information/__001__extract_herb_data.py      # 抽取（会调大模型）
python __002__extract_information/__002__extract_formula_data.py
python __003__create_neo4j_database/__001__graph_importer.py       # 导入 Neo4j
python __003__create_neo4j_database/__002__export_metadata.py      # 导出 tcm_metadata.json
python __003__create_neo4j_database/__003__faiss_embedding.py      # 构建 FAISS 索引
```

> 所有脚本都依赖 `PYTHONPATH` 指向项目根目录，例如：
> `set PYTHONPATH=%cd%`（Windows）/ `export PYTHONPATH=$PWD`（Linux/macOS）

### 4.4 启动服务

```bash
# 后端（含 /process 流式问答与 /picture 静态图片）
python __005__fastapi/__001__langgraph_fastapi.py          # http://127.0.0.1:8000

# 前端
python -m streamlit run __006__streamlit/langgraph_streamlit.py   # http://localhost:8501
```

### 4.5 直接命令行问答

```bash
python __004__langgraph_more_nodes/langgraph_more_nodes.py
```

## 5. 多轮对话与流式输出

- **多轮记忆**：`langgraph_more_nodes.zhongyi_response(input, user_id)` 把 `user_id` 当作 LangGraph 的 `thread_id`，图用 `InMemorySaver()` 编译；`AgentState.history_messages` 随线程持久化。
- **语义转写**：入口节点 `semantic_transcription_node` 用最近若干轮历史把省略句补全（实测：「它还能治什么病？」→「当归还能治疗哪些疾病？」），并**回写 `state["input"]`** 供下游使用。
- **逐节点流式**：各节点通过 `__005__fastapi/__003__msg_queue.py` 的 `put_msg_sentence_content` / `put_reply_content` 推入按 `user_id` 隔离的 `asyncio.Queue`；后端以**行分隔 JSON** 输出，前端按行缓冲解析。
- **会话隔离**：不同 `user_id` 的历史互不可见（实测：新会话问同样的省略句，模型会要求补充主语）。

## 6. 相对课程文档的修正

复现过程中发现并修掉了以下真实缺陷（均为「跑不通」级别，非风格问题）：

| # | 位置 | 问题 | 修法 |
|---|---|---|---|
| 1 | `common/path_utils.py` | 只定义 `root_dir`，但节点导入 `root_path` → `ImportError` | 增加别名 `root_path = root_dir` |
| 2 | `common/output_graph_utils.py`（新增） | 图模块导入 `common.output_graph_utils`，实际文件名是 `ouput_graph_utils.py`（少个 t） | 新增垫片重导出 `output_pic_graph` |
| 3 | `nodes/match_entity_from_neo4j_node.py` | `faiss.read_index` 在**含中文的项目路径**下报 “No such file or directory”（faiss C++ 层用 ANSI `fopen`） | 改为 Python 读字节流 + `faiss.deserialize_index` |
| 4 | `__003__create_neo4j_database/__003__faiss_embedding.py` | `faiss.write_index` 同样受中文路径限制 | 改为 `faiss.serialize_index` + Python 写出 |
| 5 | `nodes/semantic_transcription_node.py` | 只写 `input_semantic_trans`，而下游都读 `state["input"]` → 多轮实际不生效 | 语义转写结果同时回写 `state["input"]` |
| 6 | `__005__fastapi/__001__langgraph_fastapi.py` + 前端 | 后端 `json.dumps(msg)` 裸拼接，TCP 粘包时前端 `json.loads` 崩溃 | 后端改为行分隔 JSON，前端按行缓冲 |
| 7 | 9 个节点 | 无流式推送、无历史记录 | 统一改为 `async def (state, config)`，加 `put_*` 推流与 `history_messages` 追加 |

## 7. 模型微调（QLoRA）

目标：让本地小模型直接完成「中医文本 → 知识图谱 JSON」的抽取，替代每次调用大模型。

### 7.1 显存实测决定基座选型（RTX 3060 Laptop 6GB）

| 序列长度 | 4-bit QLoRA 峰值显存（1.5B） |
|---|---|
| 512 | 2.76 GB |
| 1024 | 4.01 GB |
| 1536 | ❌ 触发驱动级 `device not ready`（超限） |

语料 token 分布：prompt 中位 698；**response(JSON) 中位 995 / p90 1676**；`prompt+response ≤ 1024` 的样本仅 **15%**。
→ 6GB 显存上 1.5B 可用 `cutoff_len` 上限约 1024，**装不下本语料的目标 JSON**（硬训会截断 JSON 目标）。故改用 **Qwen2.5-0.5B-Instruct**（文档同时列出的备选基座），可完整跑 `cutoff_len=2048`。

### 7.2 训练配置与结果

| 项 | 值 |
|---|---|
| 数据 | `zhongyi_zh_2048.json`：1,217 条（从 1,959 条按 ≤2048 tokens 过滤，保证目标不截断） |
| 方法 | LoRA r=8 / alpha=16 / dropout=0.05 / target=`q_proj,v_proj`，template=qwen |
| 超参 | cutoff_len=2048、batch=1、梯度累积=8、lr=2e-4、cosine、3 epoch、bf16、梯度检查点 |
| 结果 | **train_loss 0.0532**，459 步，耗时 **1 小时 1 分**（7.4 秒/步） |
| 产物 | `adapter_model.safetensors` 2.07 MB（LoRA 适配器） |

环境见 `requirements-finetune.txt`（**新版 LLaMA-Factory 需要 Python ≥3.11**；本机实测 Python 3.12.7 + torch 2.14.0+cu126 + LLaMA-Factory 0.9.6.dev0 + bitsandbytes 0.50.2）。

### 7.3 效果验证（基座 vs LoRA）

| 用例 | 参考答案 | 基座 0.5B | LoRA |
|---|---|---|---|
| 训练集样本（271 tok） | 12 实体 / 12 关系 | ❌ 输出 markdown 列表，**不是 JSON** | ✅ 13 / 13 |
| 未训练长样本（588 tok） | 23 / 22 | ❌ 非 JSON | ✅ **23 / 22（与参考完全一致）** |
| 爬虫原始文本（1397 tok，未见） | — | ❌ 非 JSON | ✅ 8 实体 / 7 关系，schema 合法 |

**结论**：基座 0/3 能输出要求的 JSON，LoRA 3/3 合法 → 微调达成目标。

> ⚠️ **方法学坑（务必注意）**：`PeftModel.from_pretrained(base, ...)` 会**原地替换** `base` 的 Linear 层，直接比较 `base` 与 `peft_model` 得到的是「LoRA vs LoRA」（两边输出逐字相同）。正确做法是在同一模型上用：
> ```python
> with model.disable_adapter():      # 基座
>     base_out = generate(model, prompt)
> lora_out = generate(model, prompt) # 激活 LoRA
> ```

## 8. 已知限制

1. **小红书自动发布**需人工扫码登录（节点内含阻塞式 `input()` 与 `headless=False`），不适合无人值守；默认不启用。
2. **vLLM 部署**（文档后续步骤）Windows 原生不支持，需 WSL2 或 Linux 云端。
3. **1.5B/7B 基座微调**需 ≥12GB 显存；WSL 与 Windows 共享同一张显卡，无法绕过。
4. 0.5B 在长原文（>1000 tokens）上的抽取精度有限，实体类型分布可能偏离。
5. `history_num=5` 只截断「送入提示词的条数」，状态内历史仍会增长（沿用原参考实现的行为）。
6. 语料抓取自公开中医百科站点，仅供学习研究，请遵守目标站 robots 与版权要求。

## 9. 技术栈

Python 3.10 · Neo4j · LangChain · LangGraph · DeepSeek API · FAISS · sentence-transformers(bge-large-zh-v1.5) · FastAPI · Streamlit · Playwright · LLaMA-Factory(QLoRA)

## 10. 说明

课程实训项目复现，仅用于学习与技术交流。原始 11 篇课程文档为内部资料，未随仓库发布。
