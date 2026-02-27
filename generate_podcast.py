#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 오디오 오버뷰(팟캐스트) 생성 자동화 스크립트
"""

import os
import sys
import time
from pathlib import Path

# Windows 콘솔 인코딩 문제 방지
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# skills/notebooklm/scripts 경로를 sys.path에 추가
SKILLS_DIR = Path(__file__).parent / "antigravity-awesome-skills" / "skills" / "notebooklm" / "scripts"
sys.path.insert(0, str(SKILLS_DIR))

from patchright.sync_api import sync_playwright
from browser_utils import BrowserFactory
from auth_manager import AuthManager

# 기본 노트북 URL
DEFAULT_URL = "https://notebooklm.google.com/notebook/2f776ab3-2acc-4925-98ac-2d8997b1bea3"

def js_click(page, locator):
    element = locator.element_handle(timeout=5000)
    if element:
        page.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))", element)
        return True
    return False

def trigger_podcast(notebook_url: str) -> bool:
    print(f"[팟캐스트 생성 시작] 노트북: {notebook_url}")

    auth = AuthManager()
    if not auth.is_authenticated():
        print("[오류] NotebookLM 인증이 필요합니다.")
        return False

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=True)
        page = context.new_page()

        try:
            # 1. 노트북 페이지 이동
            print("[1/3] 노트북 로딩 중...")
            page.goto(notebook_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000) # 충분한 로딩 시간

            # 2. '노트북 가이드' 또는 '오디오 오버뷰' 영역 열기
            print("[2/4] 노트북 가이드 패널 확인 중...")
            
            # '노트북 가이드' 버튼 클릭 (없으면 이미 열려있을 수 있음)
            guide_selectors = ["text='노트북 가이드'", "text='Notebook Guide'", "[aria-label='Notebook Guide']"]
            for sel in guide_selectors:
                btn = page.locator(sel)
                if btn.count() > 0:
                    js_click(page, btn.first)
                    page.wait_for_timeout(2000)
                    break
            
            # --- 추가: 브리핑 문서 및 학습 가이드 (세로형 인포그래픽 대용) 생성 ---
            print("[3/4] '브리핑 문서/학습 가이드' 생성 시도 중...")
            content_selectors = [
                "text='브리핑 문서'", "text='Briefing Doc'", 
                "text='학습 가이드'", "text='Study Guide'"
            ]
            for sel in content_selectors:
                btn = page.locator(sel)
                if btn.count() > 0:
                    js_click(page, btn.first)
                    print(f"[OK] {sel} 생성 요청 완료.")
                    page.wait_for_timeout(3000)
                    # 하나만 생성하는 것이 아니라 여러 개를 생성하고 싶다면 break를 제거할 수 있으나, 
                    # 일단 '학습 가이드'와 '브리핑 문서'를 모두 시도하도록 함
            

            # --- 팟캐스트 생성 ---
            # --- 동영상 개요 (Video Overview) 생성 트리거 ---
            print("[4/4] '동영상 개요' 버튼 찾는 중...")
            
            video_selectors = [
                  "text='동영상 개요'",
                  "text='Video Overview'",
                  ".studio-card:has-text('동영상 개요')",
                  "mat-card:has-text('동영상 개요')"
            ]
            
            video_btn = None
            for selector in video_selectors:
                btn = page.locator(selector)
                if btn.count() > 0:
                    video_btn = btn.first
                    break
            
            if video_btn:
                js_click(page, video_btn)
                print("[OK] '동영상 개요' 클릭 완료! 동영상 기획 생성이 진행됩니다.")
                page.wait_for_timeout(5000)
                page.screenshot(path="video_overview_started.png")
                return True
            else:
                print("[경고] '동영상 개요' 버튼을 찾지 못했습니다. 구조가 변경되었을 수 있습니다.")
                page.screenshot(path="video_debug.png")
                return False

        except Exception as e:
            print(f"[오류] 팟캐스트 트리거 실패: {e}")
            return False
        finally:
            context.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    success = trigger_podcast(url)
    sys.exit(0 if success else 1)
