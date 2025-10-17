import os
import time
import json
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
wait = WebDriverWait(driver, 10)

def check_facilities():
    """施設の空き状況をチェック"""
    facilities_data = []

    try:
        # ステップ1: メインページにアクセス
        print("\n=== メインページにアクセス ===")
        url = "https://www.11489.jp/Chuo/web/Wg_ModeSelect.aspx"
        driver.get(url)
        time.sleep(2)

        # タイトル確認
        title_element = wait.until(
            EC.presence_of_element_located((By.ID, "ucPCHeader_lblTitle2"))
        )
        print(f"✓ {title_element.text}")

        # ステップ2: 空き照会・予約の申込をクリック
        print("\n=== 空き照会・予約の申込 ===")
        yoyaku_button = wait.until(
            EC.element_to_be_clickable((By.ID, "rbtnYoyaku"))
        )
        yoyaku_button.click()
        time.sleep(2)
        print(f"✓ {driver.title}")

        # ステップ3: 施設カテゴリを取得
        print("\n=== 施設カテゴリ一覧 ===")
        facility_buttons = driver.find_elements(By.CSS_SELECTOR, "input[id*='dgTable'][id*='chkShisetsu']")

        for i, btn in enumerate(facility_buttons):
            facility_name = btn.get_attribute('value')
            facility_id = btn.get_attribute('id')
            print(f"{i+1}. {facility_name} (ID: {facility_id})")

            facilities_data.append({
                "name": facility_name,
                "id": facility_id,
                "checked_at": datetime.now().isoformat()
            })

        # スクリーンショットを保存
        driver.save_screenshot("chuo_facilities_list.png")
        print(f"\n✓ 施設一覧のスクリーンショットを保存: chuo_facilities_list.png")

        # ステップ4: 学校体育館を選択してみる
        print("\n=== 学校体育館の詳細を確認 ===")
        try:
            gym_button = driver.find_element(By.ID, "dgTable_ctl04_chkShisetsu")
            gym_button.click()
            time.sleep(1)
            print("✓ 学校体育館を選択")

            # 施設一覧表示ボタンをクリック
            list_button = wait.until(
                EC.element_to_be_clickable((By.ID, "btnList"))
            )
            list_button.click()
            time.sleep(3)
            print(f"✓ 施設一覧表示: {driver.title}")

            # 施設一覧のスクリーンショット
            driver.save_screenshot("chuo_gym_list.png")
            print("✓ 学校体育館一覧のスクリーンショットを保存: chuo_gym_list.png")

            # 施設リストを取得
            print("\n=== 学校体育館リスト ===")
            # テーブルまたはリスト要素を探す
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # HTMLを保存して詳細を確認
            with open("chuo_gym_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("✓ ページソースを保存: chuo_gym_page.html")

        except Exception as e:
            print(f"⚠ 学校体育館の詳細確認でエラー: {e}")

        return facilities_data

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error_screenshot.png")
        return []

try:
    # 施設の空き状況をチェック
    facilities = check_facilities()

    # 結果を保存
    result = {
        "checked_at": datetime.now().isoformat(),
        "facilities": facilities,
        "total_count": len(facilities)
    }

    with open("chuo_facilities.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 結果を保存しました: chuo_facilities.json")
    print(f"✓ 施設数: {len(facilities)}")

except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nブラウザを閉じます...")
    driver.quit()
    print("完了しました。")
