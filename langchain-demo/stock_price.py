import os
import json
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.tools import tool

load_dotenv()

ALPHA_VANTAGE_API_KEY=os.getenv("ALPHA_VANTAGE_API_KEY")
if not ALPHA_VANTAGE_API_KEY:
    raise RuntimeError("ALPHA_VANTAGE_API_KEY is not set. Add it in .env file.")

DATE_FORMAT = "%Y-%m-%d"

session = requests.Session()

@tool
def get_current_date() -> str:
  """Returns today's date in YYYY-MM-DD format."""
  return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")

@tool
def get_stock_data(stock_symbol: str, date: str):
    """"Get the daily open, high, low, close and volume for one stock on one date.
    
    Covers the past 100 trading days.

    Args:
        stock_symbol: Ticker symbol of the stock the user requested, e.g. "GOOG".
        date: Trading date the user requested, in %Y-%m-%d format.
    """

    try:
        requested_date = datetime.strptime(date, DATE_FORMAT).date()
    except ValueError:
        return f"Invalid date {date!r}. Expected YYYY-MM-DD format."

    url = f'https://www.alphavantage.co/query'
    try:
        response = session.get(
            url,
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": stock_symbol,
                "apikey": ALPHA_VANTAGE_API_KEY,
            },
            timeout=15,
        )

        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as error:
        return f"Request to Alpha Vantage failed: {type(error).__name__}"
    except ValueError:
        return "Alpha Vantage returned a response that is not valid JSON."

    series = payload.get("Time Series (Daily)")
    if not series:
        return f"Alpha Vantage returned no daily time series for {stock_symbol!r}."

    last_refreashed = payload.get("Meta Data", {}).get("3. Last Refreshed", "")
    if last_refreashed:
        latest_date = datetime.strptime(last_refreashed[:10], DATE_FORMAT).date()
        if requested_date > latest_date:
            return (
                f"{date} is later than the latest US-time record ({latest_date}). "
                f"Retry using {latest_date} or an earlier date."
            )
    quote = series.get(date)
    if quote is None:
        return f"No stock price record for {stock_symbol} on {date}. "

    return json.dumps({"symbol": stock_symbol, "date": date, **quote})
        

SYSTEM_PROMPT = (
    "You are an expert in finance and investment. "
    "Call get_current_date to resolve relative or year-less dates before "
    "calling get_stock_data, and report the figures the tool returns verbatim."
)


def main():    
    agent = create_agent(
        model="ollama:gemma4:cloud",
        tools=[get_current_date, get_stock_data],
        system_prompt=SYSTEM_PROMPT,
    )

    result = agent.invoke(
        {"messages": [{"role":"user", "content": "What is GOOG stock price on 21 Aug?"}]}
    )

    print(result["messages"])

if __name__ == "__main__":
    main()