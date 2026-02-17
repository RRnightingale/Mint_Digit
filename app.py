from fastapi import FastAPI, Request
import uvicorn

from napcat_adapter import from_napcat_payload
from strategies_basic import get_policy
from logger import get_logger
from visualization import router as visualization_router


logger = get_logger("app")
app = FastAPI(title="NapCat Simple Debug Receiver")

# 注册可视化路由器
app.include_router(visualization_router)


@app.post("/")
async def receive_napcat_event(request: Request):
    """NapCat HTTP 客户端上报入口：接受输入，调用策略，完毕。"""
    payload = await request.json()

    event = from_napcat_payload(payload)
    if event is None:
        logger.info("收到非 message 事件: %s", payload)
        return {"status": "ignored"}

    logger.info("收到 NapCat 事件: event=%s", event)

    policy = get_policy()
    result = policy.handle(event)

    logger.info("事件处理结果: result=%s", result)

    return result


@app.get("/ping")
async def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
