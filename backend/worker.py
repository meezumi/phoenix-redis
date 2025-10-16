import redis.asyncio
import json
import datetime
from arq.connections import RedisSettings


async def run_fraud_checks(ctx, transaction_data: dict):
    """
    This function processes transactions, checks for fraud using rules and graphs,
    and publishes alerts to Redis Pub/Sub.
    """
    redis_conn: redis.asyncio.Redis = ctx["redis"]

    print(f"Processing transaction: {transaction_data}")

    user_id = transaction_data["user_id"]
    card_id = transaction_data["card_id"]
    device_id = transaction_data["device_id"]

    # --- STAGE 1: STORE TRANSACTION DATA IN REDIS ---
    # Store device usage for fraud ring detection
    device_users_key = f"device:{device_id}:users"
    await redis_conn.sadd(device_users_key, user_id)
    await redis_conn.expire(device_users_key, 3600)  # Keep for 1 hour

    is_fraud = False
    fraud_reason = ""

    # --- STAGE 2: CHECK FOR FRAUD RINGS (DEVICE SHARING) ---
    # Get all users who have used this device
    users_on_device = await redis_conn.smembers(device_users_key)
    users_on_device = [u.decode('utf-8') if isinstance(u, bytes) else u for u in users_on_device]
    
    if len(users_on_device) > 1:
        is_fraud = True
        fraud_reason = f"Fraud Ring Detected: {len(users_on_device)} different users ({', '.join(users_on_device)}) shared device {device_id}"
        print(f"ALERT: {fraud_reason}")

    # --- STAGE 3: CHECK TRANSACTION VELOCITY (RULE-BASED) ---
    # We only run this check if no fraud has been detected yet.
    if not is_fraud:
        key = f"user:{user_id}:tx_count"
        # Use a pipeline for atomic operations
        pipe = redis_conn.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        results = await pipe.execute()
        tx_count = results[0]

        if tx_count > 10:  # Rule: More than 10 transactions in 60 seconds
            is_fraud = True
            fraud_reason = "High Transaction Velocity"
            print(f"ALERT: {fraud_reason} for user {user_id}")

    # --- STAGE 4: PUBLISH ALERT ---
    if is_fraud:
        alert_message = {
            "type": "FRAUD_ALERT",
            "reason": fraud_reason,
            "transaction": transaction_data,
        }
        await redis_conn.publish("fraud_alerts", json.dumps(alert_message))

    return f"Transaction for {user_id} processed. Fraud: {is_fraud}"


# This class is used by the `arq` CLI to configure the worker.
# It should be at the top or bottom of the file.
class AppSettings:
    redis_settings = RedisSettings(host="redis")
    functions = [run_fraud_checks]
