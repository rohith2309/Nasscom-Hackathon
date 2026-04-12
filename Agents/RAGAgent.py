import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


from dotenv import load_dotenv
import os
from utils.utility import  AgentState
from chromadb.utils import embedding_functions
import chromadb
from langgraph.graph import StateGraph, START, MessagesState
load_dotenv()

CHROMA_DB_KEY=os.getenv('CHROMA_DB')
model = 'all-MiniLM-L6-v2'
ef= embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)

def RAG_check_node(state:AgentState):
    try:
        query = state["messages"][-1].content
        client = chromadb.CloudClient(
                api_key=CHROMA_DB_KEY,
                tenant='e5b49720-5aa8-4df7-bd60-0e8ea24aeda7',
                database='ticketing',
                
            )
    
        collection = client.get_or_create_collection(
            name="Incidents-collection",
            embedding_function=ef,
            metadata={'hnsw:space': 'cosine'}
        )


        results = collection.query(
             query_texts=[query],
             n_results=2,
             where={"status": "Closed"}
        )
    
        #calculate confidence score
    
        distances = results['distances'][0][0]
        confidence_score = 1 - distances
        THRESHOLD = 0.7
        
        if confidence_score >= THRESHOLD:
            return {
                    "is_relevant": True,
                    "messages":[("assistant",f"found a relevant document. results: {results}")]
                }
        else:
            print(f"--- RAG Debug: Confidence too low ({confidence_score:.2f}) ---")
            return {
                "is_relevant": False,
                "messages":[("assistant","couldn't find a relevant document in the knowledge classify and the query, create and assign a new ticket with the help available tools (create_ticket tool)")]
                }
    
        
    except Exception as e:
        return {"is_relevant": False, "messages": [("assistant", f"Error: {str(e)}")]}