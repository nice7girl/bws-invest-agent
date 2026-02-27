#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 업로드 다이얼로그 구조 분석용 스크립트
"""
import sys
import os
import time
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SKILLS_DIR = Path(__file__).parent / "antigravity-awesome-skills" / "skills" / "notebooklm" / "scripts"
sys.path.insert(0, str(SKILLS_DIR))

from patchright.sync_api import sync_playwright
from browser_utils import BrowserFactory

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/2f776ab3-2acc-4925-98ac-2d8997b1bea3"

def js_click(page, locator):
    element = locator.element_handle(timeout=5000)
    if element:
        page.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))", element)
        return True
    return False

with sync_playwright() as p:
    context = BrowserFactory.launch_persistent_context(p, headless=True)
    page = context.new_page()
    
    # 뷰포트를 크게 설정
    page.set_viewport_size({"width": 1280, "height": 900})
    
    print("노트북 페이지 로딩...")
    page.goto(NOTEBOOK_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(7000)
    
    print("소스 추가 버튼 클릭...")
    btn = page.locator('button[aria-label="업로드 소스 대화상자 열기"]')
    js_click(page, btn.first)
    page.wait_for_timeout(3000)
    
    # 다이얼로그 스크린샷 (더 큰 뷰포트)
    page.screenshot(path="dialog_full.png", full_page=False)
    print("전체 스크린샷: dialog_full.png")
    
    # 모든 input 요소 찾기 (hidden 포함)
    inputs = page.evaluate("""
        () => {
            const all = document.querySelectorAll('input');
            return Array.from(all).map(el => ({
                type: el.type,
                name: el.name,
                accept: el.accept,
                class: el.className,
                id: el.id,
                hidden: el.hidden,
                display: window.getComputedStyle(el).display,
                visibility: window.getComputedStyle(el).visibility
            }));
        }
    """)
    print(f"\n=== 모든 input 요소 ({len(inputs)}개) ===")
    for inp in inputs:
        print(f"  type={inp['type']}, accept={inp['accept']}, class={inp['class'][:50]}, display={inp['display']}")
    
    # 다이얼로그 내 모든 클릭 가능 요소
    clickables = page.evaluate("""
        () => {
            const all = document.querySelectorAll('button, [role="button"], mat-dialog-container *');
            return Array.from(all).slice(0, 30).map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().slice(0, 50),
                class: el.className.slice(0, 60)
            }));
        }
    """)
    print(f"\n=== 다이얼로그 내 요소 (처음 30개) ===")
    for el in clickables:
        print(f"  <{el['tag']}> '{el['text'][:40]}' class='{el['class'][:40]}'")
    
    # 드롭존 HTML 추출
    dropzone_html = page.evaluate("""
        () => {
            const dz = document.querySelector('.drop-zone') || 
                       document.querySelector('[class*="drop"]') ||
                       document.querySelector('mat-dialog-container');
            return dz ? dz.outerHTML.slice(0, 2000) : 'NOT FOUND';
        }
    """)
    print(f"\n=== 드롭존 HTML ===")
    print(dropzone_html)
    
    context.close()
    print("\n분석 완료!")
