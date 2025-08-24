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

