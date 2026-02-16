import uvicorn
from fastapi import FastAPI, Request
import mint_utils
import logging

# 配置日志
# logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()  # 拿到root logger
logger.setLevel(logging.DEBUG)

app = FastAPI()

@app.post("/")
async def root(request: Request):
    data = await request.json()  # 获取事件数据
    mint_utils.handle(data)
    return {}

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
