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

        # 1ヶ月ラジオボタン選択
        month_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='1ヶ月']")))
        driver.execute_script("arguments[0].click();", month_radio)

        # 土曜日チェックボックス選択
        saturday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='土曜日']")))
        driver.execute_script("arguments[0].click();", saturday_checkbox)

        # 日曜日チェックボックス選択
        sunday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='日曜日']")))
        driver.execute_script("arguments[0].click();", sunday_checkbox)

        # 祝日チェックボックス選択
        holiday_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//label[text()='祝日']")))
        driver.execute_script("arguments[0].click();", holiday_checkbox)

        # 表示ボタンクリック
        display_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '表示')] | //input[@type='submit' and @value='表示']")))
        driver.execute_script("arguments[0].click();", display_button)

        # loading-indicatorクラスが消えるまで待機
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "body.loading-indicator")))
        except:
            import time
            time.sleep(3)

        # テーブル取得
        table = wait.until(EC.presence_of_element_located((By.XPATH, "//table[@class='table table-schedule table-striped w-auto']")))
        thead = table.find_element(By.TAG_NAME, "thead")
        print(thead.text)
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    run()