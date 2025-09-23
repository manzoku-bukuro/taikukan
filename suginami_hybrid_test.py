#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import random

def create_stealth_options(disable_js=False):
    """bot検知回避のためのChromeオプション設定"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=VizDisplayCompositor")

    # bot検知回避
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    if disable_js:
        print("🚫 JavaScript無効モード")
        options.add_argument("--disable-javascript")
        options.page_load_strategy = 'none'
    else:
        print("✅ JavaScript有効モード")
        options.page_load_strategy = 'eager'

    # 共通の最適化オプション
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--no-first-run")
    options.add_argument("--mute-audio")

    return options

def test_suginami_access(disable_js=False):
    """杉並区サイトアクセステスト"""
    options = create_stealth_options(disable_js)

    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        max_retries = 2
        timeout_values = [30, 60]

        for attempt in range(max_retries):
            try:
                wait_time = random.uniform(1, 3)
                print(f"🔄 試行 {attempt + 1}/{max_retries} (待機: {wait_time:.1f}秒)")
                time.sleep(wait_time)

                driver.set_page_load_timeout(timeout_values[attempt])

                print(f"🌐 アクセス中...")
                driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")

                if disable_js:
                    # JavaScript無効時は短時間待機のみ
                    time.sleep(2)
                else:
                    # JavaScript有効時は状態確認
                    try:
                        ready_state = driver.execute_script("return document.readyState")
                        print(f"📄 Document状態: {ready_state}")
                    except:
                        pass

                # 基本情報取得
                title = driver.title
                current_url = driver.current_url
                source_length = len(driver.page_source)

                print(f"✅ アクセス成功!")
                print(f"📄 タイトル: {title}")
                print(f"📍 現在のURL: {current_url}")
                print(f"📏 ページサイズ: {source_length}文字")

                return True

            except Exception as e:
                print(f"❌ 試行 {attempt + 1} 失敗: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(2 + attempt)

        return False

    except Exception as e:
        print(f"❌ ドライバー初期化エラー: {e}")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

def hybrid_test():
    """ハイブリッド戦略でテスト"""
    print("🚀 杉並区サイト ハイブリッドテスト開始")
    print(f"🔍 GitHub Actions環境: {os.getenv('GITHUB_ACTIONS', 'False')}")

    # 戦略1: JavaScript有効でトライ
    print("\n🧪 戦略1: JavaScript有効")
    if test_suginami_access(disable_js=False):
        print("🎯 JavaScript有効で成功!")
        return True

    # 戦略2: JavaScript無効でトライ
    print("\n🧪 戦略2: JavaScript無効")
    if test_suginami_access(disable_js=True):
        print("🎯 JavaScript無効で成功!")
        return True

    print("❌ 両戦略とも失敗")
    return False

if __name__ == "__main__":
    result = hybrid_test()
    print(f"\n🎯 最終結果: {'成功' if result else '失敗'}")