# Built-in imports
import os
import random
from datetime import datetime

# External imports
import redis


REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

redis_connector = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def lambda_handler(event, context):
    token = "Not found"

    if event.get("action") == "write":
        print("action: write")
        current_utc_time = datetime.now().strftime("%Y_%m_%d-%H_%M_%SZ")
        token_int = random.randint(1, 99)
        token = f"{token_int}-santi-{current_utc_time}"
        response = redis_connector.set("token", token)
        print(response)

    if event.get("action") == "read":
        print("action: read")
        token = redis_connector.get("token")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {
            "token": token,
            "message": "Hello from Santi",
        },
    }
