from utils.utility import create_agent
from langchain_aws import ChatBedrockConverse
from Agents.AgentTools.RAGTool import RAG_check_node
from langchain_core.messages import HumanMessage
import os
from utils.Routers import RouteDecision
from typing import Literal
from langgraph.graph import END
from langgraph.types import Command
from utils.utility import AgentState

Novalite_model=ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    temperature=0, 
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )

GROUPS_LIST = ["DB_ADMIN", "NETWORK_TEAM", "CLOUD_OPS", "SERVICE_DESK"]
CATEGORIES_LIST = ['Infrastructure', 'Application', 'Security', 'Database', 'Network', 'Access Management']

SupervisorPrompt = f"""
You are the L1 Support Supervisor. Your role is to classify, summarize, and route IT issues.

CLASSIFICATION RULES:
- CATEGORY: Pick from {CATEGORIES_LIST}.
- ASSIGNMENT_GROUP: 
    - Database/RDS/SQL issues -> DB_ADMIN
    - VPN/Connectivity/Internet -> NETWORK_TEAM
    - AWS/S3/EC2/Permissions -> CLOUD_OPS
    - Access/Passwords/Hardware -> SERVICE_DESK
- PRIORITY: Assess based on impact. 'Critical' is ONLY for total system-down scenarios.

ROUTING RULES:
1. If the user mentions a Ticket ID (e.g., 'INC123'), route to 'TicketAgent' immediately for lookup.
2. If it is a technical question, route to 'RAGAgent'.
3. If RAGAgent failed to find a fix, route to 'TicketAgent' for creation.
4. If the user's issue is resolved, route to 'FINISH'.

SUMMARIZATION:
Always write a detailed 'task_description' for the worker. Include the Title, the specific error reported, and any context found in the history.
"""

def SupervisorAgentNode(state:AgentState)->Command[Literal["RAGAgent", "TicketAgent", "__end__"]]:
    last_message = state["messages"][-1]
    if "successfully created" in last_message.content or "status of your ticket" in last_message.content:
         return Command(goto=END)

    message = [{"role": "system", "content": SupervisorPrompt}] + state["messages"]
    
    # We assume RouteDecision Pydantic model now includes 'assignment_group'
    response = Novalite_model.with_structured_output(RouteDecision).invoke(message)
    
    if response.next_agent == "FINISH":
        return Command(goto=END, update={"messages": [HumanMessage(content="Session concluded.")]})

    return Command(
        goto=response.next_agent,
        update={
            "messages": [
                HumanMessage(content=(
                    f"INSTRUCTION for {response.next_agent}: {response.task_description}\n"
                    f"ASSIGNMENT GROUP: {response.assignment_group}\n"
                    f"REASON: {response.reason}"
                ))
            ],
            "next_agent": response.next_agent,
        }
    )