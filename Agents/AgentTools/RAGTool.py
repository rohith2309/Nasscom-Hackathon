import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


from dotenv import load_dotenv
import os
from utils.utility import  AgentState
from chromadb.utils import embedding_functions
import chromadb
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, MessagesState
load_dotenv()

CHROMA_DB_KEY=os.getenv('CHROMA_DB')
model = 'all-MiniLM-L6-v2'
ef= embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)

@tool
def RAG_check_node(query :str):
    
    '''A tool to check the RAG database for relevant information based on the user's query. It takes the user's query as input and returns the relevant information from the RAG database if the confidence score is above a certain threshold.'''
    
    try:
        
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
            metadata = results['metadatas'][0]
            document_text = results['documents'][0]
            
            context_info= "\n".join([f"resolution:{m["resolution"]} \ndocuments:{d}" for m,d in zip(metadata, document_text)])
            
                
            
            return {
                    "is_relevant": True,
                    "rag_context":context_info,
                    "rag_tried": True
                }
        else:
            print(f"--- RAG Debug: Confidence too low ({confidence_score:.2f}) ---")
            return {"is_relevant": False, "rag_context": "", "rag_tried": True}
    
        
    except Exception as e:
        return {"is_relevant": False, "messages": [("assistant", f"Error: {str(e)}")]}