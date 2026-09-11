> 📌 **本文说明**：这是本人复现该课程项目的**过程记录**（环境、踩坑、代码修正、实测数据与验证结论），
> **不包含课程文档原文**；文中绝对路径与密钥均已脱敏。
> 快速上手请看仓库根目录的 [README](../README.md)。

---

# 「草本通」中医药知识图谱问答系统 —— 复现报告

- 复现日期：2026-09-11
- 项目位置：`<项目根>`（**就地复现**，未改动目录结构）
- 复现程度：**最小可用版已端到端跑通**（爬虫成果 → 抽取结果 → Neo4j 图谱 → LangGraph 多智能体问答 → FastAPI → Streamlit）

---

## 一、文档获取

11 篇飞书文档原始链接均需登录，无法直接抓取。改用本机已有的飞书 CLI 以**用户身份**导出：

- CLI：`C:\Users\Elysia\AppData\Local\Qianwen\User Data\qwen-agent\resources\tools\npm\22.14.0\_larksuite_cli_1.0.84\payload\node_modules\@larksuite\cli\bin\lark-cli.exe`
- 应用：`cli_aaf78cca0eb89cc1`（用户 `飞书用户6171PF`，凭据存于 Windows 凭据管理器）
- 命令：`lark-cli docs +fetch --doc <url> --doc-format markdown --format json`
- 产物：`<复现工作目录>\docs\doc01~doc11-*.md`（11 篇全文）

文档内容规格抽取（逐字代码 + 规格 + 歧义点）：

| 文件 | 覆盖内容 |
|---|---|
| `<复现工作目录>\docs\spec\A-common-and-crawler.md` | .env、path_utils、config、llm、neo4j_manager、output_graph_utils、爬虫 4 脚本 |
| `<复现工作目录>\docs\spec\B-extraction-and-graph.md` | 实体关系定义与抽取（DeepSeek+LangChain）、Neo4j 导入导出 |
| `<复现工作目录>\docs\spec\C-langgraph-agents.md` | LangGraph 14 节点、AgentState 28 字段、条件路由、Prompt |
| `<复现工作目录>\docs\spec\D-backend-frontend-and-finetune.md` | FastAPI、Streamlit、多轮记忆、流式输出、微调概要与环境 |

---

## 二、复现前的实际状态

| 环节 | 状态 |
|---|---|
| 代码（9 模块 + demo/prompt 库） | ✅ 完整 |
| 爬虫语料 / 抽取 JSON | ✅ `__001__clawler\中药\*.txt`、`__002__extract_information\extract_{herb,formula}_data.json` |
| FAISS 索引与元数据 | ✅ `__003__create_neo4j_database\nero4j_embedding_faiss.index`(32MB)、`..._id2text.pkl`、`tcm_metadata.json` |
| bge 向量模型 | ✅ `<bge 模型目录>` |
| conda 环境 | ✅ `ctm_kg`（Python 3.10.20，依赖齐全） |
| Neo4j 服务 | ✅ 2026.03.1 运行中（7474/7687），`.env` 凭据可登录 |
| **Neo4j 图谱数据** | ❌ **空库（0 节点）—— 唯一缺口** |

---

## 三、本次执行的操作

### 1. 导入知识图谱（补齐缺口）
```powershell
$env:PYTHONPATH = '<项目根>'
Set-Location $env:PYTHONPATH
& 'D:\anaconda\envs\ctm_kg\python.exe' -X utf8 '__003__create_neo4j_database\__001__graph_importer.py'
```
结果：**节点 10,745 / 关系 25,835**（关系总数与 doc05 记载的 25,835 完全一致）

| 标签 | 数量 | 关系 | 数量 |
|---|---|---|---|
| Symptom | 2883 | TREATS_DISEASE | 8030 |
| Disease | 2852 | ALLEVIATES_SYMPTOM | 7042 |
| Herb | 2346 | HAS_INGREDIENT | 5634 |
| Formula | 965 | FROM_SOURCE | 2698 |
| Effect | 850 | HAS_EFFECT | 2200 |
| Source | 849 | HAS_SYMPTOM | 231 |

### 2. 修复 5 处跑不通的问题（最小侵入，只增不改原逻辑）

