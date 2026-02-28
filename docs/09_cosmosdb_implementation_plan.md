# Cosmos DB 実装プラン（エンドツーエンド確認）

## 目的

Cosmos DB を Terraform で作成し、フロントエンド → バックエンド → Cosmos DB の流れで動作確認する。

## 実装ステップ

### ステップ1: Terraform で Cosmos DB を作成

**ファイル**: `terraform/main.tf`

```hcl
# Cosmos DB アカウント
resource "azurerm_cosmosdb_account" "main" {
  name                = "${var.project_name}-cosmosdb"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  enable_automatic_failover = false
  enable_free_tier          = true  # 無料枠を有効化

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"  # サーバーレスモード
  }

  tags = var.tags
}

# Cosmos DB データベース
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "SangikyoDB"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Users コンテナ
resource "azurerm_cosmosdb_sql_container" "users" {
  name                = "Users"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/user_id"
}

# Customers コンテナ
resource "azurerm_cosmosdb_sql_container" "customers" {
  name                = "Customers"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/customer_id"
}

# Products コンテナ
resource "azurerm_cosmosdb_sql_container" "products" {
  name                = "Products"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/product_id"
}

# Deals コンテナ
resource "azurerm_cosmosdb_sql_container" "deals" {
  name                = "Deals"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/deal_id"
}

# News コンテナ
resource "azurerm_cosmosdb_sql_container" "news" {
  name                = "News"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/news_id"
}
```

**ファイル**: `terraform/outputs.tf`

```hcl
# Cosmos DB 接続情報を出力
output "cosmos_endpoint" {
  value     = azurerm_cosmosdb_account.main.endpoint
  sensitive = false
}

output "cosmos_primary_key" {
  value     = azurerm_cosmosdb_account.main.primary_key
  sensitive = true
}

output "cosmos_database_name" {
  value = azurerm_cosmosdb_sql_database.main.name
}
```

**実行**:
```bash
cd terraform
terraform plan
terraform apply
```

---

### ステップ2: 接続情報を取得して環境変数に設定

**接続情報取得**:
```bash
cd terraform
terraform output cosmos_endpoint
terraform output -raw cosmos_primary_key
```

**ローカル開発用（backend/.env）**:
```bash
# backend/.env
COSMOS_ENDPOINT=https://sangikyo-v2-cosmosdb.documents.azure.com:443/
COSMOS_KEY=<取得したキー>
COSMOS_DATABASE=SangikyoDB
```

**Azure App Service 用（環境変数）**:
```bash
az webapp config appsettings set \
  --name sangikyo-v2-backend \
  --resource-group rg_matsushita \
  --settings \
    COSMOS_ENDPOINT="$(cd terraform && terraform output -raw cosmos_endpoint)" \
    COSMOS_KEY="$(cd terraform && terraform output -raw cosmos_primary_key)" \
    COSMOS_DATABASE="SangikyoDB"
```

---

### ステップ3: バックエンドの実装

#### 3-1. requirements.txt に追加

```txt
# backend/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
gunicorn>=21.2.0
azure-cosmos>=4.5.1
pydantic>=2.0.0
python-dotenv>=1.0.0
```

#### 3-2. Cosmos DB クライアント実装

**ファイル**: `backend/app/config.py`

```python
"""環境変数設定"""
import os
from dotenv import load_dotenv

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "SangikyoDB")
```

**ファイル**: `backend/app/database.py`

```python
"""Cosmos DB 接続"""
from azure.cosmos import CosmosClient
from app.config import COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE

# クライアント初期化
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)

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

#### 3-3. データモデル定義

**ファイル**: `backend/app/models.py`

```python
"""Pydantic モデル"""
from pydantic import BaseModel

class User(BaseModel):
    id: str
    user_id: int
    name: str
    email: str
    department: str
    attributes: dict  # {"industries": [...], "regions": [...]}

class Customer(BaseModel):
    id: str
    customer_id: int
    company_name: str
    industry: str
    region: str
    website: str | None = None
    description: str | None = None
```

#### 3-4. デモデータ投入

**ファイル**: `backend/app/initializer.py`

```python
"""Cosmos DB にデモデータを投入"""
from app.database import get_users_container, get_customers_container

