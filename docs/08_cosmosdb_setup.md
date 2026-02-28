# Cosmos DB セットアップガイド

## 目的

Azure Cosmos DB をセットアップし、エージェントのデータストアとして使用できるようにする。

## Cosmos DB とは

**Azure Cosmos DB** は Azure のフルマネージド NoSQL データベースサービスです。

### 特徴
- **NoSQL**: JSON ドキュメントで柔軟にデータを保存
- **グローバル分散**: 世界中でレプリケーション可能
- **低レイテンシ**: 高速アクセス（<10ms）
- **スケーラブル**: 自動スケーリング

### データ構造

```
Cosmos DB Account
└── Database (例: SangikyoDB)
    ├── Container: Users
    │   └── Documents: { "id": "1", "user_id": 1, "name": "山田太郎", ... }
    ├── Container: Customers
    │   └── Documents: { "id": "1", "customer_id": 1, "company_name": "KDDI", ... }
    ├── Container: Products
    ├── Container: Deals
    └── Container: News
```

## セットアップ手順

### ステップ1: Cosmos DB リソースの作成

#### 方法A: Azure Portal（GUI）

1. Azure Portal にログイン
2. **リソースの作成** → **Azure Cosmos DB**
3. 設定:
   - **API**: NoSQL
   - **アカウント名**: `sangikyo-cosmosdb`
   - **リソースグループ**: `rg_matsushita`
   - **場所**: Japan East
   - **容量モード**: サーバーレス（開発用、コスト最小）
4. **確認および作成** → **作成**

#### 方法B: Azure CLI

```bash
# Cosmos DB アカウント作成
az cosmosdb create \
  --name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --locations regionName=japaneast \
  --kind GlobalDocumentDB \
  --default-consistency-level Session \
  --enable-automatic-failover false \
  --enable-serverless
```

**注意**: サーバーレスモードは開発に最適（使用量に応じて課金、最小コスト）

---

### ステップ2: データベースとコンテナの作成

#### Azure CLI で作成

```bash
# データベース作成
az cosmosdb sql database create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --name SangikyoDB

# Users コンテナ作成
az cosmosdb sql container create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --database-name SangikyoDB \
  --name Users \
  --partition-key-path "/user_id"

# Customers コンテナ作成
az cosmosdb sql container create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --database-name SangikyoDB \
  --name Customers \
  --partition-key-path "/customer_id"

# Products コンテナ作成
az cosmosdb sql container create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --database-name SangikyoDB \
  --name Products \
  --partition-key-path "/product_id"

# Deals コンテナ作成
az cosmosdb sql container create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --database-name SangikyoDB \
  --name Deals \
  --partition-key-path "/deal_id"

# News コンテナ作成
az cosmosdb sql container create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --database-name SangikyoDB \
  --name News \
  --partition-key-path "/news_id"
```

---

### ステップ3: 接続情報の取得

```bash
# エンドポイント取得
az cosmosdb show \
  --name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --query documentEndpoint -o tsv

# プライマリキー取得
az cosmosdb keys list \
  --name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --query primaryMasterKey -o tsv
```

**出力例**:
```
エンドポイント: https://sangikyo-cosmosdb.documents.azure.com:443/
プライマリキー: ABC123...XYZ789==
```

---

### ステップ4: 環境変数の設定

#### ローカル開発用（.env）

```bash
# backend/.env
COSMOS_ENDPOINT=https://sangikyo-cosmosdb.documents.azure.com:443/
COSMOS_KEY=ABC123...XYZ789==
COSMOS_DATABASE=SangikyoDB
```

#### Azure App Service 用（環境変数）

```bash
# App Service に環境変数を設定
az webapp config appsettings set \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --settings \
    COSMOS_ENDPOINT="https://sangikyo-cosmosdb.documents.azure.com:443/" \
    COSMOS_KEY="ABC123...XYZ789==" \
    COSMOS_DATABASE="SangikyoDB"
```

---

### ステップ5: Python クライアントのセットアップ

#### requirements.txt に追加

```txt
# backend/requirements.txt
azure-cosmos>=4.5.1
pydantic>=2.0.0
python-dotenv>=1.0.0
```

#### インストール

```bash
cd backend
pip install -r requirements.txt
```

