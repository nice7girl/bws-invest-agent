import requests
import re

def find_channel_id(playlist_url):
    response = requests.get(playlist_url)
    # Look for "channelId":"..."
    match = re.search(r'"channelId":"([^"]+)"', response.text)
    if match:
        return match.group(1)
    # Look for browse_id
    match = re.search(r'"browseId":"([^"]+)"', response.text)
    if match:
        return match.group(1)
    return None

p1 = "https://www.youtube.com/playlist?list=PLVups02-DZEWWyOMyk4jjGaWJ_0o1N1iO"
p2 = "https://www.youtube.com/playlist?list=PLVups02-DZEUU9ozegLPLzfS6WiGGiI_T"

print(f"P1: {find_channel_id(p1)}")
print(f"P2: {find_channel_id(p2)}")
