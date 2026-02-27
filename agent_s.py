#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent S: Video Content Producer (제작 에이전트 - 간소화 버전)
1. 분석 보고서를 NotebookLM 노트북에 소스로 업로드
2. 5분 내외의 핵심 요약 영상 기획 스크립트 작성 (Gemini/NotebookLM 사용)
3. 작성된 스크립트를 NotebookLM 노트북에 2번째 소스로 업로드
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# skills 경로
SKILL_PATH = Path(__file__).parent / "antigravity-awesome-skills" / "skills" / "notebooklm"
SCRIPTS_PATH = SKILL_PATH / "scripts"

if sys.platform == "win32":
    VENV_PYTHON = SKILL_PATH / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = SKILL_PATH / ".venv" / "bin" / "python"
REPORTS_DIR = Path(__file__).parent / "output" / "reports"   # Agent B 보고서
SCRIPTS_DIR = Path(__file__).parent / "output" / "scripts"   # Agent S 영상기획

# NotebookLM 노트북 URL
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/2f776ab3-2acc-4925-98ac-2d8997b1bea3"


def log(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}")


def get_venv_python() -> str:
    """가상환경 Python 경로 반환 (없으면 시스템 Python)"""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    log("경고: .venv를 찾을 수 없습니다. 시스템 Python을 사용합니다.")
    return "python"


