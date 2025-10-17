import os
import time
import chromedriver_autoinstaller
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ChromeDriverを自動的にインストール
print("ChromeDriverを確認中...")
chromedriver_autoinstaller.install()

# WebDriverの設定（GitHub Actions対応）
options = Options()
options.add_argument("--headless")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
options.add_argument("--lang=ja")

# GitHub Actions環境かどうかを確認
is_ci = os.getenv('CI') == 'true'
if is_ci:
    print("GitHub Actions環境で実行中")
else:
    print("ローカル環境で実行中（headlessモード）")

print("Chrome WebDriverを起動します...")
driver = webdriver.Chrome(options=options)

try:
    # 公共施設予約システムにアクセス（基本URLから）
    url = "https://www.11489.jp/Chuo/web/Wg_ModeSelect.aspx"
    print(f"アクセス中: {url}")
    driver.get(url)

    # ページが完全に読み込まれるまで待機
    print("ページの読み込みを待機中...")
    time.sleep(3)

    # 指定された要素を取得
    print("要素を検索中...")
    title_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ucPCHeader_lblTitle2"))
    )

    # 要素のテキストを取得
    title_text = title_element.text
    print(f"✓ 要素が見つかりました！")
    print(f"テキスト内容: {title_text}")

    # 要素の属性も確認
    print(f"フォントサイズ: {title_element.get_attribute('style')}")

    # ページタイトルも確認
    print(f"ページタイトル: {driver.title}")

    # スクリーンショットを保存（確認用）
    screenshot_path = "chuo_screenshot.png"
    driver.save_screenshot(screenshot_path)
    print(f"スクリーンショットを保存しました: {screenshot_path}")

except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("ブラウザを閉じます...")
    driver.quit()
    print("完了しました。")
