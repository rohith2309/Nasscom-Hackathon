
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from typing import Literal

class AgentState(MessagesState):
    is_satisfied: bool
    is_relevant: bool
    category: str
    priority: str
    assignment_group: str
    rag_context: str


class FeedbackCheck(BaseModel):
    is_satisfied: bool = Field(description="True if the user is happy, False if they still have an issue.")
   


class ClassificationResult(BaseModel):
    category: Literal[
        'Infrastructure', 
        'Application', 
        'Security', 
        'Database', 
        'Network', 
        'Access Management'
    ] = Field(description="The category of the issue based on the user's description.")
    
    priority: Literal[
        'Low', 
        'Medium', 
        'High', 
        'Critical'
    ] = Field(description="The priority of the issue. Use 'Critical' only for total system outages.")

CATEGORY_TO_GROUP = {
    "Infrastructure": "INFRA_TEAM_L2",
    "Application": "APP_DEV_SUPPORT",
    "Security": "SOC_SECURITY_TEAM",
    "Database": "DB_ADMIN_GROUP",
    "Network": "NETWORK_OPERATIONS",
    "Access Management": "IAM_IDENTITY_TEAM"
}    

    
def get_classificationNode(llm):
    structured_llm_classification=llm.with_structured_output(ClassificationResult)
    
    def classification_node(state: AgentState): 
        last_user_message = state["messages"][-1].content
        
        prompt= (
            "Classify the following IT support request. "
            "You MUST choose exactly one category from: "
            "['Infrastructure', 'Application', 'Security', 'Database', 'Network', 'Access Management'].\n"
            f"User request: {last_user_message}"
        )
        
        analysis=structured_llm_classification.invoke(f"Classify the issue reported by the user into category and priority. user message: {prompt}")
        
        grp=CATEGORY_TO_GROUP.get(analysis.category, "GENERAL_SUPPORT")
        
        return {
            "category": analysis.category,
            "priority": analysis.priority,
            "assignment_group": grp
        }
    return classification_node    


def get_feedbackNode(llm):
    structured_llm=llm.with_structured_output(FeedbackCheck)
    
    def feeback_node(state: AgentState):
        last_user_message = state["messages"][-1].content
        
        analysis=structured_llm.invoke(f"is the user satisfied with the resolution? {last_user_message}")
       
        if  analysis.is_satisfied:
            return {"is_satisfied": True}
        else:
            return {"is_satisfied": False} 
     
    return feeback_node       