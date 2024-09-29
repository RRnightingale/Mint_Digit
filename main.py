import uvicorn
from fastapi import FastAPI, Request
import llob_utils
import gpt_utils
import mint_utils
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

@app.post("/")
async def root(request: Request):
    data = await request.json()  # 获取事件数据
    logging.debug(f"接收到的数据: {data}")
    
    user_id = data.get('user_id')  # 读取user id
    raw_message = data.get('raw_message')  # 获取原始消息
    if user_id and raw_message:
        logging.debug(f"user_id = {user_id}, raw_message = {raw_message}")
        reply_text = mint_utils.reply(raw_message)  # 调用reply
        logging.debug(f"生成的回复: {reply_text}")
        response = llob_utils.send_private_message(user_id, reply_text)  # 向user发送回复
        logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")
    
    return {}

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
