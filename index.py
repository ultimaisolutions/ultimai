import openai
import requests
import json
import os
import datetime
import csv
import dotenv
import streamlit as st

# 📌 Set Streamlit page config
st.set_page_config(page_title="Bot Function Assistant", layout="centered")
st.title("🤖 Bot Function Assistant")

# 📁 Ensure logs directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 🔐 Load API Keys from .env
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

# ✅ Initialize OpenAI client
client = openai.OpenAI()

# 📊 Stock tool
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

# 💰 Crypto tool
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

# 📝 Function definitions for OpenAI
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

# 🧰 Tool routing
tools = {
    "get_stock_daily": get_stock_daily,
    "get_crypto_price": get_crypto_price
}

# 🗂️ Log conversations
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

# 🔁 Run a conversation using OpenAI function calling
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

# 🧾 Streamlit UI
with st.form("chat_form"):
    user_input = st.text_input("Ask me something", placeholder="e.g. What is the current price of bitcoin in USD?")
    submitted = st.form_submit_button("Submit")

if submitted and user_input:
    with st.spinner("Thinking..."):
        reply = run_conversation(user_input)
        st.markdown("### 🤖 Response:")
        st.markdown(reply)
