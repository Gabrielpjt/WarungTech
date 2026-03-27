import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)

class WaterIntakeAgent:
    def __init__(self):
        self.history = []

    def analyze_intake(self, user_input):
        
        prompt = f"Analyze the following water intake data and provide feedback:\n{user_input}"

        response = llm.predict_messages([HumanMessage(content=prompt)])

        return response.content
