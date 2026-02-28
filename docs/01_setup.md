# セットアップガイド

## 前提条件

- Azure CLI インストール済み
- Terraform インストール済み
- GitHub アカウント
- Node.js 18+ インストール済み
- Python 3.11+ インストール済み

## 1. Azureリソースの作成（Terraform）

### 1.1 Azure CLIでログイン

```bash
az login
az account set --subscription <your-subscription-id>
```

### 1.2 Terraformでリソース作成

```bash
cd terraform

# 初期化
terraform init

# プラン確認
terraform plan

# リソース作成
terraform apply
```

### 1.3 出力値を確認

```bash
# フロントエンドのAPI Token取得（GitHub Secretsに設定）
terraform output -raw frontend_api_key

# バックエンドURL取得（GitHub Secretsに設定）
terraform output backend_url

# バックエンドのPublish Profile取得
terraform output -raw backend_publish_profile_command
```

上記コマンドを実行してPublish Profileを取得:

```bash
az webapp deployment list-publishing-profiles \
  --name sangikyo-v2-backend \
  --resource-group rg-sangikyo-v2 \
  --xml
```

## 2. GitHub Secrets設定

GitHubリポジトリの Settings → Secrets and variables → Actions で以下を設定:

| Secret Name | 値 | 取得方法 |
|-------------|-----|----------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | `terraform output -raw frontend_api_key` | Terraformから |
| `AZURE_WEBAPP_NAME` | `sangikyo-v2-backend` | Terraformから |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Publish Profileの内容（XML） | Azure CLIから |
| `BACKEND_URL` | `https://sangikyo-v2-backend.azurewebsites.net` | Terraformから |

## 3. ローカル開発

### 3.1 バックエンド起動

```bash
cd backend

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 起動
python main.py
```

→ http://localhost:8000 で確認

### 3.2 フロントエンド起動

```bash
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

→ http://localhost:3000 で確認

## 4. デプロイ

### 4.1 GitHubにプッシュ

```bash
git add .
git commit -m "Initial commit: Next.js + FastAPI"
git push origin main
```

### 4.2 GitHub Actionsで自動デプロイ

- フロントエンド: `.github/workflows/frontend-deploy.yml`
- バックエンド: `.github/workflows/backend-deploy.yml`

GitHub Actionsタブで進捗確認。

### 4.3 デプロイ確認

```bash
# フロントエンドURL確認
terraform output frontend_url

# バックエンドURL確認
terraform output backend_url
```

ブラウザでアクセスして動作確認。

## 5. トラブルシューティング

### バックエンドが起動しない

```bash
# Azure App Serviceのログ確認
az webapp log tail --name sangikyo-v2-backend --resource-group rg-sangikyo-v2
```

### フロントエンドがバックエンドに接続できない

1. GitHub Secretsの`BACKEND_URL`が正しいか確認
2. バックエンドのCORS設定を確認（`backend/main.py`）
3. 再デプロイ:

```bash
# 手動でワークフローを再実行
# GitHub → Actions → 該当ワークフロー → Re-run all jobs
```

### Terraform apply失敗

```bash
# リソース名が重複している場合
# terraform/variables.tf の project_name を変更
```

## 6. リソース削除

使わなくなったら削除:

```bash
cd terraform
terraform destroy
```

## 次のステップ

- [エージェント実装](./agent_implementation.md)（予定）
- [SSE実装](./sse_implementation.md)（予定）
