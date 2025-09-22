#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os

def simple_test():
    print("🚀 段階的テスト開始")

    # 最小限のChrome設定
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    try:
        driver = webdriver.Chrome(options=options)
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

            # ステップ4: 杉並区サイトテスト（段階的）
            print("🔧 ステップ4: 杉並区サイトテスト")
            driver.set_page_load_timeout(10)  # 短いタイムアウト

            try:
                driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
                print("✅ 杉並区サイト成功")

                # 基本情報取得
                title = driver.title
                print(f"📄 タイトル: {title}")

                # ページソース先頭100文字
                source = driver.page_source[:100]
                print(f"📄 ソース先頭: {source}")

            except Exception as e:
                print(f"❌ 杉並区サイトエラー: {e}")

                # タイムアウトを延長してリトライ
                print("🔄 タイムアウト延長でリトライ")
                driver.set_page_load_timeout(120)

                try:
                    driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
                    print("✅ 杉並区サイト成功（延長タイムアウト）")
                except Exception as retry_e:
                    print(f"❌ 杉並区サイト再試行失敗: {retry_e}")
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