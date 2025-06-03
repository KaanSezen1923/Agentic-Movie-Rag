from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from category_agent import CategoryAgent
from emotion_agent import EmotionAgent
from recommender_agent import RecommenderAgent
from neo4j import GraphDatabase
import json
from dotenv import load_dotenv
import os

load_dotenv()


class ManagerAgent:
    def __init__(self, api_key: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.openai_api_key = api_key
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=self.openai_api_key)
        self.category_agent = CategoryAgent(self.openai_api_key, neo4j_uri, neo4j_user, neo4j_password)
        self.emotion_agent = EmotionAgent(self.openai_api_key)
        self.recommender_agent = RecommenderAgent(self.openai_api_key)
        

    def process_query(self, query: str):
        

        
        category_result = self.category_agent.category_agent(query)
        
        if category_result and any(c.get("results") for c in category_result):
            
            print("🔍 Category detected. Getting movie recommendations...")
            recommendations = self.recommender_agent.recommend(query, category_result)
            return {
                    "mode": "category",
                    "categories": category_result,
                    "recommendations": recommendations
            }
        else:
                
            print("💬 No specific category found. Engaging emotion agent...")
            emotion_response = self.emotion_agent.detect_emotion(query)
            return {
                    "mode": "emotion",
                    "emotion_response": emotion_response
            }


            


    