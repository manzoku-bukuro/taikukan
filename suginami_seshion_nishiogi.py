#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def run():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")

        # 集会施設→西荻→次へ進む
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='集会施設']")))
        driver.execute_script("arguments[0].click();", button)

        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), '西荻地域区民センター・勤福会館')]")))
        driver.execute_script("arguments[0].click();", checkbox)

        next_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='次へ進む']")))
        driver.execute_script("arguments[0].click();", next_button)

        # 絞り込み設定
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='施設別空き状況']")))

        month_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='1ヶ月']")))
        driver.execute_script("arguments[0].click();", month_radio)

        saturday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='土曜日']")))
        driver.execute_script("arguments[0].click();", saturday_checkbox)

        sunday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='日曜日']")))
        driver.execute_script("arguments[0].click();", sunday_checkbox)

        holiday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='祝日']")))
        driver.execute_script("arguments[0].click();", holiday_checkbox)

        # 表示ボタンクリック・待機
        display_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '表示')]")))
        driver.execute_script("arguments[0].click();", display_button)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
        except:
            time.sleep(3)

        # 体育室半面Ａ・Ｂの一部空き選択
        elements_a = driver.find_elements(By.XPATH, "//tr[td[contains(text(), '体育室半面Ａ')]]//label[contains(@class, 'some')]/input[@type='checkbox']")
        elements_b = driver.find_elements(By.XPATH, "//tr[td[contains(text(), '体育室半面Ｂ')]]//label[contains(@class, 'some')]/input[@type='checkbox']")

        for element in elements_a + elements_b:
            driver.execute_script("arguments[0].click();", element)

        # 次へ進む
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='次へ進む']"))).click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='時間帯別空き状況']")))

        # 西荻地域区民センター・勤福会館の空き状況取得
        print("🏢 西荻地域区民センター・勤福会館")
        for date_element in driver.find_elements(By.CSS_SELECTOR, "div.events-date"):
            print(f"📅 {date_element.text}")
            for events_group in date_element.find_elements(By.XPATH, "./following-sibling::div[contains(@class, 'events-group')]"):
                facility_name = events_group.find_element(By.CSS_SELECTOR, "div.top-info span.room-name span").text
                print(f"  🏢 {facility_name}")
                for slot in events_group.find_elements(By.CSS_SELECTOR, "div.display-cells > div"):
                    try:
                        if "vacant" in slot.find_element(By.CSS_SELECTOR, "div.btn-group-toggle").get_attribute("class"):
                            time_from = slot.find_element(By.XPATH, ".//input[contains(@name, 'TimeFrom')]").get_attribute("value")
                            time_to = slot.find_element(By.XPATH, ".//input[contains(@name, 'TimeTo')]").get_attribute("value")
                            print(f"    ⏰ {time_from[:2]}:{time_from[2:]}-{time_to[:2]}:{time_to[2:]}: 空き")
                    except:
                        continue

        # セシオン杉並の処理開始
        print("\n🔄 セシオン杉並の情報を取得中...")
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")

        # 集会施設→セシオン杉並→次へ進む
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='集会施設']")))
        driver.execute_script("arguments[0].click();", button)

        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'セシオン杉並')]")))
        driver.execute_script("arguments[0].click();", checkbox)

        next_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='次へ進む']")))
        driver.execute_script("arguments[0].click();", next_button)

        # 絞り込み設定
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='施設別空き状況']")))

        month_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='1ヶ月']")))
        driver.execute_script("arguments[0].click();", month_radio)

        saturday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='土曜日']")))
        driver.execute_script("arguments[0].click();", saturday_checkbox)

        sunday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='日曜日']")))
        driver.execute_script("arguments[0].click();", sunday_checkbox)

        holiday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='祝日']")))
        driver.execute_script("arguments[0].click();", holiday_checkbox)

        # 表示ボタンクリック・待機
        display_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '表示')]")))
        driver.execute_script("arguments[0].click();", display_button)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
        except:
            time.sleep(3)

        # 体育室全面の一部空き選択
        for element in driver.find_elements(By.XPATH, "//tr[td[contains(text(), '体育室全面')]]//label[contains(@class, 'some')]/input[@type='checkbox']"):
            driver.execute_script("arguments[0].click();", element)

        # 次へ進む
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='次へ進む']"))).click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='時間帯別空き状況']")))

        # セシオン杉並の空き状況取得
        print("🏢 セシオン杉並")
        for date_element in driver.find_elements(By.CSS_SELECTOR, "div.events-date"):
            print(f"📅 {date_element.text}")
            for events_group in date_element.find_elements(By.XPATH, "./following-sibling::div[contains(@class, 'events-group')]"):
                facility_name = events_group.find_element(By.CSS_SELECTOR, "div.top-info span.room-name span").text
                print(f"  🏢 {facility_name}")
                for slot in events_group.find_elements(By.CSS_SELECTOR, "div.display-cells > div"):
                    try:
                        if "vacant" in slot.find_element(By.CSS_SELECTOR, "div.btn-group-toggle").get_attribute("class"):
                            time_from = slot.find_element(By.XPATH, ".//input[contains(@name, 'TimeFrom')]").get_attribute("value")
                            time_to = slot.find_element(By.XPATH, ".//input[contains(@name, 'TimeTo')]").get_attribute("value")
                            print(f"    ⏰ {time_from[:2]}:{time_from[2:]}-{time_to[:2]}:{time_to[2:]}: 空き")
                    except:
                        continue

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    run()