| 文件 | 问题 | 修法 |
|---|---|---|
| `common\path_utils.py` | 只有 `root_dir`，但节点导入 `root_path` | 增加别名 `root_path = root_dir` |
| `common\output_graph_utils.py`（新建） | 图模块导入 `common.output_graph_utils`，实际文件名为 `ouput_graph_utils.py`（少 t） | 新建垫片重导出 `output_pic_graph` |
| `__004__langgraph_more_nodes\nodes\match_entity_from_neo4j_node.py` | `faiss.read_index` 在中文路径下报 "No such file or directory"（faiss C++ 层用 ANSI fopen） | 改为 Python 读字节流 + `faiss.deserialize_index` |
| `__003__create_neo4j_database\__003__faiss_embedding.py` | `faiss.write_index` 同样受中文路径限制 | 改为 `faiss.serialize_index` + Python 写出 |
| `__005__fastapi\__001__langgraph_fastapi.py` | 调用 `zhongyi_response(input, user_id)`，但图为单参数版本 doc06 | 加适配层：`answer = await zhongyi_response(input)` → 推 `reply` 入队 |

### 3. 端到端验证（全部通过）

| 验证项 | 结果 |
|---|---|
| LangGraph 问答（CLI） | ✅ 「感冒咳嗽+桂枝汤」→ 抽实体→FAISS→4 条 Cypher→校验→查图→作答（并指出桂枝汤不含人参黄芪） |
| FastAPI `/process` 流式 | ✅ 200，1×`reply` + 1×`done`，JSON 分片 0 失败；酸枣仁汤问答正确 |
| FastAPI 静态资源 | ✅ `GET /picture/xxx.png` → 200 `image/png` 466KB |
| Streamlit 页面 | ✅ http://localhost:8501 → 200 |
| Streamlit 对话（AppTest 无头模拟） | ✅ 页面标题正确；输入「当归有什么功效？能治什么病？」→ 返回图谱支撑答复（补血和营/养血柔肝/养血活血；月经不调/经闭腹痛…） |

---

## 四、当前运行中的服务

| 服务 | 地址 | 启动命令（在项目根目录执行） |
|---|---|---|
| Neo4j | `bolt://localhost:7687` / http://localhost:7474 | 系统服务 `neo4j`（已自启） |
| FastAPI 后端 | http://127.0.0.1:8000 | `python __005__fastapi\__001__langgraph_fastapi.py` |
| Streamlit 前端 | http://localhost:8501 | `python -m streamlit run __006__streamlit\langgraph_streamlit.py` |

> 运行前需设置：`$env:PYTHONPATH = '<项目根>'`，并使用 `ctm_kg` 环境。

---

## 五、尚未纳入最小可用版的部分（按需再做）

1. ~~**多轮记忆 + 逐节点流式（doc10/doc11）**~~ → **已于 2026-09-11 补齐并验证通过，详见第八节**。
2. **小红书自动发布链路**：需要浏览器、人工首次登录（`cookie\xiaohongshu_cookie_state.json` 已存在）、且 `auto_publish_xiaohongshu_node.py` 里有阻塞式 `input()` 与 `headless=False`，不适合无人值守。极梦生图需 `JIMENG_AK/SK`（`.env` 已有）。
3. **模型微调（doc09）**：非最小链路必需；需 GPU ≥12GB + LLaMA-Factory，语料已备（`__007__fine_tune\zhongyi_zh_demo.json` 13.9MB）。
4. **GraphRAG / LightRAG（`__008__`/`__009__`）**：各自 `.env` 使用 siliconflow key，未运行。
5. **爬虫重跑**：语料已存在，无需重爬（目标站 `zhongyibaike.com`）。

---

## 六、安全提醒

1. `__000__demo\langgraph基础讲解\langgraph_demo展示.py` 等 demo 中**硬编码了真实 API Key**（`sk-****（已打码）`），若仍有效建议轮换。
2. 项目 `.env` 中 Neo4j 密码为弱口令；建议仅在本地监听（当前 7474/7687 为本机服务）。
3. `.env` 内含 DeepSeek Key、极梦 AK/SK，请勿将该项目目录提交到公开仓库。

---

## 七、辅助脚本（本次新增，可复用）

| 脚本 | 用途 |
|---|---|
| `<复现工作目录>\tools\neo4j_check.py` | 只读体检 Neo4j（节点/关系/标签分布/库状态） |
| `<复现工作目录>\tools\fastapi_client_test.py` | 模拟前端调用 `/process` 流式接口 + 静态资源探查 |
| `<复现工作目录>\tools\streamlit_apptest.py` | 用 Streamlit AppTest 无头模拟一次真实对话 |
| `<复现工作目录>\tools\multiturn_test.py` | 多轮记忆 + 跨 user_id 会话隔离验证 |
| `<复现工作目录>\tools\stream_test.py` | doc11 行式 JSON 流式链路验证（思考消息序列） |
| `<复现工作目录>\tools\streamlit_apptest_multiturn.py` | UI 级连续两问（省略句依赖历史）验证 |

