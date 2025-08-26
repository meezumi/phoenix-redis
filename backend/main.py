from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pantic import BaseModel
import asyncio
import redis.asyncio as aioredis
import json
from arq import create_pool
from arq.connections import RedisSettings

app = FastAPI()


class Transaction(BaseModel):
    user_id: str
    card_id: str
    device_id: str
    amount: float
    merchant: str


@app.post("/transaction")
async def process_transaction(transaction: Transaction):
    redis_pool = await create_pool(RedisSettings(host="redis"))
    await redis_pool.enqueue_job("run_fraud_checks", transaction.model_dump())
    return {"status": "Transaction accepted for processing"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Use redis.asyncio for non-blocking Pub/Sub
    r = aioredis.from_url("redis://redis")
    pubsub = r.pubsub()

    try:
        await pubsub.subscribe("fraud_alerts")
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                await websocket.send_text(message["data"].decode("utf-8"))
            await asyncio.sleep(0.01)  # Yield control
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await pubsub.close()
