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
    """杉並区さざんかねっと - 集会施設ボタンクリック"""
    # Chrome設定
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")

    # WebDriver起動
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. ホームページアクセス
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 2. 集会施設ボタンクリック
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='集会施設']")))
        driver.execute_script("arguments[0].click();", button)

        # 3. 遷移確認
        wait.until(lambda driver: "AvailabilityCheckApplySelectFacility" in driver.current_url)
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='施設選択']")))

        print("✅ 成功: 施設選択ページに遷移しました")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    run()