def upload_report_to_notebook(report_path: str) -> bool:
    """
    upload_source.py를 사용해 보고서를 NotebookLM에 업로드합니다.
    """
    log("NotebookLM에 보고서 업로드 중...")
    
    upload_script = Path(__file__).parent / "upload_source.py"
    python_exe = get_venv_python()
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        result = subprocess.run(
            [python_exe, str(upload_script), report_path, NOTEBOOK_URL],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=120  # 업로드 최대 2분
        )
        
        # 로그 출력
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                log(f"  [Upload] {line}")
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                if line.strip():
                    log(f"  [Upload 오류] {line}")
        
        if result.returncode == 0:
            log("업로드 성공!")
            return True
        else:
            log(f"업로드 실패 (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        log("업로드 타임아웃 (120초 초과)")
        return False
    except Exception as e:
        log(f"업로드 중 예외 발생: {e}")
        return False


def ask_notebooklm(question: str) -> str | None:
    """
    ask_question.py를 사용해 NotebookLM에 질의합니다.
    """
    log("NotebookLM에 영상 기획 스크립트 생성 요청 중...")
    
    python_exe = get_venv_python()
    ask_script = SCRIPTS_PATH / "ask_question.py"
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        result = subprocess.run(
            [python_exe, str(ask_script), "--question", question,
             "--notebook-url", NOTEBOOK_URL],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(SCRIPTS_PATH),
            timeout=180  # 질의 최대 3분
        )
        
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip()
            
            # ask_question.py 출력 형식:
            # ============================================================
            # Question: ...
            # ============================================================
            #
            # [실제 답변 내용]
            #
            # EXTREMELY IMPORTANT: ...  ← MCP 잡음, 제거 필요
            # ============================================================
            
            # 두 번째 구분선 이후 답변 본문 추출
            separator = "=" * 60
            parts = raw.split(separator)
            if len(parts) >= 3:
                # parts[0]: 로그/헤더, parts[1]: Question 줄, parts[2]: 답변 본문, ...
                answer_raw = parts[2].strip()
            else:
                answer_raw = raw
            
            # MCP 잡음 제거 (EXTREMELY IMPORTANT: 이후 모두 제거)
            if "EXTREMELY IMPORTANT:" in answer_raw:
                answer_raw = answer_raw.split("EXTREMELY IMPORTANT:")[0].strip()
            
            return answer_raw if answer_raw else None
        else:
            log(f"NotebookLM 질의 실패: {result.stderr[:200]}")
            return None
            
    except subprocess.TimeoutExpired:
        log("NotebookLM 질의 타임아웃 (180초 초과)")
        return None
    except Exception as e:
        log(f"NotebookLM 질의 중 예외: {e}")
        return None


def generate_fallback_script(report_content: str, timeframe: str, date_str: str) -> str:
    """
    NotebookLM 실패 시 Gemini로 폴백 기획안 생성
    """
    import json
    
    log("NotebookLM 실패 → Gemini 폴백으로 기획안 생성...")
    
    # config.json에서 API 키 로드
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        api_key = config.get("GOOGLE_API_KEY", "")
    except Exception:
        api_key = ""
    
    if not api_key:
        log("Gemini API 키 없음. 기본 템플릿 반환.")
        return f"# {date_str} {timeframe} 영상 기획안 (미생성)\n\n API 키 또는 NotebookLM 연결이 필요합니다."

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-2.0-flash-lite")
        
        if timeframe == "AM":
            opening = "안녕하세요, <우석에 닿기를> 투자 동향 분석입니다. 오늘은 당일 주요 기사들을 바탕으로 어제 시장에 대한 심층 분석 내용을 준비했습니다."
        else:
            opening = "안녕하세요, <우석에 닿기를> 투자 동향 분석입니다. 지금부터 오늘 당일 시장 장 흐름과 주요 이슈에 대해 핵심만 정리해 드립니다."

        analysis_prompt = f"""
당신은 <우석에 닿기를> 투자 동향 분석의 전문 영상 프로듀서입니다.
제공된 투자 보고서를 바탕으로 유튜브에 업로드할 '5분 분량의 영상 기획안'을 작성해주세요.

[보고서 내용]
{report_content}

[작성 지침]
1. 오프닝: 반드시 "{opening}"로 시작할 것.
2. 성격: 핵심 포인트 3가지를 깊이 있게 분석하여 정확히 5분 내외 분량으로 구성할 것.
3. 스토리보드: 각 포인트마다 [시각 가이드]를 포함하여 화면 연출 지침을 명시할 것.
4. 어조: 전문적이고 신뢰감 있는 뉴스 브리핑 스타일.
"""
        
        response = model.generate_content(analysis_prompt)
        return response.text
        
    except Exception as e:
        log(f"Gemini 폴백 실패: {e}")
        return f"# {date_str} {timeframe} 영상 기획안\n\n기획안 생성 중 오류 발생: {e}"


def create_date_instruction_file(date_str: str) -> str:
    """날짜 인식을 위한 임시 지침 파일 생성"""
    temp_dir = Path(__file__).parent / "tmp"
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"date_instruction_{date_str}.md"
    
    content = f"""# NotebookLM Podcast Instruction
오늘의 날짜는 {date_str}입니다. 
오디오 오버뷰(팟캐스트)를 제작할 때, 대화 초반에 반드시 오늘의 날짜({date_str})를 언급하며 시작해 주세요.
예시: "안녕하세요! 오늘 2026년 2월 27일 시장 핵심 정보를 전해드리는 오디오 오버뷰입니다."
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return str(file_path)




def run_agent_s(timeframe: str) -> bool:
    """
    Agent S 메인 실행 함수 (Video Content Producer 버전)
    """
    log(f"=== Agent S 시작 (Video Content Producer) [{timeframe}] ===")
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. 보고서 파일 확인
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    full_date = now.strftime("%Y년 %m월 %d일")
    report_file = REPORTS_DIR / f"{date_str}_{timeframe}_분석보고서.md"
    
    if not report_file.exists():
        log(f"보고서 파일 없음: {report_file}")
        return False
    
    log(f"보고서 확인: {report_file}")
    
    with open(report_file, "r", encoding="utf-8") as f:
        report_content = f.read()
    
    # 2. 날짜 지침 및 보고서 업로드
    # (1) 날짜 지침 업로드
    instr_path = create_date_instruction_file(full_date)
    upload_report_to_notebook(instr_path)
    
    # (2) 보고서 업로드
    upload_success = upload_report_to_notebook(str(report_file))
    
    if upload_success:
        log("NotebookLM 소스 처리 대기 중 (15초)...")
        time.sleep(15)
    
    # 3. NotebookLM에 영상 기획 스크립트 생성 질의
    if timeframe == "AM":
        opening = "안녕하세요, <우석에 닿기를> 투자 동향 분석입니다. 오늘은 당일 주요 기사들을 바탕으로 어제 시장에 대한 심층 분석 내용을 준비했습니다."
        prompt_goal = "핵심 포인트 3가지를 중심으로 5분 분량의 영상 스크립트와 스토리보드 가이드를 작성해줘."
    else:
        opening = "안녕하세요, <우석에 닿기를> 투자 동향 분석입니다. 지금부터 오늘 당일 시장 장 흐름과 주요 이슈에 대해 핵심만 정리해 드립니다."
        prompt_goal = "핵심 포인트 3가지를 중심으로 5분 분량의 영상 스크립트와 스토리보드 가이드를 작성해줘."
    
    question = f"""
오늘 날짜({full_date})를 명시하고, 다음 지침에 따라 5분 분량의 영상 기획안을 작성해줘.

1. 오프닝: 반드시 "{opening}"로 시작할 것.
2. 구조: 정확히 5분 내외 분량으로 '핵심 포인트 3가지'를 선정하여 깊이 있게 다룰 것.
3. 시각 자료: 각 포인트마다 차트, 데이터 카드, 인포그래픽 등 적합한 시각 자료 삽입 구간을 [시각 가이드] 형태로 정의할 것.
4. 형식: 진행자 대본과 화면 연출 지침이 포함된 스토리보드 형식으로 작성해줘.

위 지침을 바탕으로 다음 보고서를 분석하여 기획해줘.
"""
    
    script_output = ask_notebooklm(question)
    
    # 4. 실패 시 폴백
    if not script_output:
        log("NotebookLM 응답 없음 → Gemini 폴백 사용")
        script_output = generate_fallback_script(report_content, timeframe, date_str)
        output_filename = f"{date_str}_{timeframe}_영상기획_fallback.md"
    else:
        output_filename = f"{date_str}_{timeframe}_영상기획.md"
    
    # 5. 결과 저장
    output_file = SCRIPTS_DIR / output_filename
    with open(output_file, "w", encoding="utf-8") as f:
        header = f"# {date_str} {timeframe} 영상 기획 스크립트\n\n"
        header += f"> 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        header += "---\n\n"
        f.write(header + script_output)
    
    log(f"영상 기획안 저장 완료: {output_file}")
    
    # 6. 생성된 영상 기획 스크립트를 NotebookLM에 업로드
    log("생성된 영상 기획 스크립트를 NotebookLM에 추가 업로드 중...")
    upload_success2 = upload_report_to_notebook(str(output_file))
    if upload_success2:
        log("스크립트 업로드 완료.")
    
    log("=== Agent S 완료 ===")
    return True


if __name__ == "__main__":
    mode = sys.argv[1].upper() if len(sys.argv) > 1 else "AM"
    if mode not in ("AM", "PM"):
        print(f"사용법: python agent_s.py [AM|PM]")
        sys.exit(1)
    
    success = run_agent_s(mode)
    sys.exit(0 if success else 1)
