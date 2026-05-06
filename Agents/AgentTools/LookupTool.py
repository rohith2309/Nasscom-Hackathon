import boto3
import json
from langchain_core.tools import tool
from langchain_aws import ChatBedrockConverse
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import os

load_dotenv()

session = boto3.Session()
lambda_client = boto3.client('lambda', region_name='us-east-1', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))

@tool
def lookup_ticket(ticket_id: str):
    '''A tool to lookup a ticket in the ticketing system. It takes the ticket id as input and returns the details of the ticket.'''
    
    payload={
        "ticket_id": ticket_id
    }
    
    lambda_response = lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-east-1:022880635234:function:Lookup_ticket',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    response_payload = lambda_response['Payload'].read().decode('utf-8')
    
    res = json.loads(response_payload)
    

    return res.get('body', 'No data found')