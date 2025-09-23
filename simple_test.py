#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import random

def simple_test():
    print("🚀 段階的テスト開始")
    print(f"🔍 GitHub Actions環境: {os.getenv('GITHUB_ACTIONS', 'False')}")

    # 最小限のChrome設定（GitHub Actions対応 + bot検知回避）
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")

    # bot検知回避のための設定
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # 高速化のため画像読み込み無効
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 追加のプライバシー設定
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")

    try:
        driver = webdriver.Chrome(options=options)

        # bot検知回避: WebDriverプロパティを隠す
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("✅ ChromeDriver初期化成功")

        try:
            # ステップ1: データURLテスト
            print("🔧 ステップ1: データURLテスト")
            driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
            print("✅ データURL成功")

            # ステップ2: HTTPSサイトテスト（軽量）
            print("🔧 ステップ2: HTTPSサイトテスト")
            driver.get("https://httpbin.org/html")
            print("✅ HTTPSサイト成功")

            # ステップ3: Googleテスト
            print("🔧 ステップ3: Googleテスト")
            driver.set_page_load_timeout(30)
            driver.get("https://www.google.com")
            print("✅ Google成功")

            # ステップ4: 杉並区サイトテスト（強化版）
            print("🔧 ステップ4: 杉並区サイトテスト")

            success = False
            max_retries = 3
            timeout_values = [30, 60, 120]  # 段階的にタイムアウトを増やす

            for attempt in range(max_retries):
                try:
                    # ランダム待機でbot検知を回避
                    wait_time = random.uniform(2, 5)
                    print(f"🔄 試行 {attempt + 1}/{max_retries} (待機: {wait_time:.1f}秒)")
                    time.sleep(wait_time)

                    # タイムアウト設定
                    driver.set_page_load_timeout(timeout_values[attempt])

                    # アクセス前にリファラー設定
                    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    })

                    driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
                    print("✅ 杉並区サイト成功")

                    # 基本情報取得
                    title = driver.title
                    print(f"📄 タイトル: {title}")

                    # ページソース先頭100文字
                    source = driver.page_source[:100]
                    print(f"📄 ソース先頭: {source}")

                    success = True
                    break

                except Exception as e:
                    print(f"❌ 試行 {attempt + 1} 失敗: {e}")
                    if attempt < max_retries - 1:
                        print(f"🔄 {3 + attempt * 2}秒後に再試行...")
                        time.sleep(3 + attempt * 2)  # リトライ間隔を徐々に延ばす

            if not success:
                print(f"❌ 杉並区サイト {max_retries}回試行後も失敗")
                return False

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            return False
        finally:
            driver.quit()
            print("🔒 ChromeDriver終了")

        return True

    except Exception as e:
        print(f"❌ ChromeDriver初期化エラー: {e}")
        return False

if __name__ == "__main__":
    result = simple_test()
    print(f"🎯 テスト結果: {'成功' if result else '失敗'}")