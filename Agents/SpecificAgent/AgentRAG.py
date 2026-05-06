from utils.utility import create_agent
from langchain_aws import ChatBedrockConverse
from Agents.AgentTools.RAGTool import RAG_check_node
import os
from langgraph.types import Command
from typing import Literal
from utils.utility import AgentState
from langgraph.types import Command
from langchain_core.messages import HumanMessage



Novalite_model=ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    temperature=0, 
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )

RAGPrompt="""

Your task is to fetch relevant information from the RAG tool based on the user's query. with the RAG tool you will get relevant information from the closed tickets which can help you to answer the user's query.

NOTE YOU ARE NOT SUPPOSED TO ANSWER THE WITHOUT CHECKING THE RAG TOOL. ALWAYS CHECK THE RAG TOOL FOR RELEVANT INFORMATION AND THEN ANSWER THE USER'S QUERY BASED ON THE INFORMATION FETCHED FROM THE RAG TOOL.

YOU ARE NOT SUPPOSED TO ANSWER THE USER'S QUERY BASED ON YOUR KNOWLEDGE CUTOFF. YOU MUST USE THE RAG TOOL TO FETCH RELEVANT INFORMATION AND THEN ANSWER THE USER'S QUERY BASED ON THAT INFORMATION.

"""


RAG_agent=create_agent(RAGPrompt,Novalite_model,[RAG_check_node])

# result = RAG_agent.invoke({"messages": [HumanMessage(content="RDS backup failed and the database is down need help")]})
# print(result)

def RagAgentNode(state:AgentState)->Command[Literal["SupervisorAgent"]]:
    query = state["messages"]
    result = RAG_agent.invoke({"messages": query})
    return Command(
        goto='SupervisorAgent',
        update={"messages": result["messages"]}
    )
