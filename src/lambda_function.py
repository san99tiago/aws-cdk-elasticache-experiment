# Built-in imports
from datetime import datetime


def lambda_handler(event, context):
    # print("lambda_handler: <event> is {}".format(event))

    current_utc_time = datetime.now().strftime("%Y_%m_%d-%H_%M_%SZ")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {
            "datetime": current_utc_time,
            "message": "Hello from Santi",
        },
    }
