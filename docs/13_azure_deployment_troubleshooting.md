# Azure App Service デプロイ トラブルシューティング記録

## 概要

2026年2月28日、Azure App ServiceへのFastAPIバックエンドデプロイ時に発生した問題と解決方法を記録します。

---

## 問題の経緯

### 初期状態
- **ローカル環境**: 正常動作 ✅
- **Azure環境**: Application Error / Internal Server Error (500) ❌

### 症状
全てのエンドポイントで500エラーが発生:
- `GET /` → Internal Server Error
- `GET /api/health` → Internal Server Error
- `GET /api/v1/users` → Internal Server Error
- `POST /api/v1/copilot/chat` → Internal Server Error

---

## 原因の特定

### 1. 初期調査

**ログから判明した問題**:
```
2026-02-28T20:31:52.8785176Z Error: can't chdir to 'backend'
```

**原因**: Startup commandの `--chdir backend` が失敗していた
- Azureのビルドプロセスは `/tmp/` の一時ディレクトリでアプリを展開
- `backend` サブディレクトリへのchdirが不可能

**対処**: Startup commandから `--chdir backend` を削除
```bash
az webapp config set --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --startup-file "gunicorn --bind 0.0.0.0 --timeout 600 main:app"
```

### 2. 根本原因の発見

Application Errorは継続。さらに詳細なログを確認:

```
2026-02-28T20:35:49.9682207Z WARNING: Could not find virtual environment directory /home/site/wwwroot/antenv.
2026-02-28T20:35:49.973591Z WARNING: Could not find package directory /home/site/wwwroot/__oryx_packages__.
2026-02-28T20:35:56.6530942Z [2026-02-28 20:35:56 +0000] [1891] [INFO] Using worker: sync
2026-02-28T20:35:56.8652334Z [2026-02-28 20:35:56 +0000] [1892] [ERROR] Exception in worker process
```

**根本原因**:
1. **Oryxビルドが実行されていない** → 依存関係がインストールされていない
2. **sync workerを使用** → FastAPIの非同期処理に対応していない

### 3. 解決策の実施

#### ステップ1: `.deployment` ファイル作成

プロジェクトルートに `.deployment` ファイルを作成し、`backend` をプロジェクトルートに指定:

```ini
[config]
project = backend
```

#### ステップ2: Oryxビルドを有効化

Azure App Settingsでビルドプロセスを有効化:

```bash
az webapp config appsettings set \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT="true" ENABLE_ORYX_BUILD="true"
```

**重要な環境変数**:
- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`: デプロイ時にビルドを実行
- `ENABLE_ORYX_BUILD=true`: Oryxビルドシステムを有効化

#### ステップ3: Startup Commandの最適化

Uvicorn workerを使用するようstartup commandを変更:

```bash
az webapp config set \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0 --timeout 600"
```

**パラメータ説明**:
- `-w 4`: ワーカープロセス数
- `-k uvicorn.workers.UvicornWorker`: FastAPIの非同期処理に対応したワーカー
- `--bind=0.0.0.0`: 全てのインターフェースでリッスン
- `--timeout 600`: リクエストタイムアウトを600秒に設定（AI処理に対応）

#### ステップ4: 空コミットでビルドをトリガー

```bash
git commit --allow-empty -m "Trigger Azure rebuild with Oryx build enabled"
git push
```

---

## 結果

### ✅ 解決後の状態

全てのエンドポイントが正常に動作:

```bash
# ルートエンドポイント
curl https://sangikyo-v2-backend.azurewebsites.net/
# → {"message":"Hello World from FastAPI!","service":"Sangikyo V2 Backend","status":"running"}

# ユーザー一覧
curl https://sangikyo-v2-backend.azurewebsites.net/api/v1/users
# → [{"user_id":"1","name":"山田太郎",...}, ...]

# AI Chat
curl -X POST https://sangikyo-v2-backend.azurewebsites.net/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1","query":"こんにちは"}'
# → {"response":"こんにちは。お問い合わせありがとうございます。..."}
```

### デプロイ後の正常なログ

```
Found build manifest file at '/home/site/wwwroot/oryx-manifest.toml'. Deserializing it...
Build Operation ID: e56e3763bb791a2d
Oryx Version: 0.2.20260130.1
Using packages from virtual environment antenv located at /tmp/8de77060a0d1add/antenv.
[INFO] Starting gunicorn 24.1.1
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: uvicorn.workers.UvicornWorker
```

---

## 教訓・ベストプラクティス

### 1. Azureデプロイの必須設定

FastAPIアプリをAzure App Serviceにデプロイする際は、必ず以下を設定:

1. **`.deployment` ファイル**でプロジェクトルートを指定
2. **App Settings**でビルド環境変数を設定:
   - `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
   - `ENABLE_ORYX_BUILD=true`
3. **Startup Command**でUvicorn workerを指定

### 2. トラブルシューティングの手順

1. **Azure Log Stream**で詳細なエラーログを確認
   - Azure Portal → App Service → Log stream
   - または `az webapp log tail --name <app-name> --resource-group <rg-name>`

2. **デプロイログ**でビルドプロセスを確認
   ```bash
   az webapp log deployment show --name <app-name> --resource-group <rg-name>
   ```

3. **環境変数**が正しく設定されているか確認
   ```bash
   az webapp config appsettings list --name <app-name> --resource-group <rg-name>
   ```

### 3. ローカルとAzure環境の違い

| 項目 | ローカル環境 | Azure環境 |
|------|------------|----------|
| 環境変数 | `.env` ファイル | App Settings |
| 依存関係 | `pip install -r requirements.txt` | Oryxビルド |
| Webサーバー | `uvicorn main:app` | `gunicorn -k uvicorn.workers.UvicornWorker` |
| プロジェクト構造 | `backend/` ディレクトリから実行 | `.deployment` でルートを指定 |

### 4. 重要な注意事項

- **ローカルで動作しても、Azureで動作するとは限らない**
- **ビルドプロセスが正しく実行されているか必ず確認**
- **sync workerではFastAPIの非同期処理は動作しない**
- **環境変数はApp Settingsで設定（.envファイルは使用されない）**

---

## 設定ファイルの最終状態

### `.deployment`
```ini
[config]
project = backend
```

### `requirements.txt`
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
gunicorn>=21.2.0
azure-cosmos>=4.5.0
python-dotenv>=1.0.0
google-genai>=1.0.0
```

### Startup Command
```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0 --timeout 600
```

### 必須のApp Settings
```
SCM_DO_BUILD_DURING_DEPLOYMENT=true
ENABLE_ORYX_BUILD=true
WEBSITES_PORT=8000
COSMOS_ENDPOINT=<Cosmos DB endpoint>
COSMOS_KEY=<Cosmos DB key>
COSMOS_DATABASE_NAME=SangikyoDB
GEMINI_API_KEY=<Gemini API key>
```

---

## まとめ

Azure App ServiceへのFastAPIデプロイでは、**Oryxビルドの有効化**と**適切なワーカー設定**が必須です。

今回の問題解決により、以下が完全に動作する状態になりました:
- ✅ FastAPI バックエンド
- ✅ Cosmos DB 統合
- ✅ Gemini API (AI Chat機能)
- ✅ RAG機能（ユーザーデータに基づく回答生成）

**デプロイ日**: 2026年2月28日
**解決時間**: 約2時間
**最終確認**: 全エンドポイント正常動作
