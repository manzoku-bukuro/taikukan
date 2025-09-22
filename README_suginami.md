# 杉並区体育施設空き状況監視スクリプト

## 概要
杉並区の西荻地域区民センター・勤福会館とセシオン杉並の体育室空き状況を監視し、新しい空きが見つかった場合にSlack通知を送信するスクリプトです。

## 対象施設・時間
- **西荻地域区民センター・勤福会館**: 体育室半面Ａ・Ｂ
- **セシオン杉並**: 体育室全面
- **対象日時**: 土曜日・日曜日・祝日のみ

## 機能
- 新しい空きスロットの検出
- JSONファイルでのデータ永続化
- Slack通知（新スロット発見時）
- 差分検出（新規追加のみ通知、削除は無視）

## 必要な環境
- Python 3.7+
- Google Chrome
- ChromeDriver（webdriver_managerで自動インストール）

## インストール
```bash
pip install selenium requests webdriver-manager
```

## 環境変数
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

## 実行方法

### 単発実行
```bash
python suginami_seshion_nishiogi.py
```

### 定期実行（推奨）
crontabで30分毎に実行:
```bash
# crontab -e で以下を追加
*/30 7-23 * * * cd /path/to/taikukan && python suginami_seshion_nishiogi.py
```

## 出力ファイル
- `suginami_availability.json`: 空き状況データ（自動生成）

## GitHub Actions制限
GitHub Actions環境では杉並区サイトへのアクセスでタイムアウトが発生するため、ローカル環境またはVPSでの実行を推奨します。

## 代替実行環境
1. **ローカルマシン**: 最も確実
2. **VPS**: クラウドサーバーでの定期実行
3. **Raspberry Pi**: 自宅サーバーでの24時間監視

## トラブルシューティング
- ChromeDriverのバージョン不整合: webdriver_managerが自動解決
- サイトアクセスエラー: ネットワーク環境を確認
- Slack通知が届かない: SLACK_WEBHOOK_URL環境変数を確認