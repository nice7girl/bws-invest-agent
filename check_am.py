
import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

playlist_url = "https://www.youtube.com/playlist?list=PLVups02-DZEWWyOMyk4jjGaWJ_0o1N1iO"

try:
    response = requests.get(playlist_url, timeout=10)
    if response.status_code == 200:
        script_content = response.text
        video_data = re.findall(r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\]', script_content)
        print(f"Found {len(video_data)} videos in playlist.")
        for vid, title in video_data[:10]:
            print(f"ID: {vid} | Title: {title}")
    else:
        print(f"Failed: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
