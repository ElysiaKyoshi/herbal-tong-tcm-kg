from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post("/process")
async def process(request: Request):
    # 获取传入的 JSON 数据
    data = await request.json()
    print(type(data))
    print(data)

    # 你可以在这里随意处理，比如加点东西
    result = {
        "status": "ok",
        "echo": "aaa",  # 原样返回
        "extra": {"info": "这是返回时附加的数据"}
    }

    return JSONResponse(content=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
