#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def run():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home")

        # 集会施設ボタンクリック
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='集会施設']")))
        driver.execute_script("arguments[0].click();", button)

        # 西荻地域区民センター・勤福会館チェック
        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), '西荻地域区民センター・勤福会館')]")))
        driver.execute_script("arguments[0].click();", checkbox)

        # 次へ進む
        next_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='次へ進む']")))
        driver.execute_script("arguments[0].click();", next_button)

        # 施設別空き状況ページ確認
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='施設別空き状況']")))
        print("✅ 施設別空き状況ページに到達")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    run()