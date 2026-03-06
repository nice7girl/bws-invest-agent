import os
import requests
import re
import time
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import sys
import io

# Removed manual sys.stdout/stderr wrapping to fix I/O issues

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
API_KEY = os.getenv("GOOGLE_API_KEY", "")
genai.configure(api_key=API_KEY)

PLAYLISTS = {
    "AM": "https://www.youtube.com/playlist?list=PLVups02-DZEWWyOMyk4jjGaWJ_0o1N1iO", # ӽ 𴶷ƾ
    "PM": "https://www.youtube.com/playlist?list=PLVups02-DZEUU9ozegLPLzfS6WiGGiI_T"  #  ̷
}

OUTPUT_DIR = os.path.join("output", "reports")
LOG_FILE = "logs/agent_b.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted_message + "\n")
    except Exception as e:
        print(f"Logging file error: {e}")
        
    try:
        # Avoid print encoding issues on Windows
        print(formatted_message.encode('utf-8', errors='replace').decode('utf-8'))
    except Exception as e:
        pass

def get_latest_video_id(playlist_url, timeframe):
    try:
        import json
        response = requests.get(playlist_url, timeout=10)
        if response.status_code != 200:
            return None, None
            
        # 1. Robust JSON extraction from ytInitialData
        match = re.search(r'var ytInitialData = (\{.*?\});', response.text)
        video_data = []
        if match:
            try:
                data = json.loads(match.group(1))
                # navigate to contents (this path is typical for desktop)
                try:
                    section_contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
                    for item in section_contents:
                        if 'playlistVideoRenderer' in item:
                            vid = item['playlistVideoRenderer']['videoId']
                            title = item['playlistVideoRenderer']['title']['runs'][0]['text']
                            video_data.append((vid, title))
                except (KeyError, IndexError, TypeError):
                    pass
            except Exception as e:
                log(f"JSON navigation failed: {e}")
        
        # 2. Fallback to regex if JSON extraction yielded nothing
        if not video_data:
            # Match specifically in playlistVideoRenderer context to pair correctly
            video_data = re.findall(r'"playlistVideoRenderer":\{"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\]', response.text)
        
        # 3. Last resort legacy regex
        if not video_data:
            video_data = re.findall(r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\]', response.text)

        today_str = datetime.now().strftime("%Y%m%d")
        today_kr_str = f"{datetime.now().month}월{datetime.now().day}일"
        
        for video_id, title in video_data:
            if today_str in title or today_kr_str in title:
                log(f"Matched today's video: {title} ({video_id})")
                return video_id, title
        
        if video_data:
            log(f"No date match, using latest from playlist: {video_data[0][1]} ({video_data[0][0]})")
            return video_data[0][0], video_data[0][1]
            
    except Exception as e:
        log(f"Error fetching playlist: {e}")
    return None, None

def get_transcript(video_id):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        log(f"Attempting transcript for {video_id}")
        
        transcript_list = None
        
        # 1. Try static list_transcripts()
        if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
            try:
                log("Trying YouTubeTranscriptApi.list_transcripts(video_id)...")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                log("Success with list_transcripts()")
            except Exception as e:
                log(f"list_transcripts() failed: {e}")

        # 2. Try static list()
        if not transcript_list and hasattr(YouTubeTranscriptApi, 'list'):
            try:
                log("Trying YouTubeTranscriptApi.list(video_id)...")
                transcript_list = YouTubeTranscriptApi.list(video_id)
                log("Success with YouTubeTranscriptApi.list()")
            except Exception as e:
                log(f"YouTubeTranscriptApi.list() failed: {e}")

        # 3. Try instance list()
        if not transcript_list:
            try:
                log("Trying api = YouTubeTranscriptApi(); api.list(video_id)...")
                api = YouTubeTranscriptApi()
                transcript_list = api.list(video_id)
                log("Success with instance list()")
            except Exception as e:
                log(f"Instance list() failed: {e}")

        if transcript_list:
            # Try to find Korean transcript
            try:
                transcript = transcript_list.find_generated_transcript(['ko'])
            except:
                try:
                    transcript = transcript_list.find_transcript(['ko'])
                except:
                    # Last resort: first available
                    transcript = next(iter(transcript_list))
                
            data = transcript.fetch()
            return " ".join([s.get('text', '') if isinstance(s, dict) else getattr(s, 'text', '') for s in data])
        
    except Exception as e:
        log(f"Transcript API failed for {video_id}: {e}")
        
    # Fallback to description if transcript is unavailable
    try:
        log(f"Falling back to video description for {video_id}")
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Extract description from meta tags or script
            meta_match = re.search(r'"shortDescription":"(.*?)"', response.text)
            if meta_match:
                # Clean up escaped newlines and unicode
                desc = meta_match.group(1).replace("\\n", "\n")
                log("Successfully retrieved video description as fallback.")
                return f"[VIDEO DESCRIPTION FALLBACK]\n{desc}"
    except Exception as e:
        log(f"Description fallback failed: {e}")
        
    return None

