#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 생성 콘텐츠(동영상 개요, 학습 가이드) 로컬 다운로드 스크립트
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

# 기본 노트북 URL 및 저장 경로
DEFAULT_URL = "https://notebooklm.google.com/notebook/2f776ab3-2acc-4925-98ac-2d8997b1bea3"
OUT_DIR = Path(__file__).parent / "output" / "notebook_content"

def js_click(page, locator):
    element = locator.element_handle(timeout=5000)
    if element:
        page.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))", element)
        return True
    return False

def download_content(notebook_url: str) -> bool:
    print(f"[다운로드 프로세스 시작] 노트북: {notebook_url}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    auth = AuthManager()
    if not auth.is_authenticated():
        print("[오류] NotebookLM 인증이 필요합니다.")
        return False

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=True)
        page = context.new_page()

        try:
            print("[1/3] 노트북 로딩 중...")
            page.goto(notebook_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)

            # 노트북 가이드(스튜디오) 열기
            print("[2/3] 스튜디오(Studio) 탭 및 노트북 가이드 확인 중...")
            
            # 1. '스튜디오' 또는 'Studio' 탭 클릭
            studio_selectors = ["text='스튜디오'", "text='Studio'"]
            for sel in studio_selectors:
                tab = page.locator(sel)
                if tab.count() > 0:
                    js_click(page, tab.first)
                    print(f"로그: {sel} 탭 클릭함.")
                    page.wait_for_timeout(3000)
                  # 노트북 가이드를 클릭하는 대신 '스튜디오' 탭에서 직접 요소 클릭 시도
            print("[2/3] 스튜디오 탭 내 요소 확인 중...")
            
            # 1. 팟캐스트(오디오 오버뷰) 클릭
            audio_box = page.locator("text='AI 오디오 오버뷰'")
            if audio_box.count() > 0:
                print("로그: 'AI 오디오 오버뷰' 클릭")
                js_click(page, audio_box.first)
                page.wait_for_timeout(3000)
                
                # 생성 중인지 확인 및 대기
                print("[팟캐스트] 생성 완료 대기 중 (최대 10분)...")
                download_btn = None
                for _ in range(60): # 600초
                    # 생성 중 메시지가 사라지고 다운로드 버튼이 생기는지 확인
                    is_generating = page.locator("text='생성 중'").count() > 0 or \
                                    page.locator("text='Generating'").count() > 0
                    
                    download_btn_selectors = [
                        "button:has-text('다운로드')", 
                        "button:has-text('Download')",
                        "[aria-label='Download']",
                        "[aria-label='다운로드']"
                    ]
                    
                    for sel in download_btn_selectors:
                        btn = page.locator(sel)
                        if btn.count() > 0:
                            download_btn = btn.first
                            break
                    
                    if download_btn:
                        break
                    
                    if not is_generating and _ > 5: # 어느 정도 시간이 지났는데 생성 중도 아니고 버튼도 없으면 중단
                         break
                         
                    page.wait_for_timeout(10000)
                    print(f"  대기 중... ({_ * 10}s)")

                if download_btn:
                    print("[팟캐스트] 다운로드 시작...")
                    try:
                        with page.expect_download(timeout=30000) as download_info:
                            js_click(page, download_btn)
                        download = download_info.value
                        save_path = OUT_DIR / download.suggested_filename
                        download.save_as(save_path)
                        print(f"[OK] 팟캐스트 저장 완료: {save_path}")
                    except Exception as de:
                        print(f"[경고] 팟캐스트 다운로드 중 오류: {de}")
                else:
                    print("[경고] 팟캐스트 다운로드 버튼을 찾지 못했습니다. 생성이 지연되고 있거나 구조가 다를 수 있습니다.")
                    page.screenshot(path="audio_view_debug.png")

            # 2. 문서 항목들 클릭 및 내용 추출 (동영상 개요, 학습 가이드 등)
            doc_types = ["동영상 개요", "학습 가이드", "브리핑 문서", "인포그래픽", "보고서"]
            for dtype in doc_types:
                # 텍스트로 정확히 일치하는 요소를 찾기 위해 filter 사용
                doc_box = page.locator(".studio-card, mat-card, .card").filter(has_text=dtype).first
                if doc_box.count() == 0:
                    doc_box = page.locator(f"text='{dtype}'").first

                if doc_box.count() > 0:
                    print(f"로그: '{dtype}' 클릭 시도")
                    js_click(page, doc_box)
                    page.wait_for_timeout(4000)
                    
                    # 내용 추출
                    # 여러 선택자 시도
                    content_selectors = [".document-content", "[role='main']", "mat-dialog-container", ".sidenav-content"]
                    content_text = ""
                    for csel in content_selectors:
                        loc = page.locator(csel)
                        if loc.count() > 0:
                            content_text = loc.first.text_content().strip()
                            if len(content_text) > 50:
                                break
                    
                    if content_text and len(content_text) > 50:
                        doc_path = OUT_DIR / f"{dtype}_{int(time.time())}.md"
                        with open(doc_path, "w", encoding="utf-8") as f:
                            f.write(f"# {dtype}\n\n{content_text}")
                        print(f"[OK] {dtype} 저장 완료: {doc_path}")
                    else:
                        print(f"[경고] '{dtype}' 내용을 추출하지 못했습니다.")
                    
                    # 닫기 버튼: CSS 선택자 대신 text나 aria-label 위주로
                    close_btn_selectors = ["[aria-label='Close']", "[aria-label='닫기']", "text='닫기'", "button:has-text('닫기')"]
                    for cbsel in close_btn_selectors:
                        cb = page.locator(cbsel)
                        if cb.count() > 0:
                            js_click(page, cb.first)
                            page.wait_for_timeout(1500)
                            break

            return True

        except Exception as e:
            print(f"[오류] 컨텐츠 다운로드 실패: {e}")
            page.screenshot(path="download_error.png")
            return False
        finally:
            context.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    success = download_content(url)
    sys.exit(0 if success else 1)
