from langgraph.graph import StateGraph, START ,END
from langgraph.prebuilt import ToolNode,tools_condition
from Agents.RAGAgent import RAG_check_node
from Agents.TicketingAgent import create_ticket, lookup_ticket
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, AIMessage
import boto3
import os
from dotenv import load_dotenv
from utils.utility import  get_feedbackNode,AgentState,get_classificationNode,is_ai_speaking
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel,Field


from Agents.SpecificAgent.AgentSupervisor import SupervisorAgentNode
from Agents.SpecificAgent.AgentTicket import TicketAgentNode
from Agents.SpecificAgent.AgentRAG import RagAgentNode

from utils.Routers import rag_router, feedback_router

load_dotenv()

memory = MemorySaver()
Novalite_model=ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    temperature=0, 
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
       
    )

from typing import Literal
from pydantic import BaseModel, Field

class Router(BaseModel):
    """The Supervisor's routing decision."""
    next_agent: Literal["RAG_Agent", "Ticketing_Agent", "FINISH"] = Field(
        
        description="""
        - RAG_Agent: Use for ALL technical 'how-to', troubleshooting, or error resolution questions. 
        - Ticketing_Agent: ONLY use for creating new tickets, checking ticket status, or when the user explicitly asks for a human.
        - FINISH: Use only when the user's issue is fully resolved or if they are just saying hello and asking how you can help them.
        """
    )
    instructions: str = Field(
        description="Specific instructions or context to pass to the next worker."
    )

def supervisor_node(state: AgentState):
    planner = Novalite_model.with_structured_output(Router)
    rag_already_attempted = state.get("rag_tried", False)
    rag_was_successful = state.get("is_relevant", False)

    messages = state.get("messages", [])
    if not messages:
        return {"next_agent": "RAG_Agent"}
        
    last_message = messages[-1]

    if is_ai_speaking(last_message):
        # Ensure we don't stop the graph if the AI is mid-tool-call
        has_tool_calls = hasattr(last_message, "tool_calls") and last_message.tool_calls
        if not has_tool_calls:
            return {"next_agent": "FINISH"}

    # RAG failed → force Ticketing
    if rag_already_attempted and not rag_was_successful:
        return {"next_agent": "Ticketing_Agent"}

    # RAG succeeded → go to Ticketing to present results
    if rag_already_attempted and rag_was_successful:
        return {"next_agent": "Ticketing_Agent"}

    # Default: LLM decides (only reached on first turn, before RAG has run)
    system_prompt = (
        "You are the L1 Support Supervisor. Your job is to manage the flow between workers.You can respond to users greetings and ask how can I help you?\n"
        "Workers:\n"
        "- RAG_Agent: Use this for technical questions or if the user needs a solution.\n"
        "- Ticketing_Agent: Use this if RAG failed, if the user is unhappy with the fix, "
        "or if they want to create/look up a ticket.\n"
        "- FINISH: Use this only if the user's issue is fully resolved.Also in the initial conversation where the user introduces themselves and asks for help.\n\n"
        "RULES:\n"
        "1. NEVER route to RAG_Agent if rag_tried is already True.\n"
        "2. If a technical issue is reported and RAG hasn't been tried, use RAG_Agent.\n"
        "3. For ticket creation/lookup requests, use Ticketing_Agent directly.\n"
    )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    decision = planner.invoke(messages)
    print(f"--- [Supervisor Debug] RAG Tried: {rag_already_attempted}, RAG Success: {rag_was_successful} ---")
    print(f"--- [Supervisor Decision]: {decision} ---")

    return {"next_agent": decision.next_agent}




FeedBackNode=get_feedbackNode(Novalite_model)
ClassificationNode=get_classificationNode(Novalite_model)






# --- Graph Construction ---
workFlow = StateGraph(AgentState)

# 1. Add All Nodes
workFlow.add_node("SupervisorAgent", SupervisorAgentNode)
workFlow.add_node("RAGAgent", RagAgentNode)
workFlow.add_node("TicketAgent", TicketAgentNode)


# 2. Define the Entry Point
workFlow.add_edge(START, "SupervisorAgent")


app = workFlow.compile(checkpointer=memory)



def main():
    config = {"configurable": {"thread_id": "session_v1"}}
    print("--- 🤖 L1 IT Support Supervisor Active ---")
    
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        for event in app.stream({"messages": [("user", user_input)]}, config):
            # event is a dict: {'node_name': { ... node output ... }}
            for node_name, value in event.items():
                
                print(f"--- [Event] Node: {node_name} | Output: {value["messages"][-1]} ---")
                

if __name__ == "__main__":
    main()


