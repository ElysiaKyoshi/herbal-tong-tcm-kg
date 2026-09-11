import asyncio
import json

from fastapi import FastAPI, Request
from starlette.responses import StreamingResponse
from starlette.staticfiles import StaticFiles

from __004__langgraph_more_nodes.langgraph_more_nodes import zhongyi_response
from __005__fastapi.__003__msg_queue import put_done_content, msg_queue_manager, remove_msg_queue
from common.path_utils import get_file_path

app = FastAPI()
app.mount("/picture", StaticFiles(directory=get_file_path("picture")))


async def my_zhongyi_project(input, user_id):
    # doc10/doc11 版本：user_id 同时作为 LangGraph 的 thread_id（多轮记忆），
    # 各节点在运行过程中通过 msg_queue 推送思考过程，最终答案以 reply 推送。
    await zhongyi_response(input, user_id)
    await put_done_content(user_id)


async def generate_data(input, user_id):
    # 异步执行任务
    asyncio.create_task(my_zhongyi_project(input, user_id))

    while True:
        msg = await msg_queue_manager.get_msg_queue(user_id).get()
        print(msg)
        # 每条消息一行 JSON（前端按行解析，避免 TCP 粘包导致解析失败）
        yield json.dumps(msg) + "\n"
        if msg.get("type") == "done":
            # 删除队列
            remove_msg_queue(user_id)
            break


@app.post("/process")
async def process_data(request: Request):
    # 直接获取请求体中的 JSON 数据
    # 拿到的是dict的数据
    input_data = await request.json()
    # 获取input
    input = input_data.get("input", "")
    user_id = input_data.get("user_id", "")
    # 进行处理

    return StreamingResponse(generate_data(input, user_id), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
