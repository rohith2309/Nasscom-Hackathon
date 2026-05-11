from utils.utility import create_agent, AgentState, Novalite_model
from langchain_core.messages import SystemMessage
from typing import Literal
from langgraph.types import Command
from Agents.AgentTools.CreateTool import create_ticket
from Agents.AgentTools.LookupTool import lookup_ticket 

TicketAgentPrompt = """
You are a helpful assistant agent responsible for creating and looking up tickets.
You have access to two tools:
- create_ticket: creates a new ticket
- lookup_ticket: looks up an existing ticket by ID

RULES:
- Never ask the user for priority, category, or assignment group — use values from context
- If a ticket ID is mentioned, use lookup_ticket
- Otherwise use create_ticket

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

AgentTicket = create_agent(TicketAgentPrompt, Novalite_model, [create_ticket, lookup_ticket])

def TicketAgentNode(state: AgentState) -> Command[Literal["SupervisorAgent"]]:
    # Read classification from state — set by SupervisorAgent
    category         = state.get("category", "Infrastructure")
    priority         = state.get("priority", "Medium")
    assignment_group = state.get("assignment_group", "SERVICE_DESK")

    # Inject as SystemMessage — local only, never stored in state
    context = SystemMessage(content=(
        f"Ticket classification already decided — do not change or ask user:\n"
        f"Category: {category} | Priority: {priority} | Group: {assignment_group}"
    ))

    result = AgentTicket.invoke({
        "messages": [context] + state["messages"]   # prepend, don't append
    })

    # Only return NEW messages the agent added, not the full history
    new_messages = result["messages"][len(state["messages"]):]

    return Command(
        goto="SupervisorAgent",
        update={"messages": new_messages}
    )    