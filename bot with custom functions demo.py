import openai
import requests
import json
import os
import datetime
import csv

if not os.path.exists("logs"):
    os.makedirs("logs")

# 1️⃣ Find the directory this script lives in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2️⃣ Define your logs folder inside the script folder
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 3️⃣ Create it if needed
os.makedirs(LOG_DIR, exist_ok=True)

# 🔐 API key setup (secure!)
client = openai.OpenAI(api_key="YOUR_OPENAI_API_KEY")  # Replace with your actual key
alpha_vantage_key = "YOUR_ALPHA_VANTAGE_API_KEY"  # Replace with your actual key


def log_interaction(user_input, ai_reply):
    # 1) Build the path
    today = datetime.date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"chat_log_{today}.csv")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # DEBUG: print out what we’re about to do
    #print("📂 Current working dir:", os.getcwd())
    #print("📁 Logs folder exists:", os.path.exists("logs"))
    #print("📝 Writing to:", log_path)

    file_exists = os.path.isfile(log_path)

    try:
        with open(log_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["timestamp", "user_input", "ai_reply"])
            writer.writerow([timestamp, user_input, ai_reply])
        #print("✅ Logged successfully")
    except Exception as e:
        print("❌ Failed to log:", e)

# 📈 TOOL #1: Get stock daily data from Alpha Vantage
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

# 🪙 TOOL #2: Get crypto price from CoinGecko
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

# 🧰 Function definitions for tool use
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

# 🧠 Routing to actual function logic
tools = {
    "get_stock_daily": get_stock_daily,
    "get_crypto_price": get_crypto_price
}

# 💬 Main interaction loop using new SDK
def run_conversation(user_input):
    messages = [{"role": "user", "content": user_input}]

    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=messages,
        functions=function_definitions,
        function_call="auto"
    )
    message = response.choices[0].message

    # 1️⃣ Determine the AI reply, handling function calls
    if message.function_call:
        func_name = message.function_call.name
        args = json.loads(message.function_call.arguments)

        if func_name in tools:
            # call the tool
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
        # no function call → normal reply
        reply = message.content

    # 2️⃣ Always log, regardless of branch
    log_interaction(user_input, reply)

    # 3️⃣ Return the text
    return reply


# ▶️ Example interaction loop
if __name__ == "__main__":
    while True:
        user_input = input("Ask me something: ")
        reply = run_conversation(user_input)
        print("🤖:", reply)
