#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import requests
from datetime import datetime

def setup_filters(driver, wait):
    """絞り込み設定を行う共通処理"""
    wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='施設別空き状況']")))

    month_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='1ヶ月']")))
    driver.execute_script("arguments[0].click();", month_radio)

    saturday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='土曜日']")))
    driver.execute_script("arguments[0].click();", saturday_checkbox)

    sunday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='日曜日']")))
    driver.execute_script("arguments[0].click();", sunday_checkbox)

    holiday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='祝日']")))
    driver.execute_script("arguments[0].click();", holiday_checkbox)

def click_display_and_wait(driver, wait):
    """表示ボタンをクリックして読み込み完了まで待機"""
    display_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '表示')]")))
    driver.execute_script("arguments[0].click();", display_button)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
        wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
    except:
        time.sleep(3)

def select_facility(driver, wait, facility_name):
    """施設を選択して次へ進む共通処理"""
    button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='集会施設']")))
    driver.execute_script("arguments[0].click();", button)

    checkbox = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[contains(text(), '{facility_name}')]")))
    driver.execute_script("arguments[0].click();", checkbox)

    next_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='次へ進む']")))
    driver.execute_script("arguments[0].click();", next_button)

def get_availability_data(driver, facility_key):
    """空き状況データを取得してリストで返す"""
    availability_data = []
    for date_element in driver.find_elements(By.CSS_SELECTOR, "div.events-date"):
        date_text = date_element.text
        for events_group in date_element.find_elements(By.XPATH, "./following-sibling::div[contains(@class, 'events-group')]"):
            facility_name = events_group.find_element(By.CSS_SELECTOR, "div.top-info span.room-name span").text
            for slot in events_group.find_elements(By.CSS_SELECTOR, "div.display-cells > div"):
                try:
                    if "vacant" in slot.find_element(By.CSS_SELECTOR, "div.btn-group-toggle").get_attribute("class"):
                        time_from = slot.find_element(By.XPATH, ".//input[contains(@name, 'TimeFrom')]").get_attribute("value")
                        time_to = slot.find_element(By.XPATH, ".//input[contains(@name, 'TimeTo')]").get_attribute("value")
                        availability_data.append({
                            "date": date_text,
                            "facility": facility_name,
                            "time_from": f"{time_from[:2]}:{time_from[2:]}",
                            "time_to": f"{time_to[:2]}:{time_to[2:]}",
                            "facility_key": facility_key
                        })
                except:
                    continue
    return availability_data


def load_previous_data(filename):
    """前回のデータを読み込み"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def send_slack_notification(new_slots):
    """Slackに通知を送信"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return

    message = "🏀 杉並区体育施設の新しい空きが見つかりました:\n\n"
    for slot in new_slots:
        facility_name = "西荻地域区民センター・勤福会館" if slot['facility_key'] == "nishiogi" else "セシオン杉並"
        message += f"📍 {facility_name}\n"
        message += f"🗓️ {slot['date']}\n"
        message += f"🏢 {slot['facility']}\n"
        message += f"⏰ {slot['time_from']}-{slot['time_to']}\n\n"

    payload = {"text": message}
    try:
        requests.post(webhook_url, json=payload)
    except:
        pass

def save_data_if_new_slots_added(current_data, filename):
    """新しいスロットが追加された場合のみ保存"""
    previous_data = load_previous_data(filename)

    current_availability = current_data.get("availability", [])
    previous_availability = previous_data.get("availability", [])

    # 前回のデータを識別子のセットに変換
    previous_slots = set()
    for slot in previous_availability:
        slot_id = f"{slot['facility_key']}_{slot['date']}_{slot['facility']}_{slot['time_from']}_{slot['time_to']}"
        previous_slots.add(slot_id)

    # 今回のデータから新しいスロットをチェック
    new_slots = []
    for slot in current_availability:
        slot_id = f"{slot['facility_key']}_{slot['date']}_{slot['facility']}_{slot['time_from']}_{slot['time_to']}"
        if slot_id not in previous_slots:
            new_slots.append(slot)

    if new_slots:
        current_data["last_updated"] = datetime.now().isoformat()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 新しいスロットが追加されました（{len(new_slots)}件）: {filename}")
        for slot in new_slots:
            print(f"   🆕 {slot['facility']} - {slot['date']} {slot['time_from']}-{slot['time_to']}")

        # Slack通知を送信
        send_slack_notification(new_slots)
        return True
    else:
        print(f"📝 新しいスロットはありません: {filename}")
        return False

def process_nishiogi(driver, wait):
    """西荻地域区民センター・勤福会館の処理"""
    print("🌐 サイトアクセス中...")
    try:
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
        print("✅ サイトアクセス成功")
    except Exception as e:
        print(f"❌ サイトアクセス失敗: {e}")
        raise
    select_facility(driver, wait, "西荻地域区民センター・勤福会館")
    setup_filters(driver, wait)
    click_display_and_wait(driver, wait)

    elements_a = driver.find_elements(By.XPATH, "//tr[td[contains(text(), '体育室半面Ａ')]]//label[contains(@class, 'some')]/input[@type='checkbox']")
    elements_b = driver.find_elements(By.XPATH, "//tr[td[contains(text(), '体育室半面Ｂ')]]//label[contains(@class, 'some')]/input[@type='checkbox']")

    if not elements_a and not elements_b:
        return []

    for element in elements_a + elements_b:
        driver.execute_script("arguments[0].click();", element)

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='次へ進む']"))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='時間帯別空き状況']")))

    return get_availability_data(driver, "nishiogi")

def process_sesion(driver, wait):
    """セシオン杉並の処理"""
    print("🌐 セシオン用サイトアクセス中...")
    try:
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
        print("✅ セシオン用サイトアクセス成功")
    except Exception as e:
        print(f"❌ セシオン用サイトアクセス失敗: {e}")
        raise
    select_facility(driver, wait, "セシオン杉並")
    setup_filters(driver, wait)
    click_display_and_wait(driver, wait)

    elements = driver.find_elements(By.XPATH, "//tr[td[contains(text(), '体育室全面')]]//label[contains(@class, 'some')]/input[@type='checkbox']")

    if not elements:
        return []

    for element in elements:
        driver.execute_script("arguments[0].click();", element)

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='次へ進む']"))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='時間帯別空き状況']")))

    return get_availability_data(driver, "sesion")

def run():
    print("🚀 GitHub Actions環境診断開始")

    # 環境情報の表示
    print(f"🔍 Python version: {os.sys.version}")
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 GITHUB_ACTIONS: {os.getenv('GITHUB_ACTIONS', 'not set')}")

    # Chromeの存在確認
    try:
        result = os.system("which google-chrome || which google-chrome-stable || which chromium-browser")
        print(f"🔍 Chrome検索結果: {result}")
    except:
        print("❌ Chrome検索失敗")

    # ChromeDriverの存在確認
    try:
        result = os.system("which chromedriver")
        print(f"🔍 ChromeDriver検索結果: {result}")
    except:
        print("❌ ChromeDriver検索失敗")

    print("\n🔧 最小限のChrome設定でテスト")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

    print("🔧 ChromeDriver初期化テスト...")
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ ChromeDriver初期化成功")

        print("🔧 基本接続テスト...")
        try:
            driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
            print("✅ 基本接続成功")

            title = driver.title
            print(f"✅ タイトル取得成功: {title}")

        except Exception as e:
            print(f"❌ 基本接続失敗: {e}")
            return False
        finally:
            driver.quit()
            print("✅ ChromeDriver正常終了")

        return True

    except Exception as e:
        print(f"❌ ChromeDriver初期化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run()