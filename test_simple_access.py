#!/usr/bin/env python3
"""杉並区サイトへの簡単なアクセステスト"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

def simple_access_test():
    """最小限の設定でアクセステスト"""
    print("🚀 簡単アクセステスト開始")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # 成功したbot回避設定
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 超軽量化
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-images")
    options.page_load_strategy = 'none'

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)

        print("🌐 杉並区サイトにアクセス中...")
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
        time.sleep(3)

        title = driver.title
        url = driver.current_url
        source_length = len(driver.page_source)

        print(f"✅ アクセス成功!")
        print(f"📄 タイトル: {title}")
        print(f"📍 URL: {url}")
        print(f"📏 ページサイズ: {source_length}文字")

        # HTMLソースの一部を確認
        source_snippet = driver.page_source[:500]
        print(f"📄 ソース先頭500文字:")
        print(source_snippet)

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    result = simple_access_test()
    print(f"\n🎯 結果: {'成功' if result else '失敗'}")