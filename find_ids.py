import requests
import re

def get_channel_id(playlist_url):
    try:
        response = requests.get(playlist_url)
        if response.status_code == 200:
            match = re.search(r'"channelId":"([^"]+)"', response.text)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error: {e}")
    return None

playlists = {
    "Morning": "https://www.youtube.com/playlist?list=PLVups02-DZEWWyOMyk4jjGaWJ_0o1N1iO",
    "Evening": "https://www.youtube.com/playlist?list=PLVups02-DZEUU9ozegLPLzfS6WiGGiI_T"
}

for name, url in playlists.items():
    channel_id = get_channel_id(url)
    print(f"{name}: {channel_id}")
