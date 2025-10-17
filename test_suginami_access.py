#!/usr/bin/env python3
"""
杉並区施設予約システムへのアクセステスト
様々なアプローチを試して、GitHub Actions環境で何が動くかを確認
"""

import os
import sys
import time
from datetime import datetime

def test_basic_info():
    """基本情報を表示"""
    print("=" * 60)
    print("基本環境情報")
    print("=" * 60)
    print(f"実行環境: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else 'ローカル'}")
    print(f"Python: {sys.version}")
    print(f"実行時刻: {datetime.now().isoformat()}")
    print()

def test_requests():
    """requests + BeautifulSoup でアクセステスト"""
    print("=" * 60)
    print("テスト 1: requests + BeautifulSoup")
    print("=" * 60)
    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        print(f"アクセス中: {url}")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        elapsed = time.time() - start_time

        print(f"✓ ステータスコード: {response.status_code}")
        print(f"✓ 応答時間: {elapsed:.2f}秒")
        print(f"✓ コンテンツサイズ: {len(response.content)} bytes")

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title')
        print(f"✓ ページタイトル: {title.text if title else 'なし'}")

        # Vueアプリの<div id="app">を探す
        app_div = soup.find('div', {'id': 'app'})
        print(f"✓ #app div: {'存在する' if app_div else '存在しない'}")

        # 集会施設ボタンを探す（静的HTMLには存在しないはず）
        buttons = soup.find_all('button')
        print(f"✓ button要素数: {len(buttons)}")

        facility_button = [b for b in buttons if '集会施設' in b.get_text()]
        print(f"✓ '集会施設'ボタン: {'見つかった' if facility_button else '見つからない（Vue.jsで動的生成される）'}")

        print("✅ requests でのアクセス成功（ただしVueコンテンツは取得不可）\n")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False

def test_playwright_basic():
    """Playwright で基本アクセステスト"""
    print("=" * 60)
    print("テスト 2: Playwright 基本アクセス")
    print("=" * 60)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            print("ブラウザ起動中...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            url = "https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home"
            print(f"アクセス中: {url}")
            start_time = time.time()

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            elapsed = time.time() - start_time

            print(f"✓ ページ読み込み完了: {elapsed:.2f}秒")
            print(f"✓ ページタイトル: {page.title()}")
            print(f"✓ URL: {page.url}")

            browser.close()
            print("✅ Playwright 基本アクセス成功\n")
            return True

    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False

def test_playwright_vue_wait():
    """Playwright で Vue アプリの初期化を待つテスト"""
    print("=" * 60)
    print("テスト 3: Playwright + Vue 初期化待機")
    print("=" * 60)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            print("ブラウザ起動中...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="ja-JP",
                timezone_id="Asia/Tokyo"
            )
            page = context.new_page()

            url = "https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home"
            print(f"アクセス中: {url}")
            start_time = time.time()

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"✓ DOM読み込み完了: {time.time() - start_time:.2f}秒")

            # Vueアプリの初期化を待つ
            print("Vueアプリの初期化を待機中...")
            vue_start = time.time()
            try:
                page.wait_for_selector("button:text('集会施設')", timeout=30000, state="visible")
                vue_elapsed = time.time() - vue_start
                print(f"✓ Vue初期化完了: {vue_elapsed:.2f}秒")
                print(f"✓ 総時間: {time.time() - start_time:.2f}秒")

                # ボタンの数を数える
                buttons_count = page.evaluate("document.querySelectorAll('button').length")
                print(f"✓ button要素数: {buttons_count}")

                # 集会施設ボタンが見えるか確認
                is_visible = page.is_visible("button:text('集会施設')")
                print(f"✓ '集会施設'ボタン表示: {is_visible}")

                browser.close()
                print("✅ Playwright + Vue 初期化待機 成功\n")
                return True

            except Exception as e:
                print(f"⚠ Vue初期化タイムアウト: {e}")
                print(f"  30秒以内に'集会施設'ボタンが表示されませんでした")
                browser.close()
                print("❌ Vue初期化待機 失敗\n")
                return False

    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False

def test_playwright_click():
    """Playwright でボタンクリックまでテスト"""
    print("=" * 60)
    print("テスト 4: Playwright + ボタンクリック")
    print("=" * 60)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            print("ブラウザ起動中...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="ja-JP",
                timezone_id="Asia/Tokyo"
            )
            page = context.new_page()

            url = "https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home"
            print(f"アクセス中: {url}")

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("✓ ページ読み込み完了")

            # Vueアプリの初期化を待つ
            print("Vueアプリの初期化を待機中...")
            page.wait_for_selector("button:text('集会施設')", timeout=30000, state="visible")
            print("✓ Vue初期化完了")

            # 集会施設ボタンをクリック
            print("'集会施設'ボタンをクリック中...")
            page.click("button:text('集会施設')")

            # 施設選択画面が表示されるまで待つ
            print("施設選択画面の表示を待機中...")
            page.wait_for_selector("label:has-text('西荻地域区民センター・勤福会館')", timeout=15000, state="visible")
            print("✓ 施設選択画面表示完了")

            # 現在のURL
            print(f"✓ 現在のURL: {page.url}")

            # ページタイトル
            print(f"✓ ページタイトル: {page.title()}")

            browser.close()
            print("✅ Playwright + ボタンクリック 成功\n")
            return True

    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False

def main():
    """全テストを実行"""
    test_basic_info()

    results = {}

    # テスト1: requests
    results['requests'] = test_requests()

    # テスト2: Playwright基本
    results['playwright_basic'] = test_playwright_basic()

    # テスト3: Playwright + Vue待機
    results['playwright_vue'] = test_playwright_vue_wait()

    # テスト4: Playwright + クリック
    results['playwright_click'] = test_playwright_click()

    # サマリー
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name:25} : {status}")

    print()
    success_count = sum(results.values())
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")

    # 全て成功したら0、失敗があれば1を返す
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
