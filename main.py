import uvicorn
from fastapi import FastAPI, Request
import llob_utils
import gpt_utils
import mint_utils
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
AT_MINT = "[CQ:at,qq=3995633031,name=阿敏Digit]"

app = FastAPI()

@app.post("/")
async def root(request: Request):
    data = await request.json()  # 获取事件数据
    logging.debug(f"接收到的数据: {data}")
    
    user_id = data.get('user_id')  # 读取user id
    user_name = data.get('sender', {}).get('nickname')  # 读取 nick name
    raw_message = data.get('raw_message')  # 获取原始消息
    message_type = data.get('message_type')  # 获取消息类型
    group_id = data.get('group_id')  # 获取群ID（如果有）
    
    if not user_id:
        logging.error("缺少 user_id")
        return {"error": "缺少 user_id"}
    
    if not raw_message:
        logging.error("缺少 raw_message")
        return {"error": "缺少 raw_message"}
    
    logging.debug(f"user_id = {user_id}, raw_message = {raw_message}, message_type = {message_type}")

    
    if message_type == 'private':
        reply_text = mint_utils.reply(raw_message)  # 调用reply
        logging.debug(f"生成的回复: {reply_text}")
        response = llob_utils.send_private_message(user_id, reply_text)  # 向user发送私信
        logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")
    elif message_type == 'group' and group_id:
        reply_text = mint_utils.replay_group(user_name, raw_message[len(AT_MINT):])  # 调用reply,记录信息
        if raw_message.startswith(AT_MINT):
            response = llob_utils.send_group_message_with_at(group_id, reply_text, user_id )  # 向群发送消息
            logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")  
    else:
        logging.error("未知的消息类型或缺少群ID")
        return {"error": "未知的消息类型或缺少群ID"}
    
    return {}

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
