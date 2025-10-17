#!/usr/bin/env python3
"""
杉並区施設予約システムチェック（軽量版 - GitHub Actions対応）

使い方:
  python check_suginami_lightweight.py

機能:
  - requestsライブラリで直接HTTPリクエスト（Selenium不要）
  - 西荻地域区民センターとセシオン杉並の空き状況をチェック
  - 結果をGitHub Issueに保存
  - 変更があった場合のみSlack通知
"""

import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def get_previous_data_from_issue():
    """GitHub Issueから前回のデータを取得"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set. Skipping issue check.")
        return None

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
        facilities_text += f"- 空き枠数: {len(facility.get('slots', []))}件\n"

        if facility.get('slots'):
            facilities_text += f"- 直近の空き:\n"
            for slot in facility.get('slots', [])[:3]:  # 最初の3件のみ表示
                facilities_text += f"  - {slot.get('date', 'N/A')} {slot.get('time', 'N/A')}\n"

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

def check_facility_simple(facility_name):
    """施設の空き状況を簡易チェック（HTTPリクエストのみ）"""
    print(f"\n=== {facility_name} をチェック中 ===")

    try:
        # ユーザーエージェントを設定
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # 杉並区予約サイトにアクセス
        print("サイトにアクセス中...")
        url = "https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home"

        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)

        print(f"ステータスコード: {response.status_code}")
        print(f"URL: {response.url}")
        print(f"レスポンスサイズ: {len(response.content)} bytes")

        if response.status_code == 200:
            # HTMLをパース
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "タイトルなし"
            print(f"ページタイトル: {title}")

            # 簡易的な情報を返す
            return {
                "facility": facility_name,
                "status": "accessible",
                "checked_at": datetime.now().isoformat(),
                "url": response.url,
                "title": title,
                "slots": [],  # 後で実装
                "note": "HTTPリクエストでアクセス成功"
            }
        else:
            return {
                "facility": facility_name,
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "checked_at": datetime.now().isoformat()
            }

    except Exception as e:
        print(f"❌ エラー: {e}")
        return {
            "facility": facility_name,
            "status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }

def main():
    print("=== 杉並区施設予約チェック（軽量版） ===\n")
    print(f"実行環境: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else 'ローカル'}\n")

    facilities = []

    # 西荻地域区民センター
    nishiogi = check_facility_simple("西荻地域区民センター")
    facilities.append(nishiogi)

    # セシオン杉並
    sesion = check_facility_simple("セシオン杉並")
    facilities.append(sesion)

    # 結果をまとめる
    result = {
        "checked_at": datetime.now().isoformat(),
        "environment": "github_actions" if os.getenv("GITHUB_ACTIONS") else "local",
        "facilities": facilities
    }

    # 前回のデータを取得
    previous_data = get_previous_data_from_issue()

    # 変更を検知
    has_changes = False
    new_slots = []

    if previous_data is None:
        print("\n✓ 初回実行: データを保存します")
        has_changes = True
    else:
        # 施設ステータスの変更をチェック
        prev_facilities = {f.get('facility'): f for f in previous_data.get('facilities', [])}
        curr_facilities = {f.get('facility'): f for f in facilities}

        for name, curr_info in curr_facilities.items():
            prev_info = prev_facilities.get(name, {})

            # ステータスが変化したか
            if prev_info.get('status') != curr_info.get('status'):
                print(f"\n✓ {name} のステータスが変更されました")
                print(f"  前回: {prev_info.get('status')}")
                print(f"  今回: {curr_info.get('status')}")
                has_changes = True

            # 空き枠が増えたか（将来実装）
            prev_slots_count = len(prev_info.get('slots', []))
            curr_slots_count = len(curr_info.get('slots', []))

            if curr_slots_count > prev_slots_count:
                print(f"\n✓ {name} の空き枠が増えました ({prev_slots_count} → {curr_slots_count})")
                has_changes = True
                new_slots.append(name)

        if not has_changes:
            print("\n➡ 変更はありません")

    # 変更があった場合のみIssueを更新
    if has_changes:
        save_data_to_issue(result)

        # Slack通知
        message = "🏢 杉並区施設予約の状況が更新されました\n\n"
        for facility in facilities:
            status_emoji = "✅" if facility.get('status') == 'accessible' else "❌"
            message += f"{status_emoji} {facility.get('facility')}: {facility.get('status')}\n"

            if facility.get('slots'):
                message += f"  空き枠: {len(facility.get('slots'))}件\n"

        send_slack_notification(message)
    else:
        print("\n➡ 変更がないためIssue更新とSlack通知をスキップします")

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
