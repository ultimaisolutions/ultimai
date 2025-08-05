import streamlit as st
import db
import datetime
import os
import dotenv
import requests
import pandas as pd
from io import StringIO
from PyDesmos import Graph
import streamlit.components.v1 as components

# Load API keys (if needed for other services)
dotenv.load_dotenv()

st.set_page_config(page_title="Test Chat App", page_icon="💬", layout="wide")

# ------------------ Session State ------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_chat' not in st.session_state:
    st.session_state.current_chat = None
if 'chat_buffer' not in st.session_state:
    st.session_state.chat_buffer = []

# ------------------ Login/Register ------------------
def login_ui():
    st.title("Login / Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = db.get_user_by_email(email)
            if user and user[2] == password:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        name = st.text_input("Name")
        email = st.text_input("Register Email")
        password = st.text_input("Register Password", type="password")
        if st.button("Register"):
            try:
                db.insert_user(name, password, email)
                st.success("Registered successfully! Please login.")
            except Exception as e:
                st.error("Error registering: " + str(e))

# ------------------ Conversation with LLM ------------------
def conversation(chat_id, prompt):
    WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
    url = f"{WEBHOOK_URL}/{chat_id}/{prompt}"
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Try to parse as JSON, fallback to raw text (CSV)
        try:
            result = response.json()
            return result.get("output", "[Error: No output in response]")
        except ValueError:
            # Not JSON — assume it's raw CSV
            return response.text

    except requests.exceptions.RequestException as e:
        print("Error while calling the API:", e)
        return "Sorry, there was an error contacting the LLM."


# ------------------ Chat UI ------------------
def chat_ui():
    st.sidebar.title("💬 Your Chats")
    chats = db.get_user_chats(st.session_state.user_id)

    if st.sidebar.button("➕ New Chat"):
        chat_id = db.insert_chat(st.session_state.user_id)
        st.session_state.current_chat = chat_id
        st.session_state.chat_buffer = []
        st.rerun()

    for chat in chats:
        chat_id = chat[0]
        chat_name = f"Chat {chat_id}"
        col1, col2 = st.sidebar.columns([4, 1])
        if col1.button(chat_name, key=f"chat-{chat_id}"):
            st.session_state.current_chat = chat_id
            st.session_state.chat_buffer = []
            st.rerun()
        if col2.button("🗑️", key=f"delete-{chat_id}"):
            db.delete_chat(chat_id)
            if st.session_state.current_chat == chat_id:
                st.session_state.current_chat = None
            st.rerun()

    if st.session_state.current_chat:
        st.title(f"🗨️ Chat {st.session_state.current_chat}")

        # Load and display previous messages
        messages = db.get_chat_messages(st.session_state.current_chat)

        for row in messages:
            parsed = row[0]  # This is already a dict

            # Determine sender type
            sender = "assistant" if parsed.get("type") == "ai" else "user"
            content = parsed.get("content", "")

            with st.chat_message(sender):
                st.markdown(content)

        for sender, msg in st.session_state.chat_buffer:
            with st.chat_message(sender):
                st.markdown(msg)

        # Handle user input
        if prompt := st.chat_input("Send a message"):
            timestamp = datetime.datetime.now()

            # Show user message
            st.session_state.chat_buffer.append(("user", prompt))
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Thinking..."):
                response = conversation(st.session_state.current_chat, prompt)
                #visualize(response)

            st.session_state.chat_buffer.append(("assistant", response))
            with st.chat_message("assistant"):
                st.markdown(response)

            #with st.chat_message("assistant"):
            #    # Check if response looks like a CSV
            #    if "x" in response and "y" in response and "," in response:
            #        visualize(response)
            #    else:
            #        st.markdown(response)

            # Clear buffer
            st.rerun()
            st.session_state.chat_buffer = []
# ------------------ Visualization ------------------
def visualize(response):
    try:
        # Decode BOM if present
        csv_clean = response.encode('utf-8').decode('utf-8-sig')
        df = pd.read_csv(StringIO(csv_clean))

        x_vals = df['x'].tolist()
        y_vals = df['y'].tolist()


        with Graph("StreamlitGraph") as G:
            #G(x=x_vals, y=y_vals)
            G.new_table({'x': x_vals, 'y': y_vals})
            

        #For Future use for visualization inside the chat
        #st.subheader("📊 Visualized Coordinates")
        #components.iframe(desmos_url, height=500)

    except Exception as e:
        st.error(f"Visualization failed: {e}")


# ------------------ Main ------------------
if not st.session_state.logged_in:
    login_ui()
else:
    chat_ui()
