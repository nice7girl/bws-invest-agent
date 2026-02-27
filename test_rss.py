import requests
from datetime import datetime, date
import xml.etree.ElementTree as ET

def check_playlist_rss(playlist_id):
    url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"RSS works for {playlist_id}")
        return response.text
    else:
        print(f"RSS failed for {playlist_id}: {response.status_code}")
        return None

playlist_id = "PLVups02-DZEWWyOMyk4jjGaWJ_0o1N1iO"
content = check_playlist_rss(playlist_id)
if content:
    print(content[:1000])
