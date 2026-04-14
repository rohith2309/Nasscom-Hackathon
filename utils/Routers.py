from typing import Literal
from utils.utility import AgentState

def rag_router(state: AgentState) -> Literal["ticketing_agent", "classification_node"]:
    if state.get("is_relevant"):
        return "ticketing_agent"  
    return "classification_node"     

def feedback_router(state: AgentState) -> Literal["end", "classification_node"]:
    if state.get("is_satisfied"):
        return "end"             
    return "classification_node"  