---

### ステップ6: Cosmos DB クライアントの実装

#### backend/app/database.py

```python
"""Cosmos DB 接続設定"""
import os
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

# 環境変数から取得
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "SangikyoDB")

# クライアント初期化
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)

# コンテナ取得関数
def get_users_container():
    return database.get_container_client("Users")

def get_customers_container():
    return database.get_container_client("Customers")

def get_products_container():
    return database.get_container_client("Products")

def get_deals_container():
    return database.get_container_client("Deals")

def get_news_container():
    return database.get_container_client("News")
```

---

### ステップ7: データ投入の実装

#### backend/app/initializer.py

```python
"""Cosmos DB にデモデータを投入"""
from app.database import (
    get_users_container,
    get_customers_container,
    get_products_container,
)

def initialize_users():
    """ユーザーデータを投入"""
    container = get_users_container()

    user = {
        "id": "1",
        "user_id": 1,
        "name": "山田太郎",
        "email": "yamada@example.com",
        "department": "営業部",
        "attributes": {
            "industries": ["IT", "通信系"],
            "regions": ["西日本"]
        }
    }

    container.upsert_item(user)
    print(f"User {user['name']} created")

def initialize_customers():
    """顧客データを投入"""
    container = get_customers_container()

    customers = [
        {
            "id": "1",
            "customer_id": 1,
            "company_name": "KDDI株式会社",
            "industry": "通信系",
            "region": "西日本",
            "website": "https://www.kddi.com",
            "description": "総合通信事業者"
        },
        {
            "id": "2",
            "customer_id": 2,
            "company_name": "NTT西日本",
            "industry": "通信系",
            "region": "西日本",
            "website": "https://www.ntt-west.co.jp",
            "description": "地域通信事業者"
        },
    ]

    for customer in customers:
        container.upsert_item(customer)
        print(f"Customer {customer['company_name']} created")

def initialize_all():
    """すべてのデータを投入"""
    print("Initializing Cosmos DB...")
    initialize_users()
    initialize_customers()
    # initialize_products()
    # initialize_deals()
    # initialize_news()
    print("Initialization complete!")
```

---

### ステップ8: 動作確認

#### Python コンソールで確認

```python
# backend ディレクトリで実行
from app.initializer import initialize_all
initialize_all()

# データ取得確認
from app.database import get_users_container
container = get_users_container()
users = list(container.query_items(
    query="SELECT * FROM c",
    enable_cross_partition_query=True
))
print(users)
# → [{'id': '1', 'user_id': 1, 'name': '山田太郎', ...}]
```

---

## コスト見積もり

### サーバーレスモード（推奨）

- **ストレージ**: $0.25/GB/月
- **RU消費**: $0.28/100万 RU
- **最小コスト**: ほぼ無料（開発用途）

**例**: 月1万リクエスト、1GB データ
- ストレージ: $0.25
- RU消費: ~$0.01
- **合計**: 約 $0.26/月（約30円）

### 無料枠

- **最初の400 RU/s**: 永続無料
- **最初の25 GB**: 永続無料

開発段階では**ほぼ無料**で使えます。

---

## トラブルシューティング

### エラー: Authentication failed

```
azure.cosmos.exceptions.CosmosHttpResponseError:
Authentication failed
```

**原因**: COSMOS_KEY が間違っている

**解決策**:
```bash
# キーを再取得
az cosmosdb keys list \
  --name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --query primaryMasterKey -o tsv
```

---

### エラー: Database not found

**原因**: データベースが作成されていない

**解決策**:
```bash
# データベース作成
az cosmosdb sql database create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --name SangikyoDB
```

---

### エラー: Container not found

**原因**: コンテナが作成されていない

**解決策**:
```bash
# コンテナ作成（例: Users）
az cosmosdb sql container create \
  --account-name sangikyo-cosmosdb \
  --resource-group rg_matsushita \
  --database-name SangikyoDB \
  --name Users \
  --partition-key-path "/user_id"
```

---

## 次のステップ

Cosmos DB のセットアップが完了したら、以下を実装:

1. **データモデルの定義** (Pydantic)
2. **CRUD 操作の実装**
3. **エージェントツールへの統合**

準備ができたら進めましょう！
