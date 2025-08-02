import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ---- Users Database Functions ----
def insert_user(username, password, email):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO usersTbl (username, password, email)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (username, password, email))
                user_id = cur.fetchone()[0]
                print(f"✅ User inserted with ID: {user_id}")
    except Exception as e:
        print("❌ Insert error:", e)

def update_user(user_id, new_username=None, new_password=None, new_email=None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                updates = []
                values = []
                if new_username:
                    updates.append("username = %s")
                    values.append(new_username)
                if new_password:
                    updates.append("password = %s")
                    values.append(new_password)
                if new_email:
                    updates.append("email = %s")
                    values.append(new_email)

                values.append(user_id)

                if updates:
                    query = f"UPDATE usersTbl SET {', '.join(updates)} WHERE id = %s"
                    cur.execute(query, values)
                    print("✅ User updated.")
                else:
                    print("⚠️ No fields provided for update.")
    except Exception as e:
        print("❌ Update error:", e)

def delete_user(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM usersTbl WHERE id = %s", (user_id,))
                print("✅ User deleted.")
    except Exception as e:
        print("❌ Delete error:", e)

def get_user_by_email(email):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM usersTbl WHERE email = %s", (email,))
                user = cur.fetchone()
                if user:
                    print(f"✅ User found: {user}")
                    return user
                else:
                    print("⚠️ No user found with that email.")
                    return None
    except Exception as e:
        print("❌ Query error:", e)


# ---- User Chats Database Functions ----
def insert_chat(userId):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                  INSERT INTO user_chats_tbl (user_id)
                  VALUES (%s) RETURNING chat_id;
                """, (userId,))
                return cur.fetchone()[0]
    except Exception as e:
        print("❌ Insert error:", e)
        return None

def get_user_chats(userId):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_id FROM user_chats_tbl WHERE user_id = %s", (userId,))
                chats = cur.fetchall()
                if chats:
                    print(f"✅ Chats found: {chats}")
                    return chats
                else:
                    print("⚠️ No chats found for this user.")
                    return []
    except Exception as e:
        print("❌ Query error:", e)
        return []

# ---- Chat History Database Functions ----
def insert_chat_message(userId, chatId, role, content, timestamp):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_history_tbl (user_id, chat_id, role, content, timestamp)
                    VALUES (%s, %s, %s, %s, %s);
                """, (userId, chatId, role, content, timestamp))
                print("✅ Chat message inserted.")
    except Exception as e:
        print("❌ Insert error:", e)



def delete_chat_messages(chatId):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM n8n_chat_histories WHERE session_id = %s", (chatId,))
                print("✅ Chat messages deleted.")
    except Exception as e:
        print("❌ Delete error:", e)


def get_chat_messages(chatId):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT message,session_id FROM n8n_chat_histories WHERE session_id = %s ORDER BY id", (str(chatId),))
                messages = cur.fetchall()
                if messages:
                    print(f"✅ Messages found: {messages}")
                    return messages
                else:
                    print("⚠️ No messages found for this chat.")
                    return []
    except Exception as e:
        print("❌ Query error:", e)
        return []

def delete_chat(chat_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Delete messages first (if you have foreign key constraints)
                cur.execute("DELETE FROM n8n_chat_histories WHERE session_id = %s", (str(chat_id),))
                # Delete the chat itself
                cur.execute("DELETE FROM user_chats_tbl WHERE chat_id = %s", (chat_id,))
                conn.commit()
    except Exception as e:
        print("❌ Delete chat error:", e)