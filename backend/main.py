from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
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
    # This creates a connection pool to Redis for `arq`.
    redis_pool = await create_pool(RedisSettings(host="redis"))

    # "run_fraud_checks" is the name of the function the worker will execute.
    # transaction.model_dump() passes the transaction data to the function.
    await redis_pool.enqueue_job("run_fraud_checks", transaction.model_dump())

    return {"status": "Transaction accepted for processing"}


# We'll define the WebSocket endpoint later for the dashboard.
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Logic to subscribe to Redis Pub/Sub and forward messages
    # will go here in a later step.
    while True:
        await asyncio.sleep(1)  # Keep connection alive
