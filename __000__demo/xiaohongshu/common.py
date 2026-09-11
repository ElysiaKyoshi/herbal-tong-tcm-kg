from langchain_openai import ChatOpenAI

# ============ 配置llm区域 ============
my_llm = ChatOpenAI(
    api_key="YOUR_API_KEY_HERE",  # ← 替换为你自己的 API Key
    base_url="https://api.deepseek.com",
    model="deepseek-chat"
)

JIMENG_AK = "YOUR_JIMENG_AK_HERE"
JIMENG_SK = "YOUR_JIMENG_SK_HERE"