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
# Set your Google API Key here or in environment variables
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCwLk9JO445ST-mdioNhM5G-jaKEqWlGwo")
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
        response = requests.get(playlist_url, timeout=10)
        if response.status_code != 200:
            return None, None
            
        # Extract video IDs and Titles to ensure we get today's video
        script_content = response.text
        video_data = re.findall(r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\]', script_content)
        
        today_str = datetime.now().strftime("%Y%m%d")
        
        for video_id, title in video_data:
            # Check if today's date is in title (e.g., 20260227)
            if today_str in title:
                log(f"Matched today's video: {title} ({video_id})")
                return video_id, title
        
        # If no date match, take the first one as fallback
        if video_data:
            return video_data[0][0], video_data[0][1]
            
    except Exception as e:
        log(f"Error fetching playlist: {e}")
    return None, None

def get_transcript(video_id):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        # Use api.list instead of api.list_transcripts
        transcript_list = api.list(video_id)
        
        try:
            transcript = transcript_list.find_generated_transcript(['ko'])
        except:
            transcript = transcript_list.find_transcript(['ko'])
            
        data = transcript.fetch()
        # Handle both dict and object types for segments
        parts = []
        for s in data:
            if isinstance(s, dict):
                parts.append(s.get('text', ''))
            else:
                parts.append(getattr(s, 'text', ''))
        return " ".join(parts)
    except Exception as e:
        log(f"Error fetching transcript for {video_id}: {e}")
        # Final desperate attempt if previous failed
        try:
            import youtube_transcript_api
            # try direct one-liner as second fallback
            data = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
            final_parts = []
            for s in data:
                if isinstance(s, dict):
                    final_parts.append(s.get('text', ''))
                else:
                    final_parts.append(getattr(s, 'text', ''))
            return " ".join(final_parts)
        except Exception as e2:
            log(f"Final fallback failed: {e2}")
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
    2. 섹션별 필수 포함 내용 및 구조: (각 섹션 제목 앞에는 이모지와 사각형 기호(■) 사용)
    
       ■ 🇰🇷 국내 시장 요약
         - [지수 동향]: 코스피/코스닥 종가, 등락 폭, 수급 주체별(외인/기관) 매매 동향 요약
         - [주요 정책]: 정부 발표, 금리 관련 공시, 규제 변화 등 시장 영향력이 큰 정책 이슈
         - [주요 섹터 및 종목]: 당일 주도 섹터(예: 반도체, 2차전지 등) 및 특징주 요약
         
       ■ 🇺🇸 미국 시장 요약
         - [지수 동향]: 다우/나스닥/S&P500 등락 및 주요 지표(국채 금리, 달러 인덱스 등) 변동
         - [주요 정책]: 연준(Fed) 인사 발언, 고용/물가 지표 발표 내용 및 시장 반응
         - [주요 섹터 및 종목]: 빅테크 실적, AI 인프라 관련주 등 미 증시 핵심 움직임
         
       ■ 🪙 코인 시장 동향
         - [시장 심리 및 영향 요인]:
           - 위험자산 회피, 거시 연동성 등 시황과 관련된 거시적인 흐름(예: 미 증시 투매 여파, 달러 강세, 투심 변화 등)을 작성하세요.
           - ※ 주의: 만약 유튜브 영상 자막 내에 구체적인 코인 시세나 내용에 대한 언급이 없다면, "분석 데이터 없음"이나 "미언급" 같은 표현을 절대 쓰지 말고 거시 경제 연동성 위주로 자연스럽게 채우세요.
         
       ■ 💡 BWS 투자 인사이트
         - 핵심 코멘트 및 향후 투자 전략 방향성 제시
         
    3. 보고서 작성 원칙 (가독성 최우선):
       - 모든 내용은 줄글 형태의 서술을 피하고, 각 카테고리([지수 동향] 등) 하위에 반드시 글머리 기호('- ')를 사용한 개조식(Bullet Point)으로 핵심만 간결하게 작성하세요.
       - 주요 종목명, 상승/하락률, 핵심 수치, 중요 키워드 등은 반드시 **굵은 글씨(**텍스트**)**로 강조하세요.
       - 각 섹션 사이, 그리고 의미가 구분되는 그룹 단위에는 빈 줄을 넣어 한눈에 구조가 들어오게 하세요.
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
