import os
import requests
import time
from datetime import datetime

# --- Configuration ---
def load_config():
    import json
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, value in config.items():
                    os.environ[key] = value
        except Exception:
            pass

load_config()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

WATCH_DIR = os.path.join("output", "reports")  # Agent B가 저장하는 위치
PROCESSED_LOG = "data/processed_reports.txt"

import re
import sys
import io

import html

# Removed manual sys.stdout/stderr wrapping

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [Agent W] {message}")

def get_processed_files():
    if not os.path.exists(PROCESSED_LOG):
        return set()
    with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def mark_as_processed(file_name):
    with open(PROCESSED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{file_name}\n")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            log(f"Telegram API Error: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        log(f"Error sending Telegram message: {e}")
        return False

def run_agent_w():
    log("Starting Agent W (Telegram Delivery)...")
    processed_files = get_processed_files()
    
    log(f"Watching directory: {WATCH_DIR}")
    if not os.path.exists(WATCH_DIR):
        log(f"Error: Directory {WATCH_DIR} does not exist.")
        return

    # 오늘 날짜 (YYYYMMDD) 추출
    today_prefix = datetime.now().strftime("%Y%m%d")
    
    # 쉼표로 구분된 여러 채팅 ID 처리
    raw_chat_ids = TELEGRAM_CHAT_ID.split(",")
    chat_ids = [cid.strip() for cid in raw_chat_ids if cid.strip()]
    
    if not chat_ids:
        log("Error: No TELEGRAM_CHAT_ID specified.")
        return
        
    log(f"Filtering for today's reports (prefix: {today_prefix})")
    log(f"Target Chat IDs: {chat_ids}")

    all_files = os.listdir(WATCH_DIR)
    # 당일 보고서만 필터링 (YYYYMMDD로 시작하는 파일)
    files = [f for f in all_files if f.startswith(today_prefix) and re.search(r'_(AM|PM)_.*\.md$', f)]
    log(f"Matching today's report files found: {len(files)}")
    
    for file_name in files:
        if file_name not in processed_files:
            log(f"Processing new report: {file_name}")
            file_path = os.path.join(WATCH_DIR, file_name)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Format message (use HTML for safer delivery and better formatting)
            timeframe = "AM Brief" if "_AM_" in file_name else "PM Brief"
            title = f"☀️ &lt;우석에 닿기를&gt; 투자 동향 분석 {timeframe}"
            
            safe_content = html.escape(content)
            formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_content)
            
            youtube_link = "https://www.youtube.com/@우석에닿기를"
            message = f"<b>{title}</b>\n\n{formatted_content}\n\n{youtube_link}"
            
            if len(message) > 4000:
                message = message[:4000] + "\n\n...(이하 생략)"
            
            success_count = 0
            for cid in chat_ids:
                # payload 복사하여 chat_id만 교체
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": cid,
                    "text": message,
                    "parse_mode": "HTML"
                }
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    if response.status_code == 200:
                        log(f"Successfully sent to Telegram Chat ID: {cid}")
                        success_count += 1
                    else:
                        log(f"Telegram API Error (ID: {cid}): {response.status_code} - {response.text}")
                except Exception as e:
                    log(f"Error sending to {cid}: {e}")

            if success_count > 0:
                mark_as_processed(file_name)

if __name__ == "__main__":
    run_agent_w()
