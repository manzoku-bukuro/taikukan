import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import difflib

# ローカルファイルの読み書き関数
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

def write_file(file_path, lines):
    with open(file_path, 'w') as file:
        file.writelines(lines)

# シートの比較関数
def compare_sheets(file1, file2):
    lines1 = read_file(file1)
    lines2 = read_file(file2)
    diff = list(difflib.unified_diff(lines1, lines2))
    return diff

# Slackに通知を送信する関数
def send_slack_notification(message):
    WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not WEBHOOK_URL:
        print("Slack Webhook URL is not set.")
        return
    payload = {
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send notification: {response.status_code}, {response.text}")

# WebDriverの設定
options = Options()
options.add_argument("--headless")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--no-sandbox")
options.add_argument("--lang=ja")
driver = webdriver.Chrome(options=options)

# 要素をクリックする関数
def click_element(driver, selector):
    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    element.click()

# データをシートに書き込む関数
def write_data_to_sheet(file_path, data):
    with open(file_path, 'w') as file:
        for row in data:
            file.write("\n".join(row) + "\n\n")

# データを取得してシートに書き込む関数
def fetch_and_write_data(driver, file_path):
    all_data = []
    for _ in range(5):  # 5週間分のデータを取得
        for day in range(1, 8):  # 各週の7日分のデータを取得
            day_id = f"DAY{day}"
            try:
                day_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, day_id))
                )
                date_text = day_element.find_element(By.CLASS_NAME, "DAYTX").text
                time_slots = day_element.find_elements(By.CLASS_NAME, "KOMASTS8")
                slots = [slot.text if slot.text else slot.find_element(By.TAG_NAME, "img").get_attribute("alt") for slot in time_slots]
                all_data.append([date_text] + slots)
            except Exception as e:
                print(f"An error occurred while processing {day_id}: {e}")
                continue  # エラーが発生した場合でも次の要素に進む
        try:
            next_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#NEXTWEEK"))
            )
            next_element.click()
        except Exception as e:
            print(f"An error occurred while clicking NEXTWEEK: {e}")
            break  # エラーが発生した場合はループを終了
    write_data_to_sheet(file_path, all_data)

# 変更箇所を抽出する関数
def extract_changes(file1, file2):
    lines1 = read_file(file1)
    lines2 = read_file(file2)
    changes = []
    time_slots = ["7-9", "9-11", "11-13", "13-15", "15-17", "17-19", "19-21", "21-23"]
    holidays = ["(土曜日)", "(日曜日)"]
    spesial_holidays = ["10月14日", "11月4日"]

    for i in range(0, len(lines1), 11):  # 11行ごとに処理
        current_date = lines1[i].strip()
        current_day = lines1[i + 1].strip()

        for j in range(8):  # 3行目から10行目までの時間帯を処理
            line1 = lines1[i + 2 + j].strip()
            line2 = lines2[i + 2 + j].strip()

            if line1 != line2 and line2 in ["1", "2", "3", "4"]:
                time_slot = time_slots[j]
                if time_slot in ["19-21"]:
                    time_slot = f"*{time_slot}*"
                if current_day in holidays:
                    current_day = f"*{current_day}*"
                if current_date in spesial_holidays:
                    current_date = f"*{current_date}*"
                changes.append(f"{current_date} {current_day} {time_slot}")

    return changes

# メイン処理
def main():
    try:
        driver.get("https://www.yoyaku-sports.city.suginami.tokyo.jp/w/")
        print(driver.title)
        
        # iframeに移動
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src='https://www.yoyaku-sports.city.suginami.tokyo.jp/reselve/k_index.do']"))
        )
        driver.switch_to.frame(iframe)
        
        # 必要な要素をクリック
        selectors = ["#BB1", "#BB1", "#T3", "#T7", "#T3", "#T1", "#T4"]
        for selector in selectors:
            click_element(driver, selector)
        
        # シート2の内容をシート1にコピー
        sheet_koenji2_content = read_file('sheet_koenji2.txt')
        write_file('sheet_koenji1.txt', sheet_koenji2_content)
        
        # シート2をクリア
        write_file('sheet_koenji2.txt', [])
        
        # データを取得してシートに書き込む
        fetch_and_write_data(driver, 'sheet_koenji2.txt')

        # シート1とシート2の違いを表示
        changes = extract_changes('sheet_koenji1.txt', 'sheet_koenji2.txt')
        if changes:
            message = "*高円寺体育館は以下の時間帯で予約可能になりました:*\n" + "\n".join(changes)
            send_slack_notification(message)
            print(message)
            # 環境変数を設定して、変更があったことを示す
            with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
                env_file.write(f'CHANGES=true\n')
        else:
            with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
                env_file.write(f'CHANGES=false\n')
        
    except Exception as e:
        print(f"An error occurred: {e}")
        with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
            env_file.write(f'CHANGES=false\n')
    finally:
        driver.quit()

# メイン処理の実行
if __name__ == "__main__":
    main()