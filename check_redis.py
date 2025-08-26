import redis
import os

print("--- Redis Library Check ---")
print(f"Version: {redis.__version__}")
print(f"File Path: {redis.__file__}")
print("--- End Check ---")

try:
    r = redis.Redis()
    r.ai()
    print("'.ai()' method found successfully.")
except AttributeError as e:
    print(f"Error as expected: {e}")
