
import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

video_id = "5jNIobMPY7I"
url = f"https://www.youtube.com/watch?v={video_id}"

try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        # Extract description (it's often in a script tag or hidden div)
        # simplified search
        desc_match = re.search(r'"description":\{"runs":\[\{"text":"(.*?)"\}', response.text)
        if desc_match:
            print(f"Description: {desc_match.group(1)}")
        else:
            print("Description not found via simple regex.")
    else:
        print(f"Failed to fetch video page: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