def initialize_users():
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
    print(f"✓ User {user['name']} created")

def initialize_customers():
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
        print(f"✓ Customer {customer['company_name']} created")

def initialize_all():
    print("Initializing Cosmos DB...")
    initialize_users()
    initialize_customers()
    print("✓ Initialization complete!")
```

#### 3-5. API エンドポイント実装

**ファイル**: `backend/app/main.py`

```python
"""FastAPI アプリケーション"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_users_container, get_customers_container
from app.initializer import initialize_all

app = FastAPI(
    title="Sangikyo V2 API",
    version="1.0.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """起動時にデータ初期化"""
    try:
        initialize_all()
    except Exception as e:
        print(f"Initialization failed: {e}")

@app.get("/")
async def root():
    return {"message": "Sangikyo V2 Backend", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/users")
async def get_users():
    """ユーザー一覧を取得"""
    container = get_users_container()
    users = list(container.query_items(
        query="SELECT * FROM c",
        enable_cross_partition_query=True
    ))
    return users

@app.get("/api/v1/customers")
async def get_customers():
    """顧客一覧を取得"""
    container = get_customers_container()
    customers = list(container.query_items(
        query="SELECT * FROM c",
        enable_cross_partition_query=True
    ))
    return customers
```

---

### ステップ4: フロントエンドの実装

#### 4-1. データ表示ページ作成

**ファイル**: `frontend/src/app/data/page.tsx`

```typescript
'use client'

import { useEffect, useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { Card } from '@/components/shared/Card'

interface User {
  user_id: number
  name: string
  email: string
  department: string
  attributes: {
    industries: string[]
    regions: string[]
  }
}

interface Customer {
  customer_id: number
  company_name: string
  industry: string
  region: string
  website?: string
}

export default function DataPage() {
  const [users, setUsers] = useState<User[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const [usersRes, customersRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/users`),
          fetch(`${apiUrl}/api/v1/customers`),
        ])

        const usersData = await usersRes.json()
        const customersData = await customersRes.json()

        setUsers(usersData)
        setCustomers(customersData)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <MainLayout>
        <div className="p-6">
          <p>読み込み中...</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">データ管理</h1>

        {/* ユーザー一覧 */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">ユーザー</h2>
          <div className="space-y-2">
            {users.map((user) => (
              <div key={user.user_id} className="border-b pb-2">
                <p className="font-medium">{user.name}</p>
                <p className="text-sm text-gray-600">{user.email}</p>
                <p className="text-sm text-gray-600">
                  担当業界: {user.attributes.industries.join(', ')}
                </p>
                <p className="text-sm text-gray-600">
                  担当地域: {user.attributes.regions.join(', ')}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* 顧客一覧 */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">顧客企業</h2>
          <div className="space-y-2">
            {customers.map((customer) => (
              <div key={customer.customer_id} className="border-b pb-2">
                <p className="font-medium">{customer.company_name}</p>
                <p className="text-sm text-gray-600">
                  {customer.industry} / {customer.region}
                </p>
                {customer.website && (
                  <a
                    href={customer.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {customer.website}
                  </a>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </MainLayout>
  )
}
```

---

### ステップ5: 動作確認

#### ローカルで確認

```bash
# 1. バックエンド起動
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000

# 2. フロントエンド起動（別ターミナル）
cd frontend
npm run dev
# → http://localhost:3000

# 3. ブラウザで確認
# http://localhost:3000/data
```

#### 確認ポイント

- [ ] バックエンドが起動する
- [ ] Cosmos DB にデータが投入される
- [ ] `/api/v1/users` でユーザー一覧が返る
- [ ] `/api/v1/customers` で顧客一覧が返る
- [ ] フロントエンドでユーザーと顧客が表示される

---

## まとめ

このプランで以下が達成できます:

✅ Terraform で Cosmos DB を管理
✅ バックエンドから Cosmos DB にアクセス
✅ フロントエンドでデータ表示
✅ **エンドツーエンドで動作確認**

準備ができたら、ステップ1（Terraform）から開始しましょう！
