#!/usr/bin/env python3
"""
【目的】
杉並区さざんかねっとから西荻地域区民センター・勤福会館の体育室半面Ａの空き状況を取得

【フロー】
1. https://www.shisetsuyoyaku.city.suginami.tokyo.jp/user/Home にアクセス
2. 「集会施設」をクリック → /user/AvailabilityCheckApplySelectFacility に移動
3. 「西荻地域区民センター・勤福会館」をチェック → 次へ進む → /user/AvailabilityCheckApplySelectDays に移動
4. テーブル上の「体育室半面Ａ」の情報を取得
"""

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import re
import time

class SazankaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.shisetsuyoyaku.city.suginami.tokyo.jp"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.csrf_token = None
    
    def get_csrf_token(self):
        """CSRFトークンを取得"""
        print("📄 Step 1: ホームページからCSRFトークン取得")
        response = self.session.get(f"{self.base_url}/user/Home")
        
        if response.status_code != 200:
            print(f"❌ ホームページアクセス失敗: {response.status_code}")
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': '__RequestVerificationToken'})
        
        if csrf_input:
            self.csrf_token = csrf_input.get('value')
            print(f"✅ CSRFトークン取得成功: {self.csrf_token[:20]}...")
            return True
        else:
            print("❌ CSRFトークンが見つかりません")
            return False
    
    def click_meeting_facility(self):
        """集会施設ボタンをクリック"""
        print("\n🖱️ Step 2: 集会施設ボタンクリック")
        
        form_data = {
            'facilityCategoryCode': '1',
            '__RequestVerificationToken': self.csrf_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = self.session.post(
            f"{self.base_url}/user/Home/SearchByFacilityCategory",
            data=form_data,
            headers=headers
        )
        
        if response.status_code == 200:
            redirect_path = response.text.strip()
            print(f"✅ リダイレクトパス取得: {redirect_path}")
            return redirect_path
        else:
            print(f"❌ 集会施設ボタンクリック失敗: {response.status_code}")
            return None
    
    def access_facility_selection(self, redirect_path):
        """施設選択ページにアクセス"""
        print(f"\n📍 Step 3: 施設選択ページアクセス")
        
        # JSONレスポンスのクォートを除去
        redirect_path = redirect_path.strip('"')
        
        # ./AvailabilityCheckApplySelectFacility → /user/AvailabilityCheckApplySelectFacility
        if redirect_path.startswith('./'):
            full_url = f"{self.base_url}/user/{redirect_path[2:]}"
        else:
            full_url = urljoin(self.base_url, redirect_path)
        
        print(f"アクセス先: {full_url}")
        response = self.session.get(full_url)
        
        if response.status_code == 200:
            print("✅ 施設選択ページアクセス成功")
            return response.text
        else:
            print(f"❌ 施設選択ページアクセス失敗: {response.status_code}")
            return None
    
    def select_nishiogi_facility(self, html_content):
        """西荻地域区民センター・勤福会館を選択"""
        print(f"\n☑️ Step 4: 西荻地域区民センター・勤福会館を選択")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        
        target_facility = "西荻地域区民センター・勤福会館"

        # BeautifulSoupでパースした後のテキストで確認（HTMLエンティティがデコードされる）
        soup_text = soup.get_text()
        if target_facility not in soup_text:
            print(f"❌ ページ内に'{target_facility}'が見つかりません")
            # デバッグ: 利用可能な施設を表示
            checkboxes = soup.find_all('b-form-checkbox')
            print("利用可能な施設:")
            for cb in checkboxes:
                print(f"  - {cb.get_text().strip()}")
            return None

        print(f"✅ ページ内に'{target_facility}'が存在します")
        
        # 特定の施設を探す（HTMLから見ると、西荻地域区民センター・勤福会館はindex 1）
        target_checkbox = None
        target_facility_data = None
        
        # b-form-checkboxを探す
        checkboxes = soup.find_all('b-form-checkbox')
        for checkbox in checkboxes:
            checkbox_text = checkbox.get_text().strip()
            if target_facility in checkbox_text:
                print(f"✅ 目標チェックボックス発見: {checkbox_text}")
                
                # v-modelから施設のインデックスを取得
                v_model = checkbox.get('v-model')
                if v_model:
                    # v-model="model.SelectFacilities.Facilities[1].IsChecked" からインデックスを抽出
                    match = re.search(r'Facilities\[(\d+)\]\.IsChecked', v_model)
                    if match:
                        facility_index = int(match.group(1))
                        print(f"✅ 施設インデックス: {facility_index}")
                        
                        # 対応するhidden inputsを探す
                        target_checkbox = checkbox
                        target_facility_data = {
                            'index': facility_index,
                            'checkbox_name': f'SelectFacilities.Facilities[{facility_index}].IsChecked',
                            'value_name': f'SelectFacilities.Facilities[{facility_index}].SelectedFacility.Value',
                            'text_name': f'SelectFacilities.Facilities[{facility_index}].SelectedFacility.Text'
                        }
                        break
        
        if not target_facility_data:
            print(f"❌ {target_facility}のチェックボックスが見つかりません")
            return None
        
        # フォームデータを準備
        form_data = {
            '__RequestVerificationToken': self.csrf_token
        }
        
        # 全ての hidden input を収集
        all_inputs = soup.find_all('input')
        for inp in all_inputs:
            input_name = inp.get('name')
            input_value = inp.get('value')
            input_type = inp.get('type')
            
            if input_name and input_value is not None:
                if input_type == 'hidden' and input_name != '__RequestVerificationToken':
                    form_data[input_name] = input_value
                elif input_type == 'checkbox':
                    # 全てのチェックボックスをfalseに設定
                    if '.IsChecked' in input_name:
                        form_data[input_name] = 'false'
        
        # 目標の施設をチェック状態にする
        form_data[target_facility_data['checkbox_name']] = 'true'
        
        print(f"📝 フォームデータ準備完了: {len(form_data)}項目")
        print(f"チェック対象: {target_facility_data['checkbox_name']} = true")
        
        # Next ボタンの処理をエミュレート
        response = self.session.post(
            f"{self.base_url}/user/AvailabilityCheckApplySelectFacility/Next",
            data=form_data
        )
        
        if response.status_code == 200:
            try:
                # レスポンスがJSONの場合
                result = response.json()
                if result.get('Result') == 'Ok':
                    next_url = result.get('Information')
                    print(f"✅ 施設選択成功、次のURL: {next_url}")
                    
                    # 次のページにアクセス
                    if next_url.startswith('./'):
                        next_url = f"{self.base_url}/user/{next_url[2:]}"
                    elif not next_url.startswith('http'):
                        next_url = f"{self.base_url}{next_url}"
                    
                    next_response = self.session.get(next_url)
                    if next_response.status_code == 200:
                        return next_response.text
                    else:
                        print(f"❌ 次のページアクセス失敗: {next_response.status_code}")
                        return None
                else:
                    print(f"❌ サーバーエラー: {result.get('Information')}")
                    return None
            except json.JSONDecodeError:
                print("✅ 施設選択送信成功（HTMLレスポンス）")
                return response.text
        else:
            print(f"❌ 施設選択送信失敗: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
    
    def call_search_condition_api(self, html_content):
        """SearchCondition APIで週末・祝日に絞り込み"""
        print(f"\n🔍 Step 5: SearchCondition APIで週末・祝日絞り込み")

        soup = BeautifulSoup(html_content, 'html.parser')

        # フォームデータを準備
        form_data = {
            '__RequestVerificationToken': self.csrf_token
        }

        # 全ての hidden input を収集
        all_inputs = soup.find_all('input')
        for inp in all_inputs:
            input_name = inp.get('name')
            input_value = inp.get('value')
            input_type = inp.get('type')

            if input_name and input_value is not None and input_type == 'hidden':
                if input_name != '__RequestVerificationToken':  # 既に設定済み
                    form_data[input_name] = input_value

        # 検索条件を設定（1ヶ月、土曜・日曜・祝日のみ）
        form_data.update({
            'SearchCondition.StartDate': '2025-09-21',
            'SearchCondition.DisplayTerm': '4',  # 1ヶ月
            'SearchCondition.DisplayCalendar': '0',  # 横表示
            'SearchCondition.TimeZone': '0',  # 全日
        })

        # 土曜・日曜・祝日の設定
        # WeekdayCode: 6=土曜, 7=日曜, 8=祝日
        weekends_and_holidays = ['6', '7', '8']
        for i, week_value in enumerate(weekends_and_holidays):
            form_data[f'weeks[{i}]'] = week_value

        # その他の曜日もフォームに含める（チェックなしの状態で）
        form_data['SearchCondition.Week'] = weekends_and_holidays

        print(f"📝 検索条件設定:")
        print(f"  期間: 1ヶ月")
        print(f"  対象曜日: 土曜・日曜・祝日")
        print(f"  総パラメータ数: {len(form_data)}項目")

        # SearchCondition APIを呼び出し
        api_url = f"{self.base_url}/user/AvailabilityCheckApplySelectDays/SearchCondition"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }

        response = self.session.post(api_url, data=form_data, headers=headers)

        if response.status_code == 200:
            try:
                api_result = response.json()
                print(f"✅ SearchCondition API呼び出し成功")


                # レスポンス構造の確認
                if isinstance(api_result, list) and len(api_result) >= 2:
                    result_status = api_result[0]
                    if result_status.get('Result') == 'Ok':
                        print(f"✅ 検索条件設定成功")
                        availability_data = api_result[1]
                        return availability_data
                    else:
                        print(f"❌ SearchCondition APIエラー: {result_status.get('Information')}")
                        return None
                else:
                    print(f"❌ 予期しないレスポンス形式: {type(api_result)}")
                    return None

            except json.JSONDecodeError as e:
                print(f"❌ SearchCondition APIレスポンスのJSON解析失敗: {e}")
                print(f"Response text: {response.text[:500]}")
                return None
        else:
            print(f"❌ SearchCondition API呼び出し失敗: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    def call_get_availability_api(self, html_content):
        """GetAvailability APIを直接呼び出して体育室情報を取得"""
        print(f"\n🏃 Step 6: GetAvailability API呼び出し")

        soup = BeautifulSoup(html_content, 'html.parser')

        # フォームデータを準備
        form_data = {
            '__RequestVerificationToken': self.csrf_token
        }

        # 全ての hidden input を収集
        all_inputs = soup.find_all('input')
        for inp in all_inputs:
            input_name = inp.get('name')
            input_value = inp.get('value')
            input_type = inp.get('type')

            if input_name and input_value is not None and input_type == 'hidden':
                if input_name != '__RequestVerificationToken':  # 既に設定済み
                    form_data[input_name] = input_value

        # 検索条件を設定（1ヶ月、土曜・日曜・祝日のみ）
        form_data.update({
            'SearchCondition.StartDate': '2025-09-21',
            'SearchCondition.DisplayTerm': '4',  # 1ヶ月
            'SearchCondition.DisplayCalendar': '0',  # 横表示
            'SearchCondition.TimeZone': '0',  # 全日
        })

        # 土曜・日曜・祝日の設定
        weekends_and_holidays = ['6', '7', '8']
        for i, week_value in enumerate(weekends_and_holidays):
            form_data[f'weeks[{i}]'] = week_value

        form_data['SearchCondition.Week'] = weekends_and_holidays

        print(f"📝 APIリクエストデータ準備完了: {len(form_data)}項目")

        # GetAvailability APIを呼び出し
        api_url = f"{self.base_url}/user/AvailabilityCheckApplySelectDays/GetAvailability"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }

        response = self.session.post(api_url, data=form_data, headers=headers)

        if response.status_code == 200:
            try:
                api_result = response.json()
                print(f"✅ GetAvailability API呼び出し成功")


                if isinstance(api_result, list) and len(api_result) >= 3:
                    # 体育室情報を解析
                    return self.parse_gym_info_from_api_response(api_result)
                else:
                    print(f"❌ 予期しないレスポンス形式: {type(api_result)}")
                    return None

            except json.JSONDecodeError as e:
                print(f"❌ APIレスポンスのJSON解析失敗: {e}")
                print(f"Response text: {response.text[:500]}")
                return None
        else:
            print(f"❌ GetAvailability API呼び出し失敗: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    def parse_gym_info_from_api_response(self, api_result):
        """APIレスポンスから体育室半面Ａの情報を解析"""
        print(f"\n📋 体育室半面Ａの情報解析開始")

        gym_info = []
        target_room = "体育室半面Ａ"

        # AvailabilityDaysデータを解析
        availability_data = api_result[0]

        # 横表示データがある場合
        if 'Horizontal' in availability_data and availability_data['Horizontal']:
            horizontal_data = availability_data['Horizontal']

            for facility in horizontal_data:
                # Common内の情報を取得
                common = facility.get('Common', {})
                facility_name = common.get('FacilityName', '')

                if '西荻' in facility_name:
                    # Rows内の部屋を確認
                    if 'Rows' in common:
                        for room in common['Rows']:
                            room_name = room.get('Name', '')
                            if target_room in room_name:

                                # Cells内の日別データを取得
                                if 'Cells' in room:
                                    for cell in room['Cells']:
                                        use_date = cell.get('UseDate', '')
                                        weekday_code = cell.get('WeekdayCode', '')
                                        vacant_status = cell.get('VacantStatus', '')
                                        display_status = cell.get('DisplayStatusForUser', '')
                                        is_enabled = cell.get('IsEnabledForUser', False)
                                        is_closed = cell.get('IsClosed', False)
                                        is_holiday = cell.get('IsHoliday', False)

                                        # 日付をフォーマット
                                        if use_date:
                                            from datetime import datetime
                                            date_obj = datetime.fromisoformat(use_date.replace('T00:00:00', ''))
                                            formatted_date = date_obj.strftime('%Y-%m-%d')
                                            day_of_week = ['月', '火', '水', '木', '金', '土', '日'][weekday_code - 1]
                                        else:
                                            formatted_date = use_date
                                            day_of_week = str(weekday_code)

                                        gym_info.append({
                                            'facility': facility_name,
                                            'room': room_name,
                                            'date': formatted_date,
                                            'day_of_week': day_of_week,
                                            'vacant_status': vacant_status,
                                            'display_status': display_status,
                                            'is_enabled': is_enabled,
                                            'is_closed': is_closed,
                                            'is_holiday': is_holiday,
                                            'raw_data': cell
                                        })
                            else:
                                # 体育室関連かチェック（デバッグ用情報は削除）
                                pass

        if gym_info:
            print(f"✅ {target_room}の情報: {len(gym_info)}件取得")
            return gym_info
        else:
            print(f"❌ {target_room}の情報が見つかりません")

            return None

    def extract_all_form_fields_from_html(self, html_content):
        """HTMLから全ての隠しフィールドを抽出してフォームデータを構築"""
        print(f"\n📅 Step 7: HTMLから全フォームフィールドを抽出")

        soup = BeautifulSoup(html_content, 'html.parser')
        form_data = {
            '__RequestVerificationToken': self.csrf_token,
            'SearchCondition.StartDate': '2025-09-21',
            'SearchCondition.DisplayTerm': '4',
            'SearchCondition.DisplayCalendar': '0',
            'SearchCondition.TimeZone': '0',
        }

        # 週末・祝日設定
        weekends_and_holidays = ['6', '7', '8']
        for i, week_value in enumerate(weekends_and_holidays):
            form_data[f'weeks[{i}]'] = week_value
        form_data['SearchCondition.Week'] = weekends_and_holidays

        # 全てのhidden inputを抽出
        hidden_inputs = soup.find_all('input', {'type': 'hidden'})
        for hidden_input in hidden_inputs:
            name = hidden_input.get('name')
            value = hidden_input.get('value', '')

            if name and name != '__RequestVerificationToken':
                # デフォルトでFalseに設定
                if 'IsChecked' in name:
                    form_data[name] = 'false'
                else:
                    form_data[name] = value

        print(f"📝 HTMLから{len(hidden_inputs)}個の隠しフィールドを抽出")
        return form_data

    def select_available_days_html_approach(self, gym_info, html_content):
        """HTMLから抽出したフォームフィールドで日付選択を試行"""
        print(f"\n🎯 Step 7: HTMLベースアプローチで日付選択")

        if not gym_info:
            print("❌ 体育室情報がないため、処理をスキップします")
            return None

        # vacant_status='some'の日を抽出
        available_days = [info for info in gym_info if info['vacant_status'] == 'some']

        if not available_days:
            print("❌ 空きのある日（vacant_status='some'）が見つかりません")
            return None

        print(f"✅ 空きのある日: {len(available_days)}件発見")
        for day in available_days:
            print(f"  - {day['date']} ({day['day_of_week']})")

        # 最新のHTMLを取得
        current_response = self.session.post(
            f"{self.base_url}/user/AvailabilityCheckApplySelectDays/GetAvailability",
            data={
                '__RequestVerificationToken': self.csrf_token,
                'SearchCondition.StartDate': '2025-09-21',
                'SearchCondition.DisplayTerm': '4',
                'SearchCondition.DisplayCalendar': '0',
                'SearchCondition.TimeZone': '0',
                'weeks[0]': '6', 'weeks[1]': '7', 'weeks[2]': '8',
                'SearchCondition.Week': ['6', '7', '8']
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            }
        )

        if current_response.status_code == 200:
            current_data = current_response.json()
            if len(current_data) >= 3:
                current_html = current_data[2]
                with open('latest_availability.html', 'w', encoding='utf-8') as f:
                    f.write(current_html)
                print("💾 最新HTMLをlatest_availability.htmlに保存")
            else:
                current_html = html_content
        else:
            current_html = html_content

        # フォームデータを構築
        form_data = self.extract_all_form_fields_from_html(current_html)

        # 体育室半面Ａ（行25）の利用可能日のチェックボックスをtrueに設定
        selected_count = 0

        # 9/23, 9/27, 9/28のセルインデックス（推定）
        # 9/21=0, 9/23=1, 9/27=2, 9/28=3
        target_dates_cells = {
            '2025-09-23': 1,
            '2025-09-27': 2,
            '2025-09-28': 3
        }

        for day_info in available_days:
            target_date = day_info['date']
            if target_date in target_dates_cells:
                cell_index = target_dates_cells[target_date]
                checkbox_field = f'Horizontal[0].Common.Rows[25].Cells[{cell_index}].IsChecked'

                if checkbox_field in form_data:
                    form_data[checkbox_field] = 'true'
                    selected_count += 1
                    print(f"  ✅ 選択: {target_date} (セル{cell_index}: {checkbox_field})")
                else:
                    print(f"  ⚠️ フィールドが見つかりません: {checkbox_field}")

        if selected_count == 0:
            print("❌ チェックボックスの選択に失敗しました")
            # 体育室半面Ａの任意のセルを強制選択
            force_field = 'Horizontal[0].Common.Rows[25].Cells[1].IsChecked'
            if force_field in form_data:
                form_data[force_field] = 'true'
                selected_count = 1
                print(f"  🧪 強制選択: {force_field}")

        print(f"📝 HTMLベースフォームデータ準備完了: {len(form_data)}項目")
        print(f"選択された日数: {selected_count}日")

        # privateTokenを設定
        form_data['privateToken'] = ''

        # Next APIを呼び出し
        api_url = f"{self.base_url}/user/AvailabilityCheckApplySelectDays/Next"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
        }

        response = self.session.post(api_url, data=form_data, headers=headers)

        if response.status_code == 200:
            print(f"✅ Next API呼び出し成功")

            try:
                api_result = json.loads(response.text)

                if isinstance(api_result, str):
                    api_result = json.loads(api_result)

                with open('html_approach_response.json', 'w', encoding='utf-8') as f:
                    json.dump(api_result, f, ensure_ascii=False, indent=2)
                print("💾 HTMLアプローチのレスポンスをhtml_approach_response.jsonに保存")

                if isinstance(api_result, dict) and api_result.get('Result') == 'Ok':
                    info = api_result.get('Information', '')
                    if isinstance(info, dict):
                        next_url = info.get('MessageId', '')
                    else:
                        next_url = str(info)
                    print(f"✅ 次ページ遷移成功: {next_url}")
                    return self.access_select_time_page(next_url)
                else:
                    error_info = api_result.get('Information', {})
                    error_msg = error_info.get('MessageId', str(error_info)) if isinstance(error_info, dict) else str(error_info)
                    print(f"❌ HTMLアプローチエラー: {error_msg}")
                    return None

            except json.JSONDecodeError:
                print("📄 HTMLレスポンスを受信")
                return response.text
        else:
            print(f"❌ Next API呼び出し失敗: {response.status_code}")
            return None


    def access_select_time_page(self, next_url):
        """SelectTimeページにアクセスしてHTMLを保存"""
        print(f"\n⏰ Step 8: SelectTimeページアクセス")

        # URLの正規化
        if next_url.startswith('./'):
            full_url = f"{self.base_url}/user/{next_url[2:]}"
        elif not next_url.startswith('http'):
            full_url = f"{self.base_url}/user/{next_url}"
        else:
            full_url = next_url

        print(f"アクセス先: {full_url}")

        response = self.session.get(full_url)

        if response.status_code == 200:
            print("✅ SelectTimeページアクセス成功")

            # HTMLを保存
            with open('select_time_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 HTMLをselect_time_page.htmlに保存しました")

            # ページタイトルを確認
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            if title:
                print(f"ページタイトル: {title.text.strip()}")

            # 時間帯情報を取得
            time_slots = self.get_available_time_slots(response.text)
            if time_slots:
                print(f"✅ 空き時間帯: {len(time_slots)}件取得")
                # 時間帯情報を保存
                with open('available_time_slots.json', 'w', encoding='utf-8') as f:
                    json.dump(time_slots, f, ensure_ascii=False, indent=2)
                print("💾 時間帯情報をavailable_time_slots.jsonに保存")
            else:
                print("❌ 時間帯情報の取得に失敗")

            return response.text
        else:
            print(f"❌ SelectTimeページアクセス失敗: {response.status_code}")
            return None

    def get_available_time_slots(self, html_content):
        """時間帯選択ページから実際の空き時間情報を抽出"""
        print(f"\n🕰 時間帯情報と空き状況を解析中...")

        soup = BeautifulSoup(html_content, 'html.parser')
        import re

        # 1. 隠しフィールドから時間帯情報を取得
        time_slot_inputs = soup.find_all('input', {'name': re.compile(r'AvailabilityTime\..*')})
        if not time_slot_inputs:
            print("❌ 時間帯関連の隠しフィールドが見つかりません")
            return None

        print(f"✅ {len(time_slot_inputs)}個の時間帯フィールドを発見")

        # 2. SVGアイコンから空き状況を取得
        # 空きあり: circleアイコン
        # 空きなし: times-solidアイコン
        available_icons = soup.find_all('use', {'xlink:href': re.compile(r'.*#circle$')})
        unavailable_icons = soup.find_all('use', {'xlink:href': re.compile(r'.*#times-solid$')})

        print(f"✅ 空きありアイコン: {len(available_icons)}個")
        print(f"✅ 空きなしアイコン: {len(unavailable_icons)}個")

        # 3. 時間帯データを構築
        time_cells = {}
        for input_field in time_slot_inputs:
            name = input_field.get('name', '')
            value = input_field.get('value', '')

            cell_match = re.match(r'AvailabilityTime\.FacilityList\[(\d+)\]\.Days\[(\d+)\]\.DisplayRows\[(\d+)\]\.DisplayCells\[(\d+)\]\.(\w+)', name)
            if cell_match:
                facility_idx, day_idx, row_idx, cell_idx, field_name = cell_match.groups()
                cell_key = f"{facility_idx}_{day_idx}_{row_idx}_{cell_idx}"

                if cell_key not in time_cells:
                    time_cells[cell_key] = {
                        'facility_idx': facility_idx,
                        'day_idx': day_idx,
                        'row_idx': row_idx,
                        'cell_idx': cell_idx
                    }
                time_cells[cell_key][field_name] = value

        # 4. 空き状況をマッピング
        availability_map = self.detect_availability_from_icons(soup)

        # 5. 時間スロット情報を解析
        time_slots = []
        for cell_key, cell_data in time_cells.items():
            if 'TimeFrom' in cell_data and 'TimeTo' in cell_data:
                time_from = int(cell_data.get('TimeFrom', 0))
                time_to = int(cell_data.get('TimeTo', 0))
                is_checked = cell_data.get('IsChecked', 'False').lower() == 'true'

                start_time = f"{time_from // 100:02d}:{time_from % 100:02d}"
                end_time = f"{time_to // 100:02d}:{time_to % 100:02d}"

                # 空き状況を判定
                is_available = availability_map.get(cell_key, False)

                time_slot = {
                    'facility_idx': cell_data['facility_idx'],
                    'day_idx': cell_data['day_idx'],
                    'row_idx': cell_data['row_idx'],
                    'cell_idx': cell_data['cell_idx'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'time_from': time_from,
                    'time_to': time_to,
                    'is_checked': is_checked,
                    'is_available': is_available,
                    'status_times': cell_data.get('StatusTimes', ''),
                    'total_quantity': cell_data.get('TotalQuantity', ''),
                    'reservation_used_quantity': cell_data.get('ReservationUsedQuantity', ''),
                    'is_extend_frame': cell_data.get('IsExtendFrame', 'False').lower() == 'true',
                    'form_field_name': f"AvailabilityTime.FacilityList[{cell_data['facility_idx']}].Days[{cell_data['day_idx']}].DisplayRows[{cell_data['row_idx']}].DisplayCells[{cell_data['cell_idx']}].IsChecked"
                }

                time_slots.append(time_slot)

                status_text = "空きあり" if is_available else "空きなし"
                if is_available:
                    print(f"  ✅ {start_time}-{end_time} (日{cell_data['day_idx']}, セル{cell_data['cell_idx']}) - {status_text}")

        # 時間順でソート
        time_slots.sort(key=lambda x: (x['day_idx'], x['time_from']))

        # 空きありの時間帯のみをフィルタリング
        available_slots = [slot for slot in time_slots if slot['is_available']]

        print(f"✅ 総計{len(time_slots)}個の時間スロットを取得")
        print(f"✅ そのうち{len(available_slots)}個が空きあり")

        return available_slots

    def detect_availability_from_icons(self, soup):
        """アイコンから空き状況を検出してマッピングを作成"""
        import re
        availability_map = {}

        # circleアイコン（空きあり）を探す
        circle_icons = soup.find_all('use', {'xlink:href': re.compile(r'.*#circle$')})

        for icon in circle_icons:
            # アイコンの親要素をたどってセル情報を特定
            cell_info = self.extract_cell_info_from_icon(icon)
            if cell_info:
                availability_map[cell_info] = True
                print(f"  🟢 空きあり検出: {cell_info}")

        return availability_map

    def extract_cell_info_from_icon(self, icon_element):
        """アイコン要素からセル情報を抽出"""
        # SVGアイコンの周囲HTMLからセル情報を取得
        # HTML構造: <label>の:class属性にDisplayCells[X]が含まれている

        # 親要素のlabelを探す
        label_parent = icon_element.find_parent('label')
        if not label_parent:
            return None

        # labelの:class属性からセル情報を抽出
        class_attr = label_parent.get(':class', '')

        import re
        # :class属性からDisplayCells[X]を抽出
        # 例: {active:$data.model.AvailabilityTime.FacilityList[0].Days[0].DisplayRows[0].DisplayCells[6].IsChecked, disabled:!isEnabled}
        cell_match = re.search(r'AvailabilityTime\.FacilityList\[(\d+)\]\.Days\[(\d+)\]\.DisplayRows\[(\d+)\]\.DisplayCells\[(\d+)\]', class_attr)

        if cell_match:
            facility_idx, day_idx, row_idx, cell_idx = cell_match.groups()
            return f"{facility_idx}_{day_idx}_{row_idx}_{cell_idx}"

        return None



    def run(self):
        """メイン実行"""
        print("🚀 さざんかねっと体育室情報取得開始")
        print("=" * 50)
        
        # Step 1: CSRFトークン取得
        if not self.get_csrf_token():
            return None
        
        # Step 2: 集会施設ボタンクリック
        redirect_path = self.click_meeting_facility()
        if not redirect_path:
            return None
        
        # Step 3: 施設選択ページアクセス
        facility_page = self.access_facility_selection(redirect_path)
        if not facility_page:
            return None
        
        # Step 4: 西荻地域区民センター・勤福会館選択
        days_page = self.select_nishiogi_facility(facility_page)
        if not days_page:
            return None
        
        # Step 5: SearchCondition APIで週末・祝日に絞り込み
        search_result = self.call_search_condition_api(days_page)
        if not search_result:
            print("❌ 検索条件設定に失敗しました")
            return None

        # Step 6: GetAvailability APIで絞り込み後の体育室情報取得
        gym_info = self.call_get_availability_api(days_page)

        # Step 7: HTMLベースアプローチで日付選択を試行
        select_time_html = self.select_available_days_html_approach(gym_info, days_page)

        print("\n🏁 実行完了")
        return {'gym_info': gym_info, 'time_page_html': select_time_html}

def main():
    scraper = SazankaScraper()
    result = scraper.run()
    
    if result:
        print(f"\n✅ 成功: {len(result)}件の情報を取得")
        # 結果をJSONで保存
        with open('gym_availability_weekends_holidays.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("💾 結果をgym_availability_weekends_holidays.jsonに保存しました")
    else:
        print("\n❌ 情報取得に失敗しました")

if __name__ == "__main__":
    main()