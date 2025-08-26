import redis
import json
import datetime


# This class is used by the `arq` CLI to configure the worker.
# It should be at the top or bottom of the file.
class AppSettings:
    redis_settings = redis.asyncio.RedisSettings(host="redis")
    functions = ["run_fraud_checks"]


async def run_fraud_checks(ctx, transaction_data: dict):
    """
    This function processes transactions, checks for fraud using rules and graphs,
    and publishes alerts to Redis Pub/Sub.
    """
    redis_conn: redis.asyncio.Redis = ctx["redis"]
    graph = redis_conn.graph("fraud_graph")

    print(f"Processing transaction: {transaction_data}")

    user_id = transaction_data["user_id"]
    card_id = transaction_data["card_id"]
    device_id = transaction_data["device_id"]

    # --- STAGE 1: MODEL THE TRANSACTION IN THE GRAPH ---
    await graph.query(f"MERGE (u:User {{id: '{user_id}'}})")
    await graph.query(f"MERGE (c:Card {{id: '{card_id}'}})")
    await graph.query(f"MERGE (d:Device {{id: '{device_id}'}})")
    await graph.query(
        f"""
        MATCH (u:User {{id: '{user_id}'}}), (c:Card {{id: '{card_id}'}})
        MERGE (u)-[:USED_CARD]->(c)
    """
    )
    await graph.query(
        f"""
        MATCH (u:User {{id: '{user_id}'}}), (d:Device {{id: '{device_id}'}})
        MERGE (u)-[:USED_DEVICE]->(d)
    """
    )

    is_fraud = False
    fraud_reason = ""

    # --- STAGE 2: QUERY FOR FRAUD RINGS (GRAPH-BASED) ---
    query = """
        MATCH (u1:User)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(u2:User)
        WHERE u1.id <> u2.id AND d.id = $device_id
        RETURN u1.id AS user1, u2.id AS user2, d.id AS shared_device
    """
    result = await graph.query(query, {"device_id": device_id})

    if not result.is_empty():
        is_fraud = True
        first_match = result.result_set[0]
        user1, user2, shared_device = first_match[0], first_match[1], first_match[2]
        fraud_reason = f"Fraud Ring Detected: Users {user1} and {user2} shared device {shared_device}"
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
