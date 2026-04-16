import json
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ticket')


def lambda_handler(event, context):
    ticket = {
        "ticket_id": f"INC{(uuid.uuid4().hex[:6])}".upper(),
        "priority": event.get("priority", "Low"),
        "category":event.get("category", "NOT DEFINED"),
        "description": event.get("description", "NOT DEFINED"),
        "requestor": event.get("requestor", "unknown"),
        "status": "Open",
        "assignment_group": event.get("assignment_group","NOT DEFINED"),
        "created_at": datetime.utcnow().isoformat()
    }

    table.put_item(Item=ticket)

    return {
        "statusCode": 200,
        "body": json.dumps(ticket)
    }
