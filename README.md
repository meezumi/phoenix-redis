# Project Deets # 
Detecting fraud in a hidden backend process, but also providing human analysts with a live, intuitive dashboard to visualize transaction flows, identify emerging threats, and investigate suspicious patterns. The project is gonna highlight this and will also push these events to a dynamic web interface, allowing for immediate insight and action. Also incorporating a machine learning model directly into Redis and using graph database capabilities to uncover sophisticated fraud rings.

# The Planned Architecture #
```
                                      +--------------------------+
                                      |   Next.js Frontend       |
                                      | (Dashboard, Visuals)     |
                                      +-------------+------------+
                                                    ^
                                                    | (WebSocket for Live Updates)
                                                    |
+-------------------+      +--------------------+   |   +--------------------------+
| Transaction       |----->|   FastAPI Backend  |---+-->|   Redis Pub/Sub          |
| Simulator (Script)|      | (API Endpoints)    |   |   | (fraud_alerts channel)   |
+-------------------+      +--------------------+   |   +--------------------------+
                                      |             |
           (Enqueues Task via `arq`)  |             | (Publishes alert)
                                      v             ^
+---------------------------------------------------+------------------------------------+
|                                 Redis Stack                                            |
|                                                                                        |
|  +---------------+      +----------------+      +---------------+      +------------+  |
|  | `arq` Queue   |----->|   `arq` Worker |----->|  RedisGraph   |----->| RedisAI    |  |
|  | (Job List)    |      | (Fraud Logic)  |      |(Relationships)|      | (ML Model) |  |
|  +---------------+      +----------------+      +---------------+      +------------+  |
|                                                                                        |
+----------------------------------------------------------------------------------------+
```

# Sample Testing Scenario Snippets #

## High Velocity Fraud ##
```
curl -X POST -H "Content-Type: application/json" -d '{
  "user_id": "user-high-velocity",
  "card_id": "card-hv",
  "device_id": "device-hv",
  "amount": 10.00,
  "merchant": "Gas Station"
}' http://localhost:8000/transaction

```
## Fraud Ring ##
```
# First, a transaction from a new user on a specific device
curl -X POST -H "Content-Type: application/json" -d '{
  "user_id": "user-ring-1",
  "card_id": "card-ring-1",
  "device_id": "device-shared-123",
  "amount": 150.00,
  "merchant": "Online Store"
}' http://localhost:8000/transaction

# Second, a transaction from a DIFFERENT user on the SAME device
curl -X POST -H "Content-Type: application/json" -d '{
  "user_id": "user-ring-2",
  "card_id": "card-ring-2",
  "device_id": "device-shared-123",
  "amount": 25.50,
  "merchant": "Coffee Shop"
}' http://localhost:8000/transaction

```
