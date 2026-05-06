from typing import Literal
from utils.utility import AgentState
from pydantic import BaseModel,Field
def rag_router(state: AgentState) -> Literal["ticketing_agent", "classification_node"]:
    if state.get("is_relevant"):
        return "ticketing_agent"  
    return "classification_node"     

def feedback_router(state: AgentState) -> Literal["end", "classification_node"]:
    if state.get("is_satisfied"):
        return "end"             
    return "classification_node"  

def base_router(state: AgentState)->Literal["rag_check", "ticketing_agent"]:
    initial_message = state["messages"][0].content.lower() if state["messages"] else ""


class RouteDecision(BaseModel):
    next_agent: Literal["RAGAgent", "TicketAgent", "FINISH"]
    reason: str           # Why this agent was selected
    task_description: str  # What the agent should do   
    category: Literal[
        'Infrastructure', 
        'Application', 
        'Security', 
        'Database', 
        'Network', 
        'Access Management'
    ] = Field(description="The category of the issue based on the user's description.")
    assignment_group: Literal["DB_ADMIN", "NETWORK_TEAM", "CLOUD_OPS", "SERVICE_DESK", "NOT_APPLICABLE"]
    priority: Literal[
        'Low', 
        'Medium', 
        'High', 
        'Critical'
    ] = Field(description="The priority of the issue. Use 'Critical' only for total system outages.")