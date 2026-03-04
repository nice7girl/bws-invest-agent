import requests
import re
from datetime import datetime

url = "https://www.youtube.com/playlist?list=PLVups02-DZEUU9ozegLPLzfS6WiGGiI_T"
r = requests.get(url)
today_str = datetime.now().strftime("%Y%m%d")
print(f"Looking for {today_str} in titles...")
video_data = re.findall(r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\]', r.text)
for v_id, title in video_data[:10]:
    print(f" - {v_id}: {title}")
