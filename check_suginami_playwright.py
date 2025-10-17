#!/usr/bin/env python3
"""
杉並区施設予約システムチェック（Playwright版）

Playwrightを使用してGitHub Actionsで安定動作
"""

import os
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def send_slack_notification(new_slots):
    """Slackに通知を送信"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠ SLACK_WEBHOOK_URL not set")
        return

    message = "🏀 杉並区体育施設の新しい空きが見つかりました:\n\n"
    for slot in new_slots:
        facility_name = "西荻地域区民センター" if slot['facility_key'] == "nishiogi" else "セシオン杉並"
        message += f"📍 {facility_name}\n"
        message += f"🗓️ {slot['date']}\n"
        message += f"🏢 {slot['facility']}\n"
        message += f"⏰ {slot['time_from']}-{slot['time_to']}\n\n"

    payload = {"text": message}
    try:
        requests.post(webhook_url, json=payload)
        print("✓ Slack通知を送信しました")
    except Exception as e:
        print(f"⚠ Slack通知失敗: {e}")

def get_previous_data_from_issue():
    """GitHub Issueから前回のデータを取得"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set")
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
    except Exception as e:
        print(f"⚠ Error getting previous data: {e}")

    return None

def save_data_to_issue(data):
    """GitHub Issueにデータを保存"""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY", "manzoku-bukuro/taikukan")

    if not GITHUB_TOKEN:
        print("⚠ GITHUB_TOKEN is not set")
        return False

    issue_number = 2
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Issueの本文を作成
    slots_text = ""
    for slot in data.get("availability", [])[:10]:  # 最初の10件
        slots_text += f"- {slot['date']} {slot['facility']} {slot['time_from']}-{slot['time_to']}\n"

    body = f"""# 杉並区施設予約 空き状況

最終更新: {data['checked_at']}

## 直近の空き枠（最大10件）

{slots_text}

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

def check_availability_with_playwright():
    """Playwrightで空き状況をチェック（リトライ機能付き）"""
    print("=== Playwright で杉並区施設予約をチェック ===\n")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            return _try_check_availability(attempt + 1)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"⚠ 試行 {attempt + 1}/{max_retries} 失敗: {str(e)[:100]}")
                print(f"  {wait_time}秒後に再試行...")
                import time
                time.sleep(wait_time)
            else:
                print(f"❌ 全ての試行が失敗しました")
                return None

def _try_check_availability(attempt_num):
    """実際のチェック処理"""
    print(f"[試行 {attempt_num}]")

    with sync_playwright() as p:
        # ブラウザ起動（headlessモード）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ja-JP",
            timezone_id="Asia/Tokyo"
        )
        page = context.new_page()

        try:
            # ホームページにアクセス
            print("サイトにアクセス中...")
            page.goto("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home",
                     wait_until="domcontentloaded", timeout=60000)

            # Vueアプリが読み込まれるまで待つ（集会施設ボタンが表示されるまで）
            print("Vueアプリの初期化を待機中...")
            page.wait_for_selector("button:text('集会施設')", timeout=30000, state="visible")
            print(f"✓ ページタイトル: {page.title()}")

            # 集会施設ボタンをクリック
            print("集会施設を選択中...")
            page.click("button:text('集会施設')")

            # 施設選択画面が表示されるまで待つ
            page.wait_for_selector("label:has-text('西荻地域区民センター・勤福会館')", timeout=15000, state="visible")

            # 西荻地域区民センターを選択
            print("西荻地域区民センターを選択中...")
            page.click("label:has-text('西荻地域区民センター・勤福会館')")
            page.wait_for_timeout(500)

            # 次へボタン
            page.click("button[aria-label='次へ進む']")
            page.wait_for_selector("h2:text('施設別空き状況')", timeout=30000)
            print("✓ 施設別空き状況ページに遷移")

            # フィルター設定
            print("フィルター設定中...")

            # フィルター要素が表示されるまで待つ（Vueルーティング遷移）
            page.wait_for_timeout(2000)  # Vueのマウント待ち

            # JavaScriptで直接操作
            page.evaluate("""
                // 1ヶ月を選択
                const monthLabel = Array.from(document.querySelectorAll('label')).find(l => l.textContent.trim() === '1ヶ月');
                if (monthLabel) monthLabel.click();
            """)
            page.wait_for_timeout(1000)

            # 曜日フィルタをJavaScriptで操作
            page.evaluate("""
                // 土曜日
                const satLabel = Array.from(document.querySelectorAll('label')).find(l => l.textContent.includes('土曜日'));
                if (satLabel) satLabel.click();
            """)
            page.wait_for_timeout(500)

            page.evaluate("""
                // 日曜日
                const sunLabel = Array.from(document.querySelectorAll('label')).find(l => l.textContent.includes('日曜日'));
                if (sunLabel) sunLabel.click();
            """)
            page.wait_for_timeout(500)

            page.evaluate("""
                // 祝日
                const holLabel = Array.from(document.querySelectorAll('label')).find(l => l.textContent.includes('祝日'));
                if (holLabel) holLabel.click();
            """)
            page.wait_for_timeout(1000)

            # 表示ボタンをクリック
            page.click("button:text('表示')")
            page.wait_for_timeout(3000)
            print("✓ 空き状況を表示")

            # 体育室を選択
            print("体育室を選択中...")

            # JavaScriptで体育室のチェックボックスを直接操作
            checkboxes_count = page.evaluate("""
                (() => {
                    const checkboxes = document.querySelectorAll('tr td:first-child');
                    let count = 0;
                    checkboxes.forEach(td => {
                        if (td.textContent.includes('体育室半面')) {
                            const checkbox = td.closest('tr').querySelector('input[type="checkbox"]');
                            if (checkbox) {
                                checkbox.click();
                                count++;
                            }
                        }
                    });
                    return count;
                })()
            """)
            print(f"✓ 体育室チェックボックスをクリック: {checkboxes_count}個")
            page.wait_for_timeout(1000)

            # 次へ
            page.click("button[aria-label='次へ進む']")
            page.wait_for_selector("h2:text('時間帯別空き状況')", timeout=30000)
            print("✓ 時間帯別空き状況ページに遷移")

            # 空き情報を取得
            print("空き情報を取得中...")

            # JavaScriptで空き情報を取得（vacant以外も含む）
            debug_info = page.evaluate("""
                (() => {
                    const debug = {
                        dateElementsCount: 0,
                        eventsGroupCount: 0,
                        totalSlotsCount: 0,
                        vacantSlotsCount: 0,
                        fullSlotsCount: 0,
                        otherSlotsCount: 0,
                        results: []
                    };

                    const dateElements = document.querySelectorAll('div.events-date');
                    debug.dateElementsCount = dateElements.length;

                    dateElements.forEach((dateElem, idx) => {
                        const dateText = dateElem.textContent.trim();

                        // 次の兄弟要素を探す
                        let sibling = dateElem.nextElementSibling;
                        while (sibling && sibling.classList.contains('events-group')) {
                            debug.eventsGroupCount++;

                            const facilityNameElem = sibling.querySelector('div.top-info span.room-name span');
                            const facilityName = facilityNameElem ? facilityNameElem.textContent.trim() : '';

                            // 全てのスロットを探す
                            const allSlots = sibling.querySelectorAll('div.display-cells > div');
                            debug.totalSlotsCount += allSlots.length;

                            allSlots.forEach(slot => {
                                const btnGroup = slot.querySelector('div.btn-group-toggle');
                                if (btnGroup) {
                                    const isVacant = btnGroup.classList.contains('vacant');
                                    const isFull = btnGroup.classList.contains('full');

                                    if (isVacant) debug.vacantSlotsCount++;
                                    else if (isFull) debug.fullSlotsCount++;
                                    else debug.otherSlotsCount++;

                                    // vacantの場合のみ結果に追加
                                    if (isVacant) {
                                        const timeFromInput = slot.querySelector('input[name*="TimeFrom"]');
                                        const timeToInput = slot.querySelector('input[name*="TimeTo"]');

                                        if (timeFromInput && timeToInput) {
                                            const timeFrom = timeFromInput.value;
                                            const timeTo = timeToInput.value;

                                            const slotData = {
                                                date: dateText,
                                                facility: facilityName,
                                                time_from: timeFrom.substring(0, 2) + ':' + timeFrom.substring(2),
                                                time_to: timeTo.substring(0, 2) + ':' + timeTo.substring(2),
                                                facility_key: 'nishiogi'
                                            };
                                            debug.results.push(slotData);
                                        }
                                    }
                                }
                            });

                            sibling = sibling.nextElementSibling;
                        }
                    });

                    return debug;
                })()
            """)

            availability_data = debug_info['results']
            print(f"📊 デバッグ情報:")
            print(f"  - 日付要素: {debug_info['dateElementsCount']}個")
            print(f"  - 施設: {debug_info['eventsGroupCount']}個")
            print(f"  - 総スロット数: {debug_info['totalSlotsCount']}個")
            print(f"  - 空き: {debug_info['vacantSlotsCount']}個")
            print(f"  - 満室: {debug_info['fullSlotsCount']}個")
            print(f"  - その他: {debug_info['otherSlotsCount']}個")

            print(f"✓ 空き枠を{len(availability_data)}件取得しました")

            # デバッグ: 最初の数件を表示
            if availability_data:
                for slot in availability_data[:3]:
                    print(f"  - {slot['date']} {slot['facility']} {slot['time_from']}-{slot['time_to']}")
            else:
                print("  （空き枠なし）")

            browser.close()

            return availability_data

        except Exception as e:
            print(f"❌ エラー: {e}")
            browser.close()
            return None

def main():
    print(f"実行環境: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else 'ローカル'}\n")

    # 空き状況をチェック
    availability = check_availability_with_playwright()

    if availability is None:
        print("⚠ エラーが発生しました")
        return False

    if len(availability) == 0:
        print("ℹ️  空き枠はありませんが、チェックは正常に完了しました")

    # 現在のデータ
    current_data = {
        "checked_at": datetime.now().isoformat(),
        "availability": availability,
        "count": len(availability)
    }

    # 前回のデータを取得
    previous_data = get_previous_data_from_issue()

    # 新しいスロットを検出
    new_slots = []
    if previous_data:
        previous_slots = set()
        for slot in previous_data.get("availability", []):
            slot_id = f"{slot['facility_key']}_{slot['date']}_{slot['facility']}_{slot['time_from']}_{slot['time_to']}"
            previous_slots.add(slot_id)

        for slot in availability:
            slot_id = f"{slot['facility_key']}_{slot['date']}_{slot['facility']}_{slot['time_from']}_{slot['time_to']}"
            if slot_id not in previous_slots:
                new_slots.append(slot)

        if new_slots:
            print(f"\n✓ 新しい空き枠: {len(new_slots)}件")
            for slot in new_slots[:5]:
                print(f"  🆕 {slot['date']} {slot['facility']} {slot['time_from']}-{slot['time_to']}")
        else:
            print("\n➡ 新しい空き枠はありません")
    else:
        print("\n✓ 初回実行")
        new_slots = availability

    # Issueを更新
    save_data_to_issue(current_data)

    # 新しい空き枠があればSlack通知
    if new_slots:
        send_slack_notification(new_slots)

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
