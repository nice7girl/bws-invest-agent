
import requests
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

playlist_url = "https://www.youtube.com/playlist?list=PLVups02-DZEUU9ozegLPLzfS6WiGGiI_T"

try:
    response = requests.get(playlist_url, timeout=10)
    if response.status_code == 200:
        # Find ytInitialData
        match = re.search(r'var ytInitialData = (\{.*?\});', response.text)
        if match:
            data = json.loads(match.group(1))
            # navigate to contents (this path is typical for desktop)
            # contents -> twoColumnBrowseResultsRenderer -> tabs -> 0 -> tabRenderer -> content -> sectionListRenderer -> contents -> 0 -> itemSectionRenderer -> contents -> 0 -> playlistVideoListRenderer -> contents
            try:
                videos = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
                print(f"Found {len(videos)} videos.")
                for v in videos[:5]:
                    if 'playlistVideoRenderer' in v:
                        info = v['playlistVideoRenderer']
                        vid = info['videoId']
                        title = info['title']['runs'][0]['text']
                        print(f"ID: {vid} | Title: {title}")
            except Exception as e:
                print(f"Navigation error: {e}")
        else:
            print("ytInitialData not found.")
    else:
        print(f"Failed: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
