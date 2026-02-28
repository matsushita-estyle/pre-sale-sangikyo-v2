# デプロイ手順と設定記録

このドキュメントでは、pre-sale-sangikyo-v2 を Azure にデプロイした際の手順と設定内容を記録します。

## 1. インフラ構築 (Terraform)

### リソース作成

```bash
cd /Users/estyle-0170/Environment/test/2026/02/Sangikyo-demo/pre-sale-sangikyo-v2/terraform
terraform init
terraform plan
terraform apply -auto-approve
```

### 作成されたリソース

| リソース | 名前 | 設定 |
|---------|------|------|
| Resource Group | rg_matsushita | 既存リソースグループを使用 |
| App Service Plan | sangikyo-v2-plan | B1 (Linux, 1コア, 1.75GB RAM) |
| App Service | sangikyo-v2-backend | Python 3.11 |
| Static Web App | sangikyo-v2-frontend | Free tier |

### 既存リソースのインポート

リソースグループが既に存在していたため、Terraform state にインポート:

```bash
terraform import azurerm_resource_group.main /subscriptions/b4f2cb18-2f77-447e-919f-530fb768efa2/resourceGroups/rg_matsushita
```

## 2. GitHub Secrets 設定

GitHub リポジトリの **Settings** → **Secrets and variables** → **Actions** で以下を設定:

### 設定した Secrets

| Secret名 | 説明 | 取得方法 |
|----------|------|---------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web Apps のデプロイトークン | `az staticwebapp secrets list --name sangikyo-v2-frontend --resource-group rg_matsushita --query "properties.apiKey" -o tsv` |
| `AZURE_BACKEND_WEBAPP_NAME` | バックエンドの App Service 名 | `sangikyo-v2-backend` |
| `AZURE_BACKEND_PUBLISH_PROFILE` | バックエンドのデプロイ設定 (XML) | `az webapp deployment list-publishing-profiles --name sangikyo-v2-backend --resource-group rg_matsushita --xml` |
| `NEXT_PUBLIC_API_URL` | フロントエンドがバックエンドを呼び出す URL | `https://sangikyo-v2-backend.azurewebsites.net` |

## 3. GitHub へのコード push

```bash
cd /Users/estyle-0170/Environment/test/2026/02/Sangikyo-demo/pre-sale-sangikyo-v2
git init
git add .
git commit -m "Initial commit: Next.js frontend + FastAPI backend with Terraform infrastructure"
git branch -M main
git remote add origin git@github-company:matsushita-estyle/pre-sale-sangikyo-v2.git
git push -u origin main
```

## 4. GitHub Actions ワークフロー修正

### 問題1: フロントエンドデプロイエラー

**エラー内容:**
```
Failed to find a default file in the app artifacts folder (frontend).
Valid default files: index.html,Index.html.
```

**原因:**
`app_location: "/frontend"` としていたため、ビルド済みの `out/` ディレクトリを見つけられなかった。

**修正:**
```yaml
# 修正前
app_location: "/frontend"
output_location: "out"

# 修正後
app_location: "/frontend/out"
output_location: ""
```

### 問題2: 環境変数名の統一

pre-sale-sangikyo との一貫性を保つため、環境変数名を修正:

| 修正前 | 修正後 | 理由 |
|--------|--------|------|
| `BACKEND_URL` | `NEXT_PUBLIC_API_URL` | Next.js の命名規則に準拠 |
| `AZURE_WEBAPP_NAME` | `AZURE_BACKEND_WEBAPP_NAME` | フロント/バックを明確に区別 |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | `AZURE_BACKEND_PUBLISH_PROFILE` | 同上 |

## 5. バックエンド起動設定

### 問題: バックエンドが起動しない

デプロイ後、バックエンドにアクセスすると Azure のデフォルト Welcome ページが表示された。

**原因:**
起動コマンドが設定されていなかった。

**修正:**
```bash
az webapp config set \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app"
```

### Gunicorn の設定

**起動コマンドの意味:**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
         │    └─ ワーカータイプ (ASGI対応のUvicorn)
         └─ ワーカー数 (4プロセス)
```

- **Gunicorn**: Python WSGI/ASGI サーバー、プロセス管理を担当
- **Uvicorn**: ASGI サーバー、FastAPI の実行を担当
- **マルチプロセス**: 4つのワーカーで並列処理、高可用性を実現

**requirements.txt への追加:**
```txt
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
gunicorn>=21.2.0
```

## 6. デプロイ後の確認

### URL

- **フロントエンド**: https://gentle-desert-0a11bfb00.2.azurestaticapps.net
- **バックエンド**: https://sangikyo-v2-backend.azurewebsites.net

### ヘルスチェック

```bash
# バックエンド
curl https://sangikyo-v2-backend.azurewebsites.net/api/health
# {"status":"healthy"}

# フロントエンド
curl https://gentle-desert-0a11bfb00.2.azurestaticapps.net
# Next.js ページが返る
```

## 7. ローカル起動 vs 本番起動

### バックエンド

| 環境 | 起動方法 | 説明 |
|------|---------|------|
| **ローカル** | `python main.py` | Uvicorn 単体 (1プロセス)、開発に最適 |
| **本番** | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app` | マルチプロセス、高可用性 |

### フロントエンド

| 環境 | 起動方法 | 説明 |
|------|---------|------|
| **ローカル** | `npm run dev` | 開発サーバー、ホットリロード有効 |
| **本番** | `npm run build` → 静的ファイル配信 | Azure Static Web Apps で CDN 配信 |

## 8. 今後の拡張に向けて

### 将来必要になる環境変数

sample-sales-agent-demo の機能を移植する際に必要:

```bash
# バックエンド (App Settings)
GEMINI_API_KEY          # Gemini API キー
COSMOS_ENDPOINT         # Cosmos DB エンドポイント
COSMOS_KEY              # Cosmos DB キー
CORS_ORIGINS            # CORS許可オリジン（現在は "*"）
```

### Terraform での管理推奨

起動コマンドも Terraform で管理することを推奨:

```hcl
resource "azurerm_linux_web_app" "backend" {
  # ...

  site_config {
    app_command_line = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app"
    # ...
  }

  app_settings = {
    "GEMINI_API_KEY"   = var.gemini_api_key
    "COSMOS_ENDPOINT"  = var.cosmos_endpoint
    "COSMOS_KEY"       = var.cosmos_key
  }
}
```

## トラブルシューティング

### デプロイログの確認

```bash
# バックエンド
az webapp log deployment show \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita

# App Service の設定確認
az webapp config show \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita
```

### Static Web Apps のログ確認

GitHub Actions の "Build and Deploy Job" タブでログを確認。

## まとめ

✅ Terraform でインフラ構築完了
✅ GitHub Actions で CI/CD パイプライン構築完了
✅ フロントエンド (Static Web Apps) デプロイ成功
✅ バックエンド (App Service B1) デプロイ成功
✅ 環境変数の命名規則を統一
✅ Gunicorn によるマルチプロセス実行設定完了

次のステップ: sample-sales-agent-demo のエージェント機能を移植
