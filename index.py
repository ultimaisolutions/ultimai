import openai
import requests
import json
import os
import datetime
import csv
import dotenv
import streamlit as st

# Streamlit Page Config
st.set_page_config(page_title="AI Chat with Tools", layout="centered")
st.title("💬 AI Chat Assistant with Tools")

# Ensure logs directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Load API keys
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

# OpenAI client
client = openai.OpenAI()

# ---- Utility Functions ----

def get_stock_daily(symbol: str) -> dict:
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={alpha_vantage_key}'
    r = requests.get(url)
    data = r.json()
    if "Time Series (Daily)" not in data:
        return {"error": "Unable to retrieve stock data. Please check the symbol."}
    latest_date = next(iter(data["Time Series (Daily)"]))
    latest_data = data["Time Series (Daily)"][latest_date]
    return {
        "symbol": symbol.upper(),
        "date": latest_date,
        "open": latest_data["1. open"],
        "high": latest_data["2. high"],
        "low": latest_data["3. low"],
        "close": latest_data["4. close"],
        "volume": latest_data["5. volume"],
    }

def get_crypto_price(coin: str, currency: str) -> dict:
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin.lower(), "vs_currencies": currency.lower()}
    response = requests.get(url, params=params)
    data = response.json()
    if coin.lower() not in data:
        return {"error": "Invalid coin or data unavailable"}
    return {
        "coin": coin,
        "currency": currency,
        "price": data[coin.lower()][currency.lower()]
    }

function_definitions = [
    {
        "name": "get_stock_daily",
        "description": "Get the most recent daily stock data for a given symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. 'AAPL'"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_crypto_price",
        "description": "Get the latest price for a cryptocurrency in a given fiat currency",
        "parameters": {
            "type": "object",
            "properties": {
                "coin": {
                    "type": "string",
                    "description": "Name of the crypto coin, e.g. 'bitcoin'"
                },
                "currency": {
                    "type": "string",
                    "description": "Fiat currency, e.g. 'usd', 'eur', 'nis'"
                }
            },
            "required": ["coin", "currency"]
        }
    }
]

tools = {
    "get_stock_daily": get_stock_daily,
    "get_crypto_price": get_crypto_price
}

def log_interaction(user_input, ai_reply):
    today = datetime.date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"chat_log_{today}.csv")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(log_path)
    try:
        with open(log_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["timestamp", "user_input", "ai_reply"])
            writer.writerow([timestamp, user_input, ai_reply])
    except Exception as e:
        st.error(f"Failed to log interaction: {e}")

def run_conversation(user_input):
    messages = [{"role": "user", "content": user_input}]
    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=messages,
        functions=function_definitions,
        function_call="auto"
    )
    message = response.choices[0].message

    if message.function_call:
        func_name = message.function_call.name
        args = json.loads(message.function_call.arguments)
        if func_name in tools:
            result = tools[func_name](**args)
            messages.append(message)
            messages.append({
                "role": "function",
                "name": func_name,
                "content": json.dumps(result)
            })
            followup = client.chat.completions.create(
                model="gpt-4-0613",
                messages=messages
            )
            reply = followup.choices[0].message.content
        else:
            reply = f"Function '{func_name}' not recognized."
    else:
        reply = message.content

    log_interaction(user_input, reply)
    return reply

# ---- Session State ----

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- Chat Display ----

for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(entry["user"])
    with st.chat_message("assistant"):
        st.markdown(entry["bot"])

# ---- Chat Input ----

user_prompt = st.chat_input("Ask me anything...")

if user_prompt:
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.spinner("🤖 Thinking..."):
        bot_response = run_conversation(user_prompt)

    with st.chat_message("assistant"):
        st.markdown(bot_response)

    # Store in history
    st.session_state.chat_history.append({
        "user": user_prompt,
        "bot": bot_response
    })
