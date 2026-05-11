from utility import Novalite_model
import json

JUDGE_PROMPT="""You are evaluating a RAG retrieval system for an IT helpdesk.

Given:
- User Query: {query}
- Retrieved Document: {document}  
- Retrieved Resolution: {resolution}

Score the retrieval on these dimensions (1-5 each):

1. RELEVANCE: Does the document relate to the query?
2. RESOLUTION_QUALITY: Does the resolution actually solve the query?
3. FAITHFULNESS: Is the resolution grounded in the document content?

Respond ONLY in this JSON format, no other text:
{{
  "relevance": <1-5>,
  "resolution_quality": <1-5>,
  "faithfulness": <1-5>,
  "reasoning": "<one sentence explanation>",
  "overall_pass": <true|false>
}}

overall_pass = true only if relevance >= 4 AND resolution_quality >= 4"""

def judge_retrieval(query: str, document: str, resolution: str) -> dict:
    prompt = JUDGE_PROMPT.format(
        query=query,
        document=document,
        resolution=resolution
    )
    response = Novalite_model.invoke(prompt)
    raw_output = response.content[0].text
    return json.loads(raw_output)
    
    
    