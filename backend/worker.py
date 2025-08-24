import redis
import json
from redis.commands.graph import Graph
import datetime

# The function that will be executed by the worker.
# The `ctx` argument is a dictionary provided by `arq`.
async def run_fraud_checks(ctx, transaction_data: dict):
    redis_conn: redis.Redis = ctx["redis"]  # `arq` provides a redis connection.
    graph = redis_conn.graph("fraud_graph")  # Connect to a graph named 'fraud_graph'
    ai = redis_conn.ai()

    print(f"Processing transaction: {transaction_data}")

    user_id = transaction_data["user_id"]
    card_id = transaction_data["card_id"]
    device_id = transaction_data["device_id"]

    # --- STAGE 1: MODEL THE TRANSACTION IN THE GRAPH ---
    # We use MERGE to create nodes if they don't exist, or match them if they do.
    # This is an idempotent operation.

    # Create nodes
    graph.query(f"MERGE (u:User {{id: '{user_id}'}})")
    graph.query(f"MERGE (c:Card {{id: '{card_id}'}})")
    graph.query(f"MERGE (d:Device {{id: '{device_id}'}})")

    # Create relationships between them
    graph.query(
        f"""
        MATCH (u:User {{id: '{user_id}'}}), (c:Card {{id: '{card_id}'}})
        MERGE (u)-[:USED_CARD]->(c)
    """
    )
    graph.query(
        f"""
        MATCH (u:User {{id: '{user_id}'}}), (d:Device {{id: '{device_id}'}})
        MERGE (u)-[:USED_DEVICE]->(d)
    """
    )
    graph.query(
        f"""
        MATCH (c:Card {{id: '{card_id}'}}), (d:Device {{id: '{device_id}'}})
        MERGE (c)-[:ASSOCIATED_WITH]->(d)
    """
    )

    # --- STAGE 2: QUERY FOR FRAUD RINGS ---
    # This query looks for a pattern where one device has been used by more than one user.
    query = """
        MATCH (u1:User)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(u2:User)
        WHERE u1.id <> u2.id
        RETURN u1.id AS user1, u2.id AS user2, d.id AS shared_device
    """
    result = graph.query(query)

    is_fraud = False
    fraud_reason = ""

    if not result.is_empty():
        is_fraud = True
        # Let's grab the details from the first match for our alert
        first_match = result.result_set[0]
        user1, user2, shared_device = first_match[0], first_match[1], first_match[2]
        fraud_reason = f"Fraud Ring Detected: Users {user1} and {user2} shared device {shared_device}"
        print(f"ALERT: {fraud_reason}")

    # --- STAGE 3: ML-BASED INFERENCE WITH RedisAI ---
    # Prepare the feature tensor for the model.
    # It must be in the same order as the training data: [amount, hour_of_day, day_of_week]
    now = datetime.datetime.now()
    features = np.array(
        [transaction_data["amount"], now.hour, now.weekday()], dtype=np.float32
    )

    # Set the input tensor in RedisAI
    ai.tensorset("tx_features", features)

    # Run the model
    ai.modelrun("fraud_model", inputs=["tx_features"], outputs=["tx_label", "tx_score"])

    # Get the result
    label, score = ai.tensorget("tx_label")[0], ai.tensorget("tx_score")[0]

    # IsolationForest returns -1 for anomalies (fraud) and 1 for inliers (normal).
    if label == -1:
        # Check if we haven't already flagged this as fraud from the graph query
        if not is_fraud:
            is_fraud = True
            fraud_reason = f"High ML Anomaly Score: {score:.4f}"
            print(f"ALERT: {fraud_reason}")

    # --- STAGE 4: RULE-BASED CHECKS (as before) ---
    key = f"user:{user_id}:tx_count"
    tx_count = await redis_conn.incr(key)
    if tx_count == 1:
        await redis_conn.expire(key, 60)

    if not is_fraud and tx_count > 10:
        is_fraud = True
        fraud_reason = "High Transaction Velocity"
        print(f"ALERT: High transaction velocity for user {user_id}")

    # --- STAGE 5: PUBLISH ALERT ---
    if is_fraud:
        alert_message = {
            "type": "FRAUD_ALERT",
            "reason": fraud_reason,
            "transaction": transaction_data,
        }
        await redis_conn.publish("fraud_alerts", json.dumps(alert_message))

    return f"Transaction for {user_id} processed. Fraud: {is_fraud}"


# This class is used by the `arq` CLI to configure the worker.
class AppSettings:
    redis_settings = RedisSettings(host="redis")
    functions = [run_fraud_checks]
