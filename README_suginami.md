# 杉並区施設予約チェック

## 概要

杉並区施設予約システムの空き状況をチェックして通知するシステムです。

## アーキテクチャ

GitHub Actionsから直接アクセスできない問題に対応するため、**ハイブリッドアプローチ**を採用しています。

### 1. ローカル実行（データ取得）

```bash
python check_suginami_local.py
```

- Seleniumで実際に杉並区サイトにアクセス
- 空き状況を取得
- `suginami_availability.json` に結果を保存
- 変更があった場合、Gitコミットを促す

### 2. GitHub Actions（通知）

`suginami_availability.json` がコミットされたら自動実行：

- 前回のデータ（GitHub Issue #2）と比較
- 変更があった場合のみ：
  - Issue #2 を更新
  - Slack通知を送信

## セットアップ

### 必要な環境変数

GitHub Secretsに以下を設定：

- `SLACK_WEBHOOK_URL`: Slack通知用Webhook URL
- `GITHUB_TOKEN`: 自動的に提供される（設定不要）

### ローカル実行の準備

```bash
# 依存関係をインストール
pip install selenium chromedriver-autoinstaller

# ヘッドレスモードで実行（デフォルト）
python check_suginami_local.py

# ブラウザを表示して実行
HEADLESS=false python check_suginami_local.py
```

## ワークフロー

### 定期チェック（手動実行）

1. ローカルで `check_suginami_local.py` を実行
2. 変更があれば `suginami_availability.json` が更新される
3. Gitにコミット＆プッシュ
4. GitHub Actionsが自動的に起動
5. 変更を検知してSlack通知

### Gitコミット例

```bash
git add suginami_availability.json
git commit -m "Update suginami availability - $(date '+%Y-%m-%d %H:%M')"
git push origin master
```

## なぜこのアプローチ？

### 問題点

- 杉並区サイトがGitHub ActionsのIPレンジをブロックしている可能性
- Seleniumでの自動アクセスが失敗する

### 解決策

- **ローカル**: IPブロックされないため、正常にアクセス可能
- **GitHub Actions**: JSONファイルの変更監視と通知のみに特化
- **メリット**: シンプルで確実、失敗しない

## ファイル構成

```
check_suginami_local.py      # ローカル実行用（データ取得）
notify_suginami_changes.py   # GitHub Actions用（通知）
suginami_availability.json   # 空き状況データ
.github/workflows/suginami_notify.yml  # GitHub Actionsワークフロー
```

## トラブルシューティング

### ローカルでアクセスできない

```bash
# ヘッドレスモードを無効化してデバッグ
HEADLESS=false python check_suginami_local.py
```

### GitHub Actionsが動かない

- `suginami_availability.json` がコミットされているか確認
- GitHub Secretsが設定されているか確認
- ワークフローのログを確認

## 今後の拡張

- [ ] 実際の空き枠取得機能を実装
- [ ] 複数施設のサポート
- [ ] 特定の日時の空き状況フィルタリング
- [ ] cronで定期的にローカル実行を促すリマインダー
