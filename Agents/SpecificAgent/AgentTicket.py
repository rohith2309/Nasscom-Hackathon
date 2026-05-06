from utils.utility import create_agent
from langchain_aws import ChatBedrockConverse
from Agents.AgentTools.CreateTool import create_ticket
from Agents.AgentTools.LookupTool import lookup_ticket 
from langchain_core.messages import HumanMessage
import os
from typing import Literal
from langgraph.types import Command
from utils.utility import AgentState


Novalite_model=ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    temperature=0, 
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )

TicketAgentPrompt="""
You are a helpful assistant agent responsible for creating and looking up tickets in the ticketing system. You have access to two tools, CreateTool and LookupTool. CreateTool is used to create a ticket in the ticketing system and LookupTool is used to lookup a ticket in the ticketing system. Always use CreateTool to create a ticket when required and use LookupTool to lookup a ticket when required.


NOTE: You Should not ask the user for priority or category; 
    use the values provided in the conversation context
    pick one category from the following list based on the user's query and the conversation context 
    [
        'Infrastructure', 
        'Application', 
        'Security', 
        'Database', 
        'Network', 
        'Access Management'
    ]
"""

AgentTicket=create_agent(TicketAgentPrompt,Novalite_model,[create_ticket,lookup_ticket])

def TicketAgentNode(state:AgentState)->Command[Literal["SupervisorAgent"]]:
    query = state["messages"]
    result = AgentTicket.invoke({"messages": query})
    return Command(
        goto='SupervisorAgent',
        update={"messages": result["messages"]}
    )