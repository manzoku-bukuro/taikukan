#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os

def simple_test():
    print("🚀 シンプルテスト開始")

    # 最小限のChrome設定
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    try:
        driver = webdriver.Chrome(options=options)
        print("✅ ChromeDriver初期化成功")

        # 短いタイムアウト設定
        driver.set_page_load_timeout(60)
        wait = WebDriverWait(driver, 15)

        print("🌐 杉並区サイトアクセス...")

        try:
            driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
            print("✅ ページアクセス成功")

            # ページタイトル取得
            title = driver.title
            print(f"📄 ページタイトル: {title}")

            # ページソースの最初の500文字
            page_source = driver.page_source[:500]
            print(f"📄 ページソース先頭:\n{page_source}")

            # 基本要素の確認
            try:
                # bodyタグの存在確認
                body = driver.find_element(By.TAG_NAME, "body")
                print(f"✅ bodyタグ発見: {body.tag_name}")

                # すべてのボタン要素を取得
                buttons = driver.find_elements(By.TAG_NAME, "button")
                print(f"🔘 ボタン数: {len(buttons)}")

                # 最初の3つのボタンのテキストを表示
                for i, button in enumerate(buttons[:3]):
                    try:
                        text = button.text or button.get_attribute("aria-label") or "テキストなし"
                        print(f"   ボタン{i+1}: {text}")
                    except:
                        print(f"   ボタン{i+1}: 取得エラー")

                # すべてのリンク要素を取得
                links = driver.find_elements(By.TAG_NAME, "a")
                print(f"🔗 リンク数: {len(links)}")

                # div要素の数
                divs = driver.find_elements(By.TAG_NAME, "div")
                print(f"📦 div要素数: {len(divs)}")

            except Exception as e:
                print(f"❌ 要素取得エラー: {e}")

        except Exception as e:
            print(f"❌ ページアクセスエラー: {e}")
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