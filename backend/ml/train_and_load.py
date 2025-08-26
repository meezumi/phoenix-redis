import numpy as np
from sklearn.ensemble import IsolationForest
import skl2onnx
from skl2onnx.common.data_types import FloatTensorType
import redis
import os

# --- 1. Generate Sample Data and Train Model ---
np.random.seed(42)
# Normal transactions
normal_data = np.random.rand(1000, 3)
normal_data[:, 0] = normal_data[:, 0] * 150
normal_data[:, 1] = normal_data[:, 1] * 24
normal_data[:, 2] = normal_data[:, 2] * 7

# Fraudulent transactions (anomalies)
fraud_data = np.random.rand(50, 3)
fraud_data[:, 0] = fraud_data[:, 0] * 2000 + 1000
fraud_data[:, 1] = (fraud_data[:, 1] * 6 + 1) % 24
fraud_data[:, 2] = np.random.randint(0, 7, 50)

X_train = np.vstack([normal_data, fraud_data])

model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X_train)
print("Model trained.")

# --- 2. Convert the Model to ONNX format ---
initial_type = [("float_input", FloatTensorType([None, 3]))]

target_opset = {"": 13, "ai.onnx.ml": 3}

onnx_model = skl2onnx.convert_sklearn(
    model, initial_types=initial_type, target_opset=target_opset
)

# Save the ONNX model to a file
model_path = "fraud_model.onnx"
with open(model_path, "wb") as f:
    f.write(onnx_model.SerializeToString())
print(f"Model converted to ONNX and saved as {model_path}")

# --- 3. Load the ONNX Model into RedisAI --- (this part still giving errors)
redis_host = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=redis_host, port=6379)
ai = r.ai()

with open(model_path, "rb") as f:
    model_blob = f.read()

ai.modelset(
    "fraud_model",
    "ONNX",
    "CPU",
    model_blob,
    inputs=["float_input"],
    outputs=["label", "score"],
)
print("Model loaded into RedisAI under the key 'fraud_model'.")
