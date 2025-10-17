import os
import time
import json
import hashlib
import requests
import chromedriver_autoinstaller
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ChromeDriverを自動インストール
chromedriver_autoinstaller.install()

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

# GitHub Issueから前回の日程データを取得
def get_previous_dates_from_issue():
    """GitHub Issueから前回保存された日程データを取得"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set. Skipping issue check.")
        return None

    # Issue #1 を使用（なければ作成される）
    issue_number = 1
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            issue = response.json()
            body = issue.get("body", "")

            # JSON形式のデータを抽出
            if "```json" in body:
                json_start = body.find("```json") + 7
                json_end = body.find("```", json_start)
                json_str = body[json_start:json_end].strip()
                data = json.loads(json_str)
                print(f"✓ 前回のデータを取得しました (Issue #{issue_number})")
                return data
        elif response.status_code == 404:
            print(f"⚠ Issue #{issue_number} not found. Will create new one.")
        else:
            print(f"⚠ Failed to get issue: {response.status_code}")
    except Exception as e:
        print(f"⚠ Error getting previous data: {e}")

    return None

# GitHub Issueに日程データを保存
def save_dates_to_issue(dates_data):
    """GitHub Issueに日程データを保存"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set. Skipping issue save.")
        return False

    issue_number = 1
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Issueの本文を作成
    body = f"""# Pickleball Park 参加日程

最終更新: {dates_data['checked_at']}

## 利用可能な日程

```json
{json.dumps(dates_data, ensure_ascii=False, indent=2)}
```

---
このIssueは自動的に更新されます。
"""

    # まずIssueが存在するか確認
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # 既存のIssueを更新
        update_data = {"body": body}
        response = requests.patch(url, headers=headers, json=update_data)
        if response.status_code == 200:
            print(f"✓ Issue #{issue_number} を更新しました")
            return True
    elif response.status_code == 404:
        # 新しいIssueを作成
        create_url = f"https://api.github.com/repos/{REPO}/issues"
        create_data = {
            "title": "Pickleball Park 参加日程",
            "body": body,
            "labels": ["automated", "andbiz"]
        }
        response = requests.post(create_url, headers=headers, json=create_data)
        if response.status_code == 201:
            print(f"✓ 新しいIssue #{issue_number} を作成しました")
            return True

    print(f"⚠ Failed to save to issue: {response.status_code}")
    return False

# 日程オプションを抽出
def extract_date_options(driver):
    """フォームから日程オプションを抽出"""
    import re

    body = driver.find_element(By.TAG_NAME, "body")
    page_text = body.text

    # 日付パターン: YYYY年MM月DD日(曜日) HH:MM-HH:MM
    date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日\([月火水木金土日]\)\s*\d{1,2}:\d{2}-\d{1,2}:\d{2})'

    dates = re.findall(date_pattern, page_text)

    # 重複を削除して、上限に達した日程を除外
    unique_dates = []
    for date in dates:
        if date not in unique_dates:
            # 上限チェック（この日程の前後に「上限に達しました」があるかチェック）
            date_index = page_text.find(date)
            context = page_text[max(0, date_index-50):date_index+len(date)+50]

            if "上限に達しました" not in context and "上限に達した" not in context:
                unique_dates.append(date)

    return unique_dates

try:
    print("=== Pickleball Park 参加日程チェック開始 ===\n")

    # Googleフォームにアクセス
    print("Googleフォームにアクセス中...")
    driver.get("https://forms.gle/etxKzkA6G9x5kWAn8")
    time.sleep(5)

    # ページテキストを取得
    body = driver.find_element(By.TAG_NAME, "body")
    page_text = body.text

    # 「現在満枠となっております」チェック
    if "現在満枠となっております" in page_text:
        print("⚠ 現在満枠となっております")
        # 満枠の場合でもIssueは更新（状態を記録）
        dates_data = {
            "status": "full",
            "available_dates": [],
            "checked_at": datetime.now().isoformat()
        }
        save_dates_to_issue(dates_data)
    else:
        print("✓ 現在満枠ではありません\n")

        # 利用可能な日程を抽出
        available_dates = extract_date_options(driver)
        print(f"=== 利用可能な日程 ({len(available_dates)}件) ===")
        for i, date in enumerate(available_dates, 1):
            print(f"{i}. {date}")

        # 現在のデータ
        current_data = {
            "status": "available",
            "available_dates": available_dates,
            "checked_at": datetime.now().isoformat()
        }

        # 前回のデータを取得
        previous_data = get_previous_dates_from_issue()

        # 変更があったかチェック
        has_changes = False
        new_dates = []

        if previous_data is None:
            # 初回実行
            print("\n✓ 初回実行: データを保存します")
            has_changes = True
        elif previous_data.get("status") == "full":
            # 前回は満枠だったが、今回は空きあり
            print("\n✓ 状態変化: 満枠 → 空きあり")
            has_changes = True
            new_dates = available_dates
        else:
            # 日程リストを比較
            previous_dates = set(previous_data.get("available_dates", []))
            current_dates = set(available_dates)

            # 新しく追加された日程
            new_dates = list(current_dates - previous_dates)

            if new_dates:
                print(f"\n✓ 新しい日程が追加されました ({len(new_dates)}件)")
                for date in new_dates:
                    print(f"  + {date}")
                has_changes = True
            else:
                print("\n➡ 日程に変更はありません")

        # Issueを更新
        save_dates_to_issue(current_data)

        # 変更があった場合のみSlack通知
        if has_changes and available_dates:
            message = "🎾 Pickleball Park に空きがあります！\n\n"
            if new_dates:
                message += "【新しい日程】\n"
                for date in new_dates:
                    message += f"• {date}\n"
            else:
                message += "【利用可能な日程】\n"
                for date in available_dates:
                    message += f"• {date}\n"

            message += "\n詳細: https://forms.gle/etxKzkA6G9x5kWAn8"

            print(f"\n=== Slack通知を送信 ===")
            send_slack_notification(message)
        else:
            print("\n➡ 変更がないためSlack通知はスキップします")

except Exception as e:
    print(f"\n❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\n=== 完了 ===")