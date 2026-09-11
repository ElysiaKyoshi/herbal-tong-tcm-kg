import httpx
import time
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# ============ vLLM 服务配置 ============
# vLLM 启动时通过 --lora-modules 参数加载多个 LoRA 适配器
# 示例: vllm serve qwen/qwen2.5-1.5b-instruct \
#   --enable-lora --lora-modules \
#   lora_nlp=/path/to/lora_nlp \
#   lora_code=/path/to/lora_code \
#   lora_math=/path/to/lora_math

# vLLM 服务地址
VLLM_BASE_URL = "https://d527e2f089a644d9bfb9ac19577b6c46--8000.ap-shanghai2.cloudstudio.club/v1"
VLLM_API_KEY = "EMPTY"

# 基座模型名称（不使用 LoRA）
BASE_MODEL = "qwen/qwen2.5-1.5b-instruct"

# 已注册的 LoRA 模块列表（名称与 vLLM 启动时的 --lora-modules 对应）
LORA_MODULES = {
    "cot": "cot",       # NLP 对话风格 LoRA
}


def createLlm(loraName=None, temperature=0.6, maxTokens=2000, streaming=True):
    """
    创建 ChatOpenAI 实例，指定使用的 LoRA 模块

    参数:
        loraName: LoRA 模块名称（在 LORA_MODULES 中定义）
                  None 表示使用基座模型，不加载 LoRA
        temperature: 生成温度
        maxTokens: 最大生成 token 数
        streaming: 是否流式输出
    返回:
        ChatOpenAI 实例
    """
    if loraName is not None:
        if loraName not in LORA_MODULES:
            raise ValueError(
                f"LoRA 模块 '{loraName}' 未注册，可用模块: {list(LORA_MODULES.keys())}"
            )
        modelName = LORA_MODULES[loraName]
        print(f"[LoRA] 使用模块: {loraName} -> model={modelName}")
    else:
        modelName = BASE_MODEL
        print(f"[Base] 使用基座模型: {modelName}")

    return ChatOpenAI(
        api_key=VLLM_API_KEY,
        base_url=VLLM_BASE_URL,
        model=modelName,
        temperature=temperature,
        max_tokens=maxTokens,
        streaming=streaming,
    )


def callLlm(llm, systemContent, userContent):
    """
    调用指定的 LLM 实例，流式输出并返回完整结果

    参数:
        llm: ChatOpenAI 实例
        systemContent: 系统提示词
        userContent: 用户输入
    返回:
        完整响应文本
    """
    messages = [
        SystemMessage(content=systemContent),
        HumanMessage(content=userContent),
    ]

    result = ""
    for chunk in llm.stream(messages):
        result += chunk.content
        print(chunk.content, end="", flush=True)
    print()  # 换行
    return result


if __name__ == '__main__':
    # 测试问题
    testQuestion = "对于「初三女生在搀扶跌倒老奶奶后反被冤枉，但仍选择资助她千元」的新闻事件，你有什么看法？"
    systemPrompt = "你是一位有见地的评论员，请用简洁有力的语言表达观点。"

    # ========== 1. 调用指定 LoRA 模块 ==========
    print("=" * 100)
    print("【1】调用指定 LoRA 模块: cot")
    print("=" * 100)
    loraLlm = createLlm(loraName="cot", temperature=0.6, maxTokens=2000)
    a = time.time()
    result1 = callLlm(loraLlm, systemPrompt, testQuestion)
    b = time.time()
    print(f"\n输出长度：{len(result1)}字  耗时：{b - a:.1f}秒  速度：{len(result1) / (b - a):.1f}字/秒")
    print("*" * 100)
    print(result1)
