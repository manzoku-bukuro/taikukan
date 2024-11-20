import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# WebDriverの設定
options = Options()
options.add_argument("--headless")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--no-sandbox")
options.add_argument("--lang=ja")
driver = webdriver.Chrome(options=options)

# Slackに通知を送信する関数
def send_slack_notification(message):
    WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not WEBHOOK_URL:
        print("Slack Webhook URL is not set.")
        return
    payload = {
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send notification: {response.status_code}, {response.text}")

try:
    # Googleフォームにアクセス
    driver.get("https://forms.gle/LPG6ZkT9evvAbdND6")
    
    # ページが完全に読み込まれるまで待機
    time.sleep(5)
    
    # 最初に見つかるdiv要素を取得
    div_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "div"))
    )
    
    # div要素のテキストを取得
    div_text = div_element.text
    print("Div text:", div_text)
    
    # テキストが「現在満枠となっております」を含むかどうかをチェック
    if "現在満枠となっております" in div_text:
        print("現在満枠となっております")
        send_slack_notification("現在満枠となっております")
    else:
        print("現在満枠ではありません")
        send_slack_notification("現在満枠ではありません")
    
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()