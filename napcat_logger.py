import logging

import uvicorn
from fastapi import FastAPI, Request


# 配置控制台日志输出
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("napcat")

app = FastAPI(title="NapCat Debug Receiver")


@app.post("/")
async def receive_napcat_event(request: Request):
    """
    接收 NapCat (OneBot) 上报的事件，并直接打到日志里。

    使用方式（在 NapCat 中）：
    - 将 OneBot HTTP 客户端的上报地址配置为，例如：
      http://127.0.0.1:8081/
    - 启用该 HTTP 客户端后，NapCat 收到消息/事件就会 POST 到这里。
    """
    try:
        data = await request.json()
    except Exception as e:
        body = await request.body()
        logger.error(f"NapCat 上报内容不是合法 JSON: {e}, body={body!r}")
        return {"status": "error", "reason": "invalid json"}

    logger.info(f"收到 NapCat 事件: {data}")
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    # 注意：NapCat 自身的 WebUI 默认运行在 6099 端口，
    # 这里我们单独启一个 8081 端口来接收 NapCat 的 HTTP 客户端上报。
    #
    # 在 NapCat 的 onebot11.json 里，将 httpClients.url 设置为：
    #   http://127.0.0.1:8081/
    # 并 enable=true，就可以看到这里的日志了。
    uvicorn.run(app, host="0.0.0.0", port=8081)

