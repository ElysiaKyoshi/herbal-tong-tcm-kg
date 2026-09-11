from autogen import AssistantAgent

assistant = AssistantAgent(
    name="Assistant",
    llm_config={"model": "deepseek-chat", "api_key": "YOUR_API_KEY_HERE",
                "base_url": "https://api.deepseek.com"}
)

reply = assistant.generate_reply("请给我写一个快速排序的Python代码")
assistant.generate_reply([{"u"}])
print(reply)
