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


def run_pipeline(timeframe: str, skip_agent_s: bool = False):
    print(f"\n{'='*50}")
    print(f"[START] BWS Invest Pipeline [{timeframe}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 1. Agent B: YouTube 분석 및 보고서 생성
    print("[Agent B] YouTube 분석 시작...")
    success = agent_b.run_agent_b(timeframe)
    if not success:
        print(f"[Agent B] {timeframe} 분석 실패 또는 새 영상 없음. 파이프라인 중단.")
        return

    # 2. Agent W: 텔레그램 전송
    print("\n[Agent W] 텔레그램 전송 시작...")
    agent_w.run_agent_w()

    # 3. Agent S: NotebookLM 업로드 및 영상 기획 생성 (로컬 전용)
    if skip_agent_s:
        print("\n[Agent S] --skip-agent-s 옵션으로 건너뜁니다 (서버 실행 중)")
    else:
        print("\n[Agent S] NotebookLM 업로드 및 영상 기획 시작...")
        agent_s.run_agent_s(timeframe)

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
                        help="Agent S(NotebookLM) 건너뜀 - 서버 실행 시 사용")
    args = parser.parse_args()
    
    run_pipeline(args.mode, skip_agent_s=args.skip_agent_s)

