import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


from dotenv import load_dotenv
import os
load_dotenv()
from chromadb.utils import embedding_functions
import chromadb

CHROMA_DB_KEY=os.getenv('CHROMA_DB')

model = 'all-MiniLM-L6-v2'
ef= embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)

try:
    # df=pd.read_csv('Data/service_now_sample_dataset.csv')
    # metadata=df[['resolution', 'priority', 'category', 'status']].to_dict('records')
    # print(metadata)
    
    # text=(df['title']+" - "+df['description']).to_list()
    
    # print("setting up chromadb cloud client..")
    client = chromadb.CloudClient(
                api_key=CHROMA_DB_KEY,
                tenant='e5b49720-5aa8-4df7-bd60-0e8ea24aeda7',
                database='ticketing',
                
            )
    # print("client has been setup..")
    # search_text = (df['title'] + " " + df['description']).to_list()
    collection = client.get_or_create_collection(
            name="Incidents-collection",
            embedding_function=ef,
            metadata={'hnsw:space': 'cosine'}
    )
    # ids = [f"ticket_{i}" for i in range(len(text))]
    # collection.add(
    #             documents=search_text,
    #             metadatas=metadata,
    #             ids=ids
    #         )
    query = "how to login into the system?"
    results = collection.query(
        query_texts=[query],
        n_results=2,
        where={"status": "Closed"}
    )
    
    #calculate confidence score
    
    distances = results['distances'][0][0]
    confidence_score = 1 - distances
    THRESHOLD = 0.7
    
    print("Confidence score:", confidence_score)
    print("Is the retrieved document relevant?", confidence_score >= THRESHOLD)
    
    
    
    print("Query results:", results)
except Exception as e:
    print("couldn't read csv file \n ", e) 



