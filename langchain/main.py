import os
from dotenv import load_dotenv
from datetime import datetime

from langchain.agents import create_agent

load_dotenv()

OLLAMA_API_KEY=os.getenv("OLLAMA_API_KEY")

def get_stock_data(stock: str, date: str):
    print()


agent = create_agent