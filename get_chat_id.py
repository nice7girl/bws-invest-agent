import requests
import json

TOKEN = "8589073083:AAHXqx9o5SZXciMxYKXbeKhwXQFWLW6X20s"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    if data.get("ok"):
        updates = data.get("result", [])
        if not updates:
            print("No updates found. Please send a message to the bot or add it to a channel.")
        else:
            for update in updates:
                chat = None
                if "message" in update:
                    chat = update["message"]["chat"]
                elif "channel_post" in update:
                    chat = update["channel_post"]["chat"]
                
                if chat:
                    print(f"Found Chat ID: {chat['id']} (Title/Name: {chat.get('title') or chat.get('first_name')})")
    else:
        print(f"Error: {data.get('description')}")
except Exception as e:
    print(f"Exception: {e}")
