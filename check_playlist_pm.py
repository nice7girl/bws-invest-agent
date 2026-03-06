
import requests
import re
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

PLAYLIST_PM = "https://www.youtube.com/playlist?list=PLVups02-DZEUU9ozegLPLzfS6WiGGiI_T"

def check_pm_playlist():
    print(f"Checking PM Playlist: {PLAYLIST_PM}")
    try:
        response = requests.get(PLAYLIST_PM, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch playlist: {response.status_code}")
            return
            
        # Extract ytInitialData
        match = re.search(r'var ytInitialData = (\{.*?\});', response.text)
        if not match:
            print("ytInitialData not found.")
            return
        
        data = json.loads(match.group(1))
        
        try:
            section_contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
            print("\nRecent videos in PM playlist (Top 10):")
            count = 0
            found_today = False
            for item in section_contents:
                if 'playlistVideoRenderer' in item:
                    vid = item['playlistVideoRenderer']['videoId']
                    title = item['playlistVideoRenderer']['title']['runs'][0]['text']
                    print(f"- {title} ({vid})")
                    if "3월 5일" in title or "3월5일" in title or "0305" in title:
                       found_today = True
                    count += 1
                    if count >= 10:
                        break
            
            print(f"\nFound today's video locally: {found_today}")
        except (KeyError, IndexError, TypeError) as e:
            print(f"Failed to parse JSON: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_pm_playlist()
    print(f"\nCurrent date/time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
