# GitHub Secrets 設定手順

GitHubリポジトリの **Settings** → **Secrets and variables** → **Actions** で以下のSecretsを設定してください。

## 必要なSecrets

### 1. AZURE_STATIC_WEB_APPS_API_TOKEN

フロントエンド（Static Web Apps）のデプロイに使用。

**値:**
```
bf62c3376df8617a746854f067f881c92ca42622efb5b4221b88005cb0b2756302-f2294582-2d24-40db-b243-c0a78c928bb800019080a11bfb00
```

### 2. AZURE_BACKEND_WEBAPP_NAME

バックエンド（App Service）の名前。

**値:**
```
sangikyo-v2-backend
```

### 3. AZURE_BACKEND_PUBLISH_PROFILE

バックエンド（App Service）のPublish Profile（XML形式）。

**取得コマンド:**
```bash
az webapp deployment list-publishing-profiles \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --xml
```

**値:** 上記コマンドの出力全体をコピー（XML形式）

### 4. NEXT_PUBLIC_API_URL

フロントエンド（Next.js）がバックエンドAPIを呼び出すURL。

**値:**
```
https://sangikyo-v2-backend.azurewebsites.net
```

## 設定完了後

GitHubにpushすると自動デプロイが開始されます:

```bash
cd /Users/estyle-0170/Environment/test/2026/02/Sangikyo-demo/pre-sale-sangikyo-v2
git add .
git commit -m "Add Azure infrastructure and applications"
git push origin main
```

## デプロイ後のURL

- **フロントエンド**: https://gentle-desert-0a11bfb00.2.azurestaticapps.net
- **バックエンド**: https://sangikyo-v2-backend.azurewebsites.net