---

## 八、doc10/doc11 补齐：多轮记忆 + 逐节点流式（2026-09-11 完成并验证）

### 8.1 改动清单

| 文件 | 改动 |
|---|---|
| `__004__langgraph_more_nodes\agent_state.py` | 新增 `input_semantic_trans: str`、`history_messages: List[dict]` |
| `__004__langgraph_more_nodes\langgraph_more_nodes.py` | ① `InMemorySaver` 编译图（按 `thread_id` 记忆）② 接入 `semantic_transcription_node` 作为入口（`START → 语义转写 → 小红书意图 → …`，**保留**原有小红书分支）③ `zhongyi_response(input, user_id)` 传 `{"configurable": {"thread_id": user_id}}` |
| `nodes\semantic_transcription_node.py` | 语义转写结果**同时回写 `state["input"]`**，让下游意图识别/实体抽取真正用上多轮上下文 |
| `nodes\` 下 9 个节点 | 改为 `async def (state, config)`；每个进度 print 后加同文本 `await put_msg_sentence_content(...)`；两个答案节点 + markdown 节点加 `await put_reply_content(...)` 与 `history_messages` 追加 |
| `__005__fastapi\__001__langgraph_fastapi.py` | 撤掉临时适配层，恢复 doc10/11 写法（`await zhongyi_response(input, user_id)` + `done`）；流式改为**每行一条 JSON**（`json.dumps(msg) + "\n"`） |
| `__006__streamlit\langgraph_streamlit.py` | 每会话独立 `user_id`（uuid4）+ 侧边栏「开启新对话」；前端按行缓冲解析 |

> 9 个节点由子智能体批量改造，改后已核对：签名带 `config`、进度 print 与推流一一对应、`py_compile` 全部通过。

### 8.2 验证证据

1. **多轮记忆（CLI）** `tools\multiturn_test.py`：
   - user A 问「当归有什么功效？」→ 答：补血活血／调经止痛／润肠通便
   - 同一 user A 追问省略句「**它**还能治什么病？」→ 语义转写补全为「当归还能治疗哪些疾病？」→ 列出当归关联疾病
   - 全新 user B 问同一省略句 → 正确回答“不知道‘它’指哪个，请补充药名”，**证明按 thread_id 隔离**
2. **流式（后端）** `tools\stream_test.py`：`/process` 依次返回多条 `msg`（逐节点思考）→ `reply`（完整答案）→ `done`；答案正确（酸枣仁汤＝虚烦不眠证，组成含酸枣仁/川芎/茯苓/知母/甘草）。
3. **UI 级多轮（AppTest 无头模拟真实前端）** `tools\streamlit_apptest_multiturn.py`：会话 ID `cabebf21-…`；两轮后 `messages` 共 4 条（user/assistant 各 2），第二轮 `think_content` 中可见「完成生成语义转写:当归还能治疗哪些疾病？」。

### 8.3 与文档的有意偏差（均为修 bug）

1. 语义转写节点**回写 `state["input"]`**——文档只写 `input_semantic_trans`，而下游节点都读 `state["input"]`，照抄则多轮不生效。
2. 流式协议改为**行分隔 JSON**——文档为裸 JSON 拼接，TCP 粘包时前端 `json.loads` 会崩。
3. 入口边保留小红书分支（`START → 语义转写 → 小红书意图 → …`）——doc10 抽取代码把该分支删掉了，本实现两分支并存以免丢功能。
4. 抽实体节点内 5 个调试 print（原始输出/dict/type/"++++"）**不推流**，避免污染前端思考区（控制台 print 保留）。

### 8.4 仍未做

- **小红书自动发布**：节点含阻塞式 `input()`、`headless=False`，需人工扫码登录，不适合无人值守。
- **doc11 的 `zhongyi_response_stream()`**：文档正文从未给出该函数定义（缺代码），当前以 msg_queue 推送实现等效流式。
- `history_num=5` 仅截断“送入提示词的条数”，状态内历史仍会增长（沿用文档原行为，未擅自更改）。

---

## 九、模型微调（doc09）——本机 QLoRA 实现与效果验证

### 9.1 关键约束与选型（全部实测，非估计）

- 本机 GPU：RTX 3060 Laptop **6GB**；文档要求 ≥12GB
- **显存探针**（4-bit QLoRA + 梯度检查点，1.5B）：seq 512 → 2.76GB；seq 1024 → 4.01GB；**seq 1536 → 驱动级 `device not ready`（超限）**
- **语料 token 分布**（1,959 条）：prompt 中位 698 / **response(JSON) 中位 995、p90 1676**；prompt+response ≤1024 的样本**仅 15%**
- ⇒ **1.5B 在 6GB 上可用 cutoff 上限约 1024，装不下本语料的目标 JSON**（硬训会截断 JSON 目标、教坏模型）
- ⇒ 改用文档同样列出的备选基座 **Qwen2.5-0.5B-Instruct**（常驻显存约 1.5B 的 1/4，可完整跑 cutoff 2048）

### 9.2 环境（全部落 D 盘，规避 C 盘仅 8.9GB 剩余）

| 项 | 值 |
|---|---|
| 环境 | `<虚拟环境目录>\tune312`（Python **3.12.7**）——新版 LLaMA-Factory 要求 Python ≥3.11，先用 3.10 建 venv 装包失败 |
| torch | **2.14.0+cu126**（配 torchvision 0.29.0 / torchaudio 2.11.0），CUDA 可用、算力 sm_86 |
| 框架 | LLaMA-Factory **0.9.6.dev0**（`<LLaMA-Factory 目录>`，commit `100e9a4`）+ bitsandbytes 0.50.2 |
| 镜像 | 华为云 PyPI **19.85 MB/s**（官方源实测 0.04 MB/s）；torch 走 pytorch 官方源 9.93 MB/s |
| 模型 | `<模型目录>\Qwen2.5-1.5B-Instruct`（2.89GB）、`<模型目录>\Qwen2.5-0.5B-Instruct`（953MB） |

### 9.3 数据与配置

- 数据集：`__007__fine_tune\llamafactory_data\{zhongyi_zh_demo.json, dataset_info.json}`（alpaca：instruction/input/output）
- **按 ≤2048 tokens 过滤** → `zhongyi_zh_2048.json`，**1,217 条**（丢弃 742 条长样本，保证目标不被截断）
- 训练配置：`__007__fine_tune\train_qlora_0.5b.yaml` —— LoRA r=8 / α=16 / dropout=0.05 / target=q_proj,v_proj、template=qwen、cutoff_len=2048、batch=1、梯度累积=8、lr=2e-4、cosine、3 epoch、bf16、梯度检查点（与 doc09 参数对齐）

### 9.4 训练结果

- **train_loss 0.0532**，3 epoch，耗时 **1:00:31**（459 步，7.4 秒/步）
- 产物：`<模型目录>\qwen2.5-0.5b-tcm-lora`（`adapter_model.safetensors` 2.07MB、checkpoint-200/400/459、`training_loss.png`）
- 峰值显存 5484/6144 MiB（89%），GPU 温度 87°C

### 9.5 效果验证（基座 vs LoRA 正确 A/B）

| 用例 | 参考答案 | 基座 0.5B | LoRA |
|---|---|---|---|
| 训练集样本（271 tok） | 12 实体 / 12 关系 | ❌ 非 JSON（markdown 列表、被截断） | ✅ **13 实体 / 13 关系** |
| 未训练长样本（588 tok） | 23 / 22 | ❌ 非 JSON | ✅ **23 / 22（与参考完全一致）** |
| 爬虫原始文本·丁香（1397 tok，未见） | — | ❌ 非 JSON | ✅ 8 实体 / 7 关系（合法 schema） |

**结论**：基座 0.5B **0/3** 能按要求输出 JSON；LoRA **3/3** 输出合法 JSON，且未训练样本上的实体/关系规模与参考答案一致 → 微调达成 doc09 的目标（把"抽取"从调用大模型变成小模型直出）。

> ⚠️ **方法学坑（复现必读）**：`PeftModel.from_pretrained(base, ...)` 会**原地替换** base 的 Linear 层，直接比较 `base` 与 `peft_model` 得到的是"LoRA vs LoRA"（第一版两边输出逐字相同，正是此坑）。正确做法：同一模型上 `with model.disable_adapter():` 取基座输出。脚本见 `<复现工作目录>\tools\compare_base_vs_lora2.py`。

### 9.6 局限与后续

- 用例 3（1397 tok 长原文）LoRA 虽输出合法 JSON，但实体类型分布偏离（Herb 2 / Symptom 4 / Disease 2），0.5B 容量与长文本抽取精度有限
- train_loss 0.053 偏低，存在过拟合风险；严谨评估应划分留出集并计算实体级 F1
- 想要 1.5B/7B 效果需 ≥12GB 显存（云端 Linux GPU）；本机 WSL 共享同一张卡，无解
- vLLM 部署只能走 WSL2 或云端（Windows 原生不支持 vLLM）
