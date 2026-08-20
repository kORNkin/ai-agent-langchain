import os
from dotenv import load_dotenv
from datetime import datetime

import requests

from langchain.agents import create_agent
from langchain.tools import tool

load_dotenv()

OLLAMA_API_KEY=os.getenv("OLLAMA_API_KEY")
ALPHA_VANTAGE_API_KEY=os.getenv("ALPHA_VANTAGE_API_KEY")

@tool
def get_current_date() -> str:
  """Returns today's date in YYYY-MM-DD format."""
  return datetime.now().strftime("%Y-%m-%d")

@tool
def get_stock_data(stock_symbol: str, date: str):
    """"Get Stock Price from the past 100 days

    Args:
            stock_symbol: Symbol of the stock user requested
            date: Stock data date user requested with %Y-%m-%d format
    """

    try:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock_symbol}&apikey={ALPHA_VANTAGE_API_KEY}'

        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            response = response.json()

            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                latest_date_obj = datetime.strptime(response['Meta Data']['3. Last Refreshed'], "%Y-%m-%d")

                if(date_obj > latest_date_obj):
                    return f"Provided date exceeds latest US-time record, you may retry using {response['Meta Data']['3. Last Refreshed']} as the latest date in the record."
                
                if(date not in response['Time Series (Daily)'].keys()):
                    return "No stock price record on this date."

                return response['Time Series (Daily)'][date]
            except Exception as e:
                return f"Error: {e}\n\n Response:{response}"
                
        else:
            return f"Failed with status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return e

agent = create_agent(
    model="ollama:gemma4:cloud",
    tools=[get_current_date, get_stock_data],
    system_prompt="You are an expert in financial and investmet",
)

result = agent.invoke(
    {"messages": [{"role":"user", "content": "What is GOOG stock price on 21 Aug?"}]}
)

print(result["messages"])