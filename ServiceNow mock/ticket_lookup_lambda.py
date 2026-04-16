import json
import boto3

dynamo=boto3.resource('dynamodb')
table=dynamo.Table('ticket')

def lambda_handler(event, context):
    # TODO implement
    body=table.get_item(
        Key={
            'ticket_id':event.get('ticket_id')
        }
    )



    return {
        'statusCode': 200,
        'body': json.dumps(body)
    }
