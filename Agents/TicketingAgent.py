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
def create_ticket(title: str, description: str, priority: str, category: str,assignement_group:str):
    
    '''A tool to create a ticket in the ticketing system. It takes the title, description, priority, category and assignment group of the ticket as input and creates a ticket in the system.
    
    Creates a ticket in the system. 
    NOTE: You do not need to ask the user for priority or category; 
    use the values provided in the conversation context.
    '''
    
    payload={
        "title": title,
        "description": description,
        "priority": priority,
        "category": category,
        "assignment_group": assignement_group
    }
    
    lambda_response = lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-east-1:022880635234:function:Create_ticket',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    res=json.loads(lambda_response['Payload'].read())
    
    body=json.loads(res.get('body', '{}'))
    ticket_id=body.get('ticket_id')

    return f"Ticket created successfully with ID: {ticket_id}" if ticket_id else "Failed to create ticket"

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