from fastapi import FastAPI, Request
import uvicorn

from napcat_adapter import from_napcat_payload
from dispatcher import dispatch_event
import napcat_client


app = FastAPI(title="NapCat Simple Debug Receiver")


@app.post("/")
async def receive_napcat_event(request: Request):
    """NapCat HTTP 客户端上报入口."""
    payload = await request.json()

    event = from_napcat_payload(payload)
    if event is None:
        # 暂时忽略非 message 事件
        print("收到非 message 事件:", payload)
        return {"status": "ignored"}

    reply = dispatch_event(event)

    print("\n=== 收到 NapCat 事件 ===")
    print("event:", event)
    print("reply:", reply)
    print("=== 事件结束 ===\n")

    if not reply.text:
        return {"status": "no_reply"}

    # 根据事件类型，通过 NapCat 真正发消息回 QQ
    resp = None
    if event.is_private:
        resp = napcat_client.send_private_message(event.user_id, reply.text)
    elif event.is_group:
        resp = napcat_client.send_group_message(event.group_id, reply.text)

    return {
        "status": "sent",
        "reply": reply.text,
        "napcat_status": getattr(resp, "status_code", None) if resp is not None else None,
    }


@app.get("/ping")
async def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    # 这里我们启一个 8081 端口来接收 NapCat 的 HTTP 客户端上报。
    # 在 NapCat 的 onebot11.json 里，将 httpClients.url 设置为：
    #   http://127.0.0.1:8081/
    # 并 enable=true，就可以看到这里的行为。
    uvicorn.run(app, host="0.0.0.0", port=8081)

