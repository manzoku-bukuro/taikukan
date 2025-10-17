#!/usr/bin/env python3
"""
杉並区施設予約の変更通知（GitHub Actions用）

使い方:
  python notify_suginami_changes.py

機能:
  - suginami_availability.jsonの変更を検知
  - GitHub Issueに記録
  - Slack通知（変更があった場合のみ）
"""

import os
import json
import requests
from datetime import datetime

def get_previous_data_from_issue():
    """GitHub Issueから前回のデータを取得"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set. Skipping issue check.")
        return None

    # Issue #2 を杉並区用に使用
    issue_number = 2
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

            if "```json" in body:
                json_start = body.find("```json") + 7
                json_end = body.find("```", json_start)
                json_str = body[json_start:json_end].strip()
                data = json.loads(json_str)
                print(f"✓ 前回のデータを取得しました (Issue #{issue_number})")
                return data
        elif response.status_code == 404:
            print(f"⚠ Issue #{issue_number} not found. Will create new one.")
    except Exception as e:
        print(f"⚠ Error getting previous data: {e}")

    return None

def save_data_to_issue(data):
    """GitHub Issueにデータを保存"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set. Skipping issue save.")
        return False

    issue_number = 2
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Issueの本文を作成
    facilities_text = ""
    for facility in data.get("facilities", []):
        facilities_text += f"\n### {facility.get('facility', 'Unknown')}\n"
        facilities_text += f"- ステータス: {facility.get('status', 'unknown')}\n"
        facilities_text += f"- チェック時刻: {facility.get('checked_at', 'N/A')}\n"

    body = f"""# 杉並区施設予約 空き状況

最終更新: {data['checked_at']}

## 施設一覧

{facilities_text}

## 詳細データ

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

---
このIssueは自動的に更新されます。
"""

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        update_data = {"body": body}
        response = requests.patch(url, headers=headers, json=update_data)
        if response.status_code == 200:
            print(f"✓ Issue #{issue_number} を更新しました")
            return True
    elif response.status_code == 404:
        create_url = f"https://api.github.com/repos/{REPO}/issues"
        create_data = {
            "title": "杉並区施設予約 空き状況",
            "body": body,
            "labels": ["automated", "suginami"]
        }
        response = requests.post(create_url, headers=headers, json=create_data)
        if response.status_code == 201:
            print(f"✓ 新しいIssue #{issue_number} を作成しました")
            return True

    print(f"⚠ Failed to save to issue: {response.status_code}")
    return False

def send_slack_notification(message):
    """Slackに通知"""
    WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not WEBHOOK_URL:
        print("⚠ Slack Webhook URL is not set.")
        return

    payload = {"text": message}
    headers = {"Content-Type": "application/json"}

    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"⚠ Failed to send Slack notification: {response.status_code}")
    else:
        print("✓ Slack通知を送信しました")

def main():
    print("=== 杉並区施設予約 変更通知チェック ===\n")

    # JSONファイルを読み込み
    json_file = "suginami_availability.json"
    if not os.path.exists(json_file):
        print(f"⚠ {json_file} が見つかりません")
        return False

    with open(json_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)

    print(f"✓ 現在のデータを読み込みました")
    print(f"  チェック時刻: {current_data.get('checked_at')}")
    print(f"  施設数: {len(current_data.get('facilities', []))}")

    # 前回のデータを取得
    previous_data = get_previous_data_from_issue()

    # 変更を検知
    has_changes = False
    if previous_data is None:
        print("\n✓ 初回実行: データを保存します")
        has_changes = True
    else:
        # 施設ステータスの変更をチェック
        prev_facilities = {f.get('facility'): f for f in previous_data.get('facilities', [])}
        curr_facilities = {f.get('facility'): f for f in current_data.get('facilities', [])}

        for name, curr_info in curr_facilities.items():
            prev_info = prev_facilities.get(name, {})
            if prev_info.get('status') != curr_info.get('status'):
                print(f"\n✓ {name} のステータスが変更されました")
                print(f"  前回: {prev_info.get('status')}")
                print(f"  今回: {curr_info.get('status')}")
                has_changes = True

        if not has_changes:
            print("\n➡ 変更はありません")

    # 変更があった場合のみIssueを更新
    if has_changes:
        save_data_to_issue(current_data)

        # Slack通知
        message = "🏢 杉並区施設予約の状況が更新されました\n\n"
        for facility in current_data.get('facilities', []):
            message += f"• {facility.get('facility')}: {facility.get('status')}\n"

        send_slack_notification(message)
    else:
        print("\n➡ 変更がないためIssue更新とSlack通知をスキップします")

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
