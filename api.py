from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from manager_agent import ManagerAgent
import os

app = FastAPI()
load_dotenv()


openai_api_key = os.getenv("OPENAI_API_KEY")
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
manager_agent = ManagerAgent(openai_api_key, neo4j_uri, neo4j_user, neo4j_password)

class AgentResponse(BaseModel):
    mode: str
    categories: Optional[List[dict]] = None
    recommendations: Optional[List[dict]] = None
    emotion_response: Optional[str] = None
    

@app.get("/process_query/{query}", response_model=AgentResponse)
def agent(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    response = manager_agent.process_query(query)
    
    if not response:
        raise HTTPException(status_code=500, detail="No response from the model")
    
    return response
