#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWS_Invest 파이프라인 오케스트레이터
Agent B -> Agent W -> Agent S 순서로 실행

실행:
    python main.py AM    # 오전 파이프라인
    python main.py PM    # 오후 파이프라인
"""

import sys
import io
import json
import os
from datetime import datetime
import agent_b
import agent_w
import agent_s

# Removed manual sys.stdout/stderr wrapping


def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)
            for key, value in config.items():
                os.environ[key] = value
    else:
        print("Warning: config.json not found. Using environment variables.")


import requests

def check_server_completed(timeframe: str) -> bool:
    """AWS 서버에서 당일 보고서가 이미 생성/발송되었는지 확인"""
    today_str = datetime.now().strftime("%Y%m%d")
    report_name = f"{today_str}_{timeframe}_분석보고서.md"
    # Bitnami 서버의 공개 디렉토리에 접근 (deploy.sh에서 심볼릭 링크 설정 필요)
    server_ip = os.getenv("SERVER_IP", "YOUR_SERVER_IP")
    url = f"http://{server_ip}/bws_reports/{report_name}"
    
    try:
        # 헤더만 요청하여 파일 존재 여부만 빠르게 확인
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            print(f"[Check] 서버에서 이미 [{timeframe}] 보고서가 완료되었습니다. ({url})")
            return True
    except Exception as e:
        print(f"[Check] 서버 연결 실패: {e} (로컬 실행 모드로 전환)")
    
    return False


def run_pipeline(timeframe: str, skip_agent_s: bool = False, force: bool = False):
    print(f"\n{'='*50}")
    print(f"[START] BWS Invest Pipeline [{timeframe}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 로컬 실행 시 서버 완료 여부 체크 (중복 발송 방지)
    # --force 옵션이 있거나 timeframe이 PM일 때는 수동 실행일 수 있으므로 체크 생략 가능 (필요시 조정)
    if not force:
        if check_server_completed(timeframe):
            print(f">>> 서버(Priority 1)에서 이미 완료되었습니다. 로컬 실행을 중단합니다.")
            return

    # 1. Agent B: YouTube 분석 및 보고서 생성
    print("[Agent B] YouTube 분석 시작...")
    success = agent_b.run_agent_b(timeframe)
    if not success:
        print(f"[Agent B] {timeframe} 분석 실패 또는 새 영상 없음. 파이프라인 중단.")
        return

    # 2. Agent W: 텔레그램 전송
    print("\n[Agent W] 텔레그램 전송 시작...")
    agent_w.run_agent_w()

    # 3. Agent S: NotebookLM 업로드 및 영상 기획 생성
    if skip_agent_s:
        print("\n[Agent S] --skip-agent-s 옵션으로 건너뜁니다.")
    else:
        print("\n[Agent S] NotebookLM 업로드 및 영상 기획 시작...")
        try:
            agent_s.run_agent_s(timeframe)
        except Exception as e:
            print(f"[Agent S] 실행 중 오류 발생: {e}")

    print(f"\n{'='*50}")
    print(f"[DONE] <우석에 닿기를> 투자 동향 분석 완료: [{timeframe}]")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    load_config()
    
    import argparse
    parser = argparse.ArgumentParser(description="BWS Invest Agent Pipeline")
    parser.add_argument("mode", nargs="?", default="AM", choices=["AM", "PM"],
                        help="실행 모드 (AM 또는 PM)")
    parser.add_argument("--skip-agent-s", action="store_true",
                        help="Agent S(NotebookLM) 건너뜀")
    parser.add_argument("--force", action="store_true",
                        help="서버 완료 여부와 관계없이 강제 실행")
    args = parser.parse_args()
    
    run_pipeline(args.mode, skip_agent_s=args.skip_agent_s, force=args.force)

