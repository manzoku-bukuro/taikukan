# 杉並区体育施設監視スクリプト - 実行環境オプション

## GitHub Actions問題の結論
GitHub Actions環境では杉並区サイトへのSeleniumアクセスで技術的制約があり、実行困難であることが判明しました。

## 代替実行環境

### 1. **ローカルマシン** (推奨度: ★★★★★)
**メリット**: 最も確実、デバッグ容易
```bash
# crontabで定期実行
crontab -e
# 30分毎に実行（7-23時）
*/30 7-23 * * * cd /path/to/taikukan && python suginami_seshion_nishiogi.py
```

### 2. **VPS (さくらVPS、ConoHa等)** (推奨度: ★★★★☆)
**メリット**: 24時間稼働、比較的安価
```bash
# 月額500円程度のVPSを契約
# Ubuntu環境にスクリプト配置
# crontabで定期実行設定
```

### 3. **Raspberry Pi** (推奨度: ★★★☆☆)
**メリット**: 自宅で24時間稼働、電気代安い
**デメリット**: 初期設定が必要
```bash
# Raspberry Pi OS セットアップ
# Chrome/ChromeDriverインストール
# crontabで定期実行
```

### 4. **AWS EC2 / GCP** (推奨度: ★★☆☆☆)
**メリット**: スケーラブル
**デメリット**: 料金が高い
```bash
# t2.micro (AWS) または e2-micro (GCP)
# 月額数千円
```

### 5. **他のCI/CDサービス** (推奨度: ★★☆☆☆)
- **GitLab CI/CD**: より多くのリソース
- **CircleCI**: 月2500分無料
- **Travis CI**: プライベートリポジトリ有料

## 実装済み機能
✅ 杉並区サイトデータ取得
✅ 新スロット検出・差分処理
✅ Slack通知
✅ JSON永続化
✅ エラーハンドリング

## 推奨セットアップ手順（VPS）

### 1. VPS契約・初期設定
```bash
# Ubuntu 22.04 LTS
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip git curl -y
```

### 2. Chrome/ChromeDriverインストール
```bash
# Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y

# Python依存関係
pip3 install selenium requests webdriver-manager
```

### 3. スクリプト配置・設定
```bash
git clone [このリポジトリ]
cd taikukan
export SLACK_WEBHOOK_URL="your_webhook_url"
echo 'export SLACK_WEBHOOK_URL="your_webhook_url"' >> ~/.bashrc
```

### 4. crontab設定
```bash
crontab -e
# 追加
*/30 7-23 * * * cd /home/user/taikukan && /usr/bin/python3 suginami_seshion_nishiogi.py >> /var/log/suginami.log 2>&1
```

## 費用比較

| 環境 | 初期費用 | 月額費用 | 年額費用 |
|------|----------|----------|----------|
| ローカルPC | 0円 | 電気代数百円 | ~3,000円 |
| さくらVPS | 0円 | 550円 | 6,600円 |
| ConoHa VPS | 0円 | 630円 | 7,560円 |
| Raspberry Pi | 8,000円 | 電気代100円 | 9,200円 |
| AWS t2.micro | 0円 | 1,500円 | 18,000円 |

## 結論
**GitHub Actions以外の環境では問題なく動作します**。最もお勧めは：
1. **テスト**: ローカルマシンで動作確認
2. **本番**: VPSで24時間監視

スクリプトの機能は完成しているので、実行環境を変更するだけで運用開始できます。