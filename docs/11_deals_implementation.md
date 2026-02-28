# Deals（案件管理）機能実装

## 概要

三技協のサービスに特化したDeals（案件管理）機能を実装しました。三技協は製品販売ではなくサービス提供事業のため、ProductsテーブルではなくDealsのみを実装しました。

## ビジネス要件

### 三技協の3つのサービス種別
1. **通信インフラ構築** - 5G基地局構築、光ファイバー網構築など
2. **技術人材派遣** - ネットワークエンジニアの派遣など
3. **危機管理対策** - BCPコンサルティング、データセンター対策など

### 案件ステージ
- 見込み
- 提案
- 商談
- 受注
- 失注

## データモデル

### Deal Schema

**ファイル**: `backend/app/models/schemas.py`

```python
class Deal(BaseModel):
    """Deal model."""
    deal_id: str
    customer_id: str
    customer_name: Optional[str] = None  # 顧客名（JOIN結果用）
    sales_user_id: str
    sales_user_name: Optional[str] = None  # 営業担当者名（JOIN結果用）
    deal_stage: str  # 見込み、提案、商談、受注、失注
    deal_amount: Optional[float] = None  # 案件金額
    service_type: Optional[str] = None  # サービス種別（通信インフラ構築、人材派遣、危機管理対策）
    last_contact_date: Optional[str] = None  # 最終接触日（YYYY-MM-DD形式）
    notes: Optional[str] = None  # メモ・提案内容
```

**フィールド説明**:
- `deal_id`: 案件ID（主キー）
- `customer_id`: 顧客ID（外部キー）
- `customer_name`: 顧客名（表示用、非正規化）
- `sales_user_id`: 営業担当者ID（外部キー）
- `sales_user_name`: 営業担当者名（表示用、非正規化）
- `deal_stage`: 案件ステージ
- `deal_amount`: 案件金額（円）
- `service_type`: サービス種別
- `last_contact_date`: 最終接触日
- `notes`: メモ・提案内容

## バックエンド実装

### 1. Repository層

**ファイル**: `backend/app/repositories/deal.py`

DealRepositoryは以下のメソッドを提供します：

```python
class DealRepository(BaseRepository[Deal]):
    async def get_all_deals() -> List[Deal]
    async def get_deal_by_id(deal_id: str) -> Optional[Deal]
    async def get_deals_by_user(sales_user_id: str) -> List[Deal]
    async def get_deals_by_customer(customer_id: str) -> List[Deal]
    async def get_deals_by_stage(deal_stage: str) -> List[Deal]
    async def get_deals_by_service_type(service_type: str) -> List[Deal]
```

**主な機能**:
- 全案件取得
- ID指定で案件取得
- 営業担当者でフィルタ
- 顧客でフィルタ
- ステージでフィルタ
- サービス種別でフィルタ

### 2. Dependency Injection

**ファイル**: `backend/app/core/dependencies.py`

```python
def get_deal_repository() -> DealRepository:
    return DealRepository()
```

### 3. API エンドポイント

**ファイル**: `backend/app/api/routes.py`

#### GET /api/v1/deals

全案件取得、または各種フィルタで絞り込み

**クエリパラメータ**:
- `sales_user_id`: 営業担当者でフィルタ
- `customer_id`: 顧客でフィルタ
- `deal_stage`: ステージでフィルタ（例: 商談）
- `service_type`: サービス種別でフィルタ（例: 通信インフラ構築）

**使用例**:
```bash
# 全案件取得
curl http://localhost:8000/api/v1/deals

# 営業担当者でフィルタ
curl http://localhost:8000/api/v1/deals?sales_user_id=1

# ステージでフィルタ
curl "http://localhost:8000/api/v1/deals?deal_stage=商談"

# サービス種別でフィルタ
curl "http://localhost:8000/api/v1/deals?service_type=通信インフラ構築"
```

#### GET /api/v1/deals/{deal_id}

特定の案件を取得

**使用例**:
```bash
curl http://localhost:8000/api/v1/deals/1
```

### 4. デモデータ

**ファイル**: `backend/app/initializers/seed_data.py`

5件のデモ案件を投入：

