#!/usr/bin/env python3
"""
杉並区施設予約システムチェック（ローカル実行用）

使い方:
  python check_suginami_local.py

機能:
  - 西荻地域区民センターとセシオン杉並の空き状況をチェック
  - 結果をsuginami_availability.jsonに保存
  - 変更があった場合はgit commitを促す
"""

import os
import sys
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# ChromeDriverを自動インストール
chromedriver_autoinstaller.install()

def get_chrome_driver():
    """Chromeドライバーを取得（ローカル最適化）"""
    options = Options()
    # ローカルではheadlessをオプションに
    if os.getenv('HEADLESS', 'true').lower() == 'true':
        options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def check_facility(driver, wait, facility_name):
    """施設の空き状況をチェック"""
    print(f"\n=== {facility_name} をチェック中 ===")

    try:
        # 杉並区予約サイトにアクセス
        print("サイトにアクセス中...")
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
        time.sleep(3)

        print(f"ページタイトル: {driver.title}")
        print(f"URL: {driver.current_url}")

        # ここで実際の施設選択とデータ取得を実装
        # 現時点では基本的な接続確認のみ

        availability = {
            "facility": facility_name,
            "status": "accessible",
            "checked_at": datetime.now().isoformat(),
            "url": driver.current_url,
            "title": driver.title,
            "slots": []  # 実際の空き枠情報
        }

        return availability

    except Exception as e:
        print(f"❌ エラー: {e}")
        return {
            "facility": facility_name,
            "status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }

def save_results(data, filename="suginami_availability.json"):
    """結果をJSONファイルに保存"""

    # 既存データを読み込み
    previous_data = None
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)
        except:
            pass

    # 新しいデータを保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 結果を {filename} に保存しました")

    # 変更を検知
    has_changes = False
    if previous_data is None:
        print("✓ 初回実行です")
        has_changes = True
    elif previous_data.get("facilities") != data.get("facilities"):
        print("✓ 空き状況に変更がありました")
        has_changes = True
    else:
        print("➡ 変更はありません")

    return has_changes

def main():
    print("=== 杉並区施設予約チェック（ローカル版） ===\n")

    driver = None
    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 10)

        facilities = []

        # 西荻地域区民センター
        nishiogi = check_facility(driver, wait, "西荻地域区民センター")
        facilities.append(nishiogi)

        # セシオン杉並
        sesion = check_facility(driver, wait, "セシオン杉並")
        facilities.append(sesion)

        # 結果をまとめる
        result = {
            "checked_at": datetime.now().isoformat(),
            "environment": "local",
            "facilities": facilities
        }

        # 保存
        has_changes = save_results(result)

        # Gitコミットの案内
        if has_changes:
            print("\n" + "="*60)
            print("🔔 変更が検出されました！")
            print("="*60)
            print("\n以下のコマンドでGitにコミットしてください：")
            print("\n  git add suginami_availability.json")
            print("  git commit -m 'Update suginami availability'")
            print("  git push origin master")
            print("\n" + "="*60)

        return True

    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            driver.quit()
            print("\n✓ ブラウザを終了しました")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