def analyze_report(transcript, timeframe):
    if not transcript:
        return "No transcript available for analysis."
    # Use gemini-flash-latest which typically has better quota
    model = genai.GenerativeModel('gemini-flash-latest')
    display_timeframe = "AM Brief" if timeframe == "AM" else "PM Brief"
    
    prompt = f"""
    당신은 <우석에 닿기를> 투자 동향 분석의 전문 투자 분석 에이전트입니다.
    제공되는 YouTube 영상 자막을 분석하여 [국내주식, 미국주식, 코인] 중심의 '{display_timeframe}' 보고서를 작성하세요.
    
    [분석 대상 자막]
    {transcript}
    
    [보고서 형식 및 지침 - 매우 중요]
    1. 제목: ☀️ <b>{display_timeframe} 투자 동향 요약</b> (반드시 이모지와 굵은 글씨 사용)
    2. 섹션별 필수 포함 내용 및 구조: (각 큰 시장 섹션 전에는 반드시 굵은 실선 `━━━━━━━━━━━━━━━━━━━━━━━━━` 을 넣어주세요)
    
       ━━━━━━━━━━━━━━━━━━━━━━━━━
       ■ 🇰🇷 국내 시장 요약
       
       **[지수 동향]**
         - 코스피(KOSPI): 종가, 등락 폭 등 설명
         
         - 코스닥(KOSDAQ): 종가, 등락 폭 등 설명
         
         - 수급 동향: 외인/기관 매매 동향 요약
         
         - 거래대금: 주요 내용
       
       -------------
       **[주요 정책]**
         - 정부 발표, 금리 관련 공시 등 주요 정책 이슈 설명
         
         - 시장 영향력이 큰 기타 항목 설명
       
       -------------
       **[주요 섹터 및 종목]**
         - 특징주1(+%): 급등/급락 사유...
         
         - 특징주2(-%): 주요 원인 등...
         
       ━━━━━━━━━━━━━━━━━━━━━━━━━
       ■ 🇺🇸 미국 시장 요약
       
       **[지수 동향]**
         - 다우/나스닥/S&P500 등락 및 변동 이유
         
         - 주요 특징 (예: 기술주 중심 차익 매물 등)
       
       -------------
       **[주요 정책]**
         - 연준 인사 발언, 물가 지표, 달러 인덱스 등
         
         - 환율 변동 및 주요 경제 지표 상황
       
       -------------
       **[주요 섹터 및 종목]**
         - 주요 빅테크 등 특징주 요약
         
         - AI 인프라 관련주 등 미 증시 핵심 움직임
         
       ━━━━━━━━━━━━━━━━━━━━━━━━━
       ■ 🪙 코인 시장 동향
       
       **[시장 심리 및 영향 요인]**
         - 위험자산 회피, 거시 연동성 등 시황과 관련된 거시적인 흐름 작성
         
         - 거시 경제 연동성 위주 상세 풀이 (미언급 등 표현 절대 금지)
         
       ━━━━━━━━━━━━━━━━━━━━━━━━━
       ■ 💡 BWS 투자 인사이트
       
       **[핵심 코멘트 및 전략]**
         - 시장의 핵심 코멘트 정리
         
         - 향후 투자 전략 방향성 1
         
         - 향후 투자 전략 방향성 2
         
    3. 보고서 작성 원칙 (가독성 최우선):
       - 소제목은 이모지 없이 반드시 `**[소제목]**` 형식으로 작성하고, 옆에 내용을 바로 적지 말고 **반드시 아랫줄**부터 하위 항목으로 기재하세요.
       - 하위에 기재하는 개조식(`- `) 설명 항목들 사이에는 **반드시 빈 줄(공백 라인)**을 하나씩 넣어 문단이 시원하게 구분되게 하세요. (위 2번 예시 구조 참고, 단락이 붙어있지 않도록 주의!)
       - 소제목과 소제목 사이(예: `[지수 동향]`과 `[주요 정책]` 사이)에는 `-------------` (하이픈 13개) 정도의 가벼운 선을 넣어 단락을 구분해 주세요.
       - 각 큰 섹션(국내 시장, 미국 시장, 코인 시장, 투자 인사이트) 직전에는 굵은 실선 구분자(`━━━━━━━━━━━━━━━━━━━━━━━━━`)를 1줄만 짧게 넣어 4가지 파트가 시각적으로 확실히 나뉘게 하세요.
       - 주요 종목명, 상승/하락률, 핵심 수치, 중요 키워드 등은 반드시 **굵은 글씨(**텍스트**)**로 강조하세요.
    4. 내용: 반드시 오늘 날짜({datetime.now().strftime("%Y-%m-%d")}) 기준으로 가장 최신 정보를 우선하여 요약하세요. (자막에 해당 내용이 부족할 경우, 있는 내용 내에서 카테고리에 맞게 최대한 분류할 것)
    5. 면책 조항: 보고서 맨 마지막에 빈 줄을 둔 후, 다음 면책 조항을 포함하세요:
       "⚠️ 본 보고서는 참고용으로만 제공되며, 투자 결정에 대한 모든 책임은 투자자 본인에게 있습니다."
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        log(f"Error during Gemini analysis: {e}")
        return None

def run_agent_b(timeframe):
    log(f"Starting Agent B for {timeframe}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)  # output/reports 자동 생성
    playlist_url = PLAYLISTS.get(timeframe)
    
    for attempt in range(1, 4):
        video_id, title = get_latest_video_id(playlist_url, timeframe)
        if video_id:
            log(f"Found video ID: {video_id} | Title: {title} (Attempt {attempt})")
            transcript = get_transcript(video_id)
            if transcript:
                report = analyze_report(transcript, timeframe)
                if report:
                    date_str = datetime.now().strftime("%Y%m%d")
                    file_name = f"{date_str}_{timeframe}_분석보고서.md"
                    file_path = os.path.join(OUTPUT_DIR, file_name)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(report)
                    
                    log(f"Report saved to {file_path}")
                    return True
            else:
                log(f"Failed to extract transcript for {video_id}.")
        else:
            log(f"No video found in playlist (Attempt {attempt}).")
        
        if attempt < 3:
            log("Waiting 30 seconds before retry...")
            time.sleep(30) # 30 seconds for testing
            
    log(f"당일 [{timeframe}] 업데이트 없음")
    return False

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "AM"
    run_agent_b(mode)
