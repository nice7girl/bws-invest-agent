#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 자동 소스 업로드 스크립트
분석 보고서(.md)를 NotebookLM 노트북에 자동으로 소스로 추가합니다.

사용법:
    python upload_source.py                          # 최신 보고서 자동 감지
    python upload_source.py output/20260226_AM.md   # 특정 파일 업로드
"""

import os
import sys
import time
import json
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

# 업로드할 노트북 URL
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/2f776ab3-2acc-4925-98ac-2d8997b1bea3"


def js_click(page, locator):
    """
    오버레이에 가려진 버튼을 JavaScript dispatchEvent로 클릭합니다.
    Playwright의 일반 click()은 요소 위에 다른 요소가 있으면 실패합니다.
    """
    element = locator.element_handle(timeout=5000)
    if element:
        page.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))", element)
        return True
    return False


def upload_report(report_path: str, notebook_url: str = NOTEBOOK_URL) -> bool:
    """
    분석 보고서를 NotebookLM 노트북에 파일 소스로 업로드합니다.
    """
    # 절대경로로 변환
    report_path = os.path.abspath(report_path)

    if not os.path.exists(report_path):
        print(f"[오류] 파일을 찾을 수 없습니다: {report_path}")
        return False

    print(f"[업로드 시작]")
    print(f"  파일: {report_path}")
    print(f"  노트북: {notebook_url}")

    # 인증 상태 확인
    auth = AuthManager()
    if not auth.is_authenticated():
        print("[오류] NotebookLM 인증이 필요합니다.")
        print("  실행: .venv\\Scripts\\python.exe antigravity-awesome-skills\\skills\\notebooklm\\scripts\\auth_manager.py setup")
        return False

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=True)
        page = context.new_page()

        try:
            # 1. 노트북 페이지 이동
            print(f"\n[1/4] 노트북 페이지 로딩 중...")
            page.goto(notebook_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(7000)  # SPA 렌더링 충분히 대기

            # 로그인 확인
            if "accounts.google.com" in page.url:
                print("[오류] 로그인이 필요합니다. 인증을 다시 설정하세요.")
                return False

            print(f"  현재 URL: {page.url}")

            # 2. '소스 추가' 버튼 클릭 (오버레이 우회 위해 JS click 사용)
            print(f"\n[2/4] '소스 추가' 버튼 찾는 중...")

            # 소스 탭('출처')을 먼저 활성화 - 소스 패널이 숨겨져 있을 수 있음
            try:
                sources_tab = page.get_by_text("출처", exact=True)
                if sources_tab.count() > 0:
                    js_click(page, sources_tab.first)
                    page.wait_for_timeout(1500)
                    print("  소스 탭 활성화 완료")
            except Exception:
                pass

            add_source_clicked = False

            # 시도 1: aria-label 버튼을 JS click으로 클릭
            btn = page.locator('button[aria-label="업로드 소스 대화상자 열기"]')
            if btn.count() > 0:
                try:
                    if js_click(page, btn.first):
                        add_source_clicked = True
                        print("  [OK] aria-label 버튼 JS 클릭 성공")
                except Exception as e:
                    print(f"  aria-label JS 클릭 실패: {e}")

            # 시도 2: 소스 패널의 upload 아이콘 버튼 (소스가 이미 있는 노트북)
            if not add_source_clicked:
                upload_icon_btn = page.locator('button.upload-icon-button')
                if upload_icon_btn.count() > 0:
                    try:
                        if js_click(page, upload_icon_btn.first):
                            add_source_clicked = True
                            print("  [OK] upload-icon-button JS 클릭 성공")
                    except Exception as e:
                        print(f"  upload-icon-button 클릭 실패: {e}")

            # 시도 3: 텍스트 기반 버튼
            if not add_source_clicked:
                for text in ["소스 추가", "소스 업로드", "시작하려면 소스 추가"]:
                    el = page.get_by_text(text, exact=True)
                    if el.count() > 0:
                        try:
                            if js_click(page, el.first):
                                add_source_clicked = True
                                print(f"  [OK] 텍스트 '{text}'로 클릭 성공")
                                break
                        except Exception as e:
                            print(f"  '{text}' JS 클릭 실패: {e}")

            if not add_source_clicked:
                print("  [오류] 소스 추가 버튼을 찾을 수 없습니다.")
                page.screenshot(path="upload_error.png")
                print("  스크린샷 저장: upload_error.png")
                return False

            # 3. 다이얼로그에서 '파일 업로드' 클릭 -> 파일 선택
            print(f"\n[3/4] 업로드 다이얼로그 처리 중...")
            page.wait_for_timeout(3000)  # 다이얼로그 열리길 대기

            # 다이얼로그 상태 디버그 스크린샷
            page.screenshot(path="upload_dialog.png")
            print("  다이얼로그 스크린샷 저장: upload_dialog.png")

            # 방법 1: button[xapscottyuploadertrigger] - HTML 분석으로 확인된 정확한 셀렉터
            file_set = False
            try:
                upload_trigger = page.locator('button[xapscottyuploadertrigger]')
                count = upload_trigger.count()
                print(f"  xapscottyuploadertrigger 버튼 수: {count}")
                if count > 0:
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        upload_trigger.first.click(force=True)
                        print("  [OK] xapscottyuploadertrigger 버튼 force 클릭")
                    file_chooser = fc_info.value
                    file_chooser.set_files(report_path)
                    file_set = True
                    print(f"  [OK] 파일 선택 완료: {os.path.basename(report_path)}")
            except Exception as e:
                print(f"  xapscottyuploadertrigger 방식 실패: {e}")

            # 방법 2: class에 'upload-bu' 포함하는 버튼
            if not file_set:
                try:
                    upload_btn = page.locator('button[class*="upload-bu"]').first
                    if upload_btn.count() > 0:
                        with page.expect_file_chooser(timeout=10000) as fc_info:
                            upload_btn.click(force=True)
                            print("  [OK] upload-bu* 버튼 force 클릭")
                        file_chooser = fc_info.value
                        file_chooser.set_files(report_path)
                        file_set = True
                        print(f"  [OK] 파일 선택 완료: {os.path.basename(report_path)}")
                except Exception as e:
                    print(f"  upload-bu* 방식 실패: {e}")

            # 방법 3: '파일 업로드' 텍스트 버튼 force 클릭
            if not file_set:
                try:
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        page.get_by_text("파일 업로드", exact=True).first.click(force=True)
                        print("  [OK] '파일 업로드' force 클릭")
                    file_chooser = fc_info.value
                    file_chooser.set_files(report_path)
                    file_set = True
                    print(f"  [OK] 파일 선택 완료: {os.path.basename(report_path)}")
                except Exception as e:
                    print(f"  텍스트 방식 실패: {e}")

            if not file_set:
                print("  [오류] 파일 설정 방법 모두 실패")
                page.screenshot(path="upload_error.png")
                print("  스크린샷 저장: upload_error.png")
                return False

            # 4. 업로드 완료 대기
            print(f"\n[4/4] 업로드 처리 중 (최대 30초 대기)...")
            page.wait_for_timeout(20000)

            # 성공 스크린샷
            page.screenshot(path="upload_success.png")
            print("  스크린샷 저장: upload_success.png")
            print("  [OK] 업로드 완료!")

            return True

        except Exception as e:
            print(f"\n[오류] 업로드 실패: {e}")
            try:
                page.screenshot(path="upload_error.png")
                print("  스크린샷 저장: upload_error.png")
            except:
                pass
            return False

        finally:
            context.close()


def get_latest_report() -> str:
    """최신 보고서 경로 자동 감지"""
    output_dir = Path(__file__).parent / "output" / "reports"
    reports = sorted(output_dir.glob("*_분석보고서.md"), reverse=True)
    return str(reports[0]) if reports else ""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
        notebook_url = sys.argv[2] if len(sys.argv) > 2 else NOTEBOOK_URL
    else:
        report_path = get_latest_report()
        notebook_url = NOTEBOOK_URL

        if not report_path:
            print("[오류] 업로드할 보고서를 찾을 수 없습니다.")
            print("  사용법: python upload_source.py <파일경로>")
            sys.exit(1)

        print(f"[자동 감지] 최신 보고서: {report_path}")

    success = upload_report(report_path, notebook_url)

    if success:
        print("\n[완료] NotebookLM 업로드 성공!")
        print(f"  노트북 확인: {notebook_url}")
    else:
        print("\n[실패] 업로드 실패 - upload_error.png 확인하세요.")
        sys.exit(1)
