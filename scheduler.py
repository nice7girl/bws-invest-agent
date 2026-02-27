import time
import subprocess
from datetime import datetime

# --- Configuration ---
AM_TIME = "08:40"
PM_TIME = "17:40"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_main(mode):
    log(f"Running main pipeline with mode: {mode}")
    try:
        # Run main.py with the specified mode
        subprocess.run(["python", "main.py", mode], check=True)
    except Exception as e:
        log(f"Error running pipeline: {e}")

def start_scheduler():
    log("BWS_Invest Scheduler started.")
    log(f"Scheduled times - AM: {AM_TIME}, PM: {PM_TIME}")
    
    while True:
        now = datetime.now().strftime("%H:%M")
        
        if now == AM_TIME:
            run_main("AM")
            time.sleep(60) # Prevent multiple runs within the same minute
        elif now == PM_TIME:
            run_main("PM")
            time.sleep(60)
            
        time.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    start_scheduler()