1. **KDDI - 5G基地局構築（商談）** - ¥50,000,000
   - サービス種別: 通信インフラ構築
   - 営業担当: 山田太郎

2. **ソフトバンク - ネットワークエンジニア派遣（提案）** - ¥30,000,000
   - サービス種別: 技術人材派遣
   - 営業担当: 山田太郎

3. **楽天 - BCP対策コンサル（見込み）** - ¥15,000,000
   - サービス種別: 危機管理対策
   - 営業担当: 佐藤花子

4. **KDDI - 光ファイバー網構築（受注）** - ¥80,000,000
   - サービス種別: 通信インフラ構築
   - 営業担当: 佐藤花子

5. **ソフトバンク - 人材派遣（失注）** - ¥20,000,000
   - サービス種別: 技術人材派遣
   - 営業担当: 山田太郎

## フロントエンド実装

### 1. API Client

**ファイル**: `frontend/src/lib/api.ts`

```typescript
export interface Deal {
  deal_id: string
  customer_id: string
  customer_name?: string
  sales_user_id: string
  sales_user_name?: string
  deal_stage: string
  deal_amount?: number
  service_type?: string
  last_contact_date?: string
  notes?: string
}

export async function getDeals(): Promise<Deal[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/deals`)
  if (!response.ok) {
    throw new Error('Failed to fetch deals')
  }
  return response.json()
}
```

### 2. データ確認ページ

**ファイル**: `frontend/src/app/data/page.tsx`

Dealsテーブルを追加し、以下の機能を実装：

**TanStack Query使用**:
```typescript
const {
  data: deals = [],
  isLoading: dealsLoading,
  error: dealsError,
} = useQuery({
  queryKey: ['deals'],
  queryFn: getDeals,
})
```

**表示内容**:
- ID
- 顧客名
- 営業担当者名
- ステージ（色分けバッジ）
  - 受注: 緑
  - 失注: 赤
  - 商談: 青
  - 提案: 黄色
  - 見込み: 灰色
- サービス種別
- 金額（¥形式でフォーマット）
- 最終接触日

## アーキテクチャパターン

このDeal実装は、バックエンドアーキテクチャガイド（`docs/10_backend_architecture.md`）に従っています：

1. **Repository Pattern** - データアクセス層の抽象化
2. **Dependency Injection** - FastAPIのDepends()を使用
3. **Logging** - 構造化ログ出力
4. **Error Handling** - カスタム例外（NotFoundException）

## フロントエンドパターン

フロントエンドは、コーディング規約（`.claude/claude.md`）に従っています：

1. **TanStack Query** - useEffect + fetchではなくuseQueryを使用
2. **TypeScript** - 型安全性を確保
3. **Tailwind CSS** - スタイリング

## Cosmos DB構成

**Container**: `Deals`
**Partition Key**: `/deal_id`

## テスト結果

### バックエンド

```bash
# 全案件取得 - ✅ 成功（5件）
curl http://localhost:8000/api/v1/deals

# 営業担当者でフィルタ - ✅ 成功（3件）
curl http://localhost:8000/api/v1/deals?sales_user_id=1

# ステージでフィルタ - ✅ 成功（1件）
curl "http://localhost:8000/api/v1/deals?deal_stage=商談"

# ID指定取得 - ✅ 成功
curl http://localhost:8000/api/v1/deals/1
```

### フロントエンド

- ✅ http://localhost:3000/data でDeals表示確認
- ✅ TanStack Queryによる自動キャッシング
- ✅ ステージバッジの色分け表示
- ✅ 金額のフォーマット表示

## 次のステップ候補

1. **Deal CRUD操作** - 作成、更新、削除APIの実装
2. **Deal詳細ページ** - 個別案件の詳細表示
3. **ダッシュボード** - 案件ステージ別の集計表示
4. **フィルタUI** - ドロップダウンでのフィルタリング
5. **AI機能統合** - 案件提案内容の自動生成

## まとめ

三技協のサービス提供事業に特化したDeals機能を実装しました。Repository パターンによる保守性の高いバックエンド、TanStack Query による効率的なフロントエンドデータ取得、そして3つのサービス種別と5つの案件ステージを管理できる SFA の基盤が完成しました。
