"""Seed demo data to Cosmos DB."""

from app.core.database import cosmos_client


def seed_users():
    """Seed demo users."""
    users_container = cosmos_client.get_container("Users")

    demo_users = [
        {
            "id": "1",
            "user_id": "1",
            "name": "山田太郎",
            "email": "yamada@example.com",
            "department": "営業部",
            "role": "営業担当",
        },
        {
            "id": "2",
            "user_id": "2",
            "name": "佐藤花子",
            "email": "sato@example.com",
            "department": "営業部",
            "role": "マネージャー",
        },
    ]

    for user in demo_users:
        try:
            users_container.upsert_item(user)
            print(f"✓ User created: {user['name']}")
        except Exception as e:
            print(f"✗ Error creating user {user['name']}: {e}")


def seed_customers():
    """Seed demo customers."""
    customers_container = cosmos_client.get_container("Customers")

    demo_customers = [
        {
            "id": "1",
            "customer_id": "1",
            "name": "KDDI株式会社",
            "industry": "通信",
            "contact_person": "田中一郎",
            "email": "tanaka@kddi.example.com",
            "phone": "03-1234-5678",
        },
        {
            "id": "2",
            "customer_id": "2",
            "name": "ソフトバンク株式会社",
            "industry": "通信",
            "contact_person": "鈴木次郎",
            "email": "suzuki@softbank.example.com",
            "phone": "03-2345-6789",
        },
        {
            "id": "3",
            "customer_id": "3",
            "name": "楽天グループ株式会社",
            "industry": "IT・通信",
            "contact_person": "高橋三郎",
            "email": "takahashi@rakuten.example.com",
            "phone": "03-3456-7890",
        },
    ]

    for customer in demo_customers:
        try:
            customers_container.upsert_item(customer)
            print(f"✓ Customer created: {customer['name']}")
        except Exception as e:
            print(f"✗ Error creating customer {customer['name']}: {e}")


def seed_deals():
    """Seed demo deals."""
    deals_container = cosmos_client.get_container("Deals")

    demo_deals = [
        {
            "id": "1",
            "deal_id": "1",
            "customer_id": "1",
            "customer_name": "KDDI株式会社",
            "sales_user_id": "1",
            "sales_user_name": "山田太郎",
            "deal_stage": "商談",
            "deal_amount": 50000000,
            "service_type": "通信インフラ構築",
            "last_contact_date": "2026-02-25",
            "notes": "5G基地局構築プロジェクト。関西エリア10拠点の提案中。",
        },
        {
            "id": "2",
            "deal_id": "2",
            "customer_id": "2",
            "customer_name": "ソフトバンク株式会社",
            "sales_user_id": "1",
            "sales_user_name": "山田太郎",
            "deal_stage": "提案",
            "deal_amount": 30000000,
            "service_type": "技術人材派遣",
            "last_contact_date": "2026-02-20",
            "notes": "ネットワークエンジニア5名の派遣。6ヶ月契約。",
        },
        {
            "id": "3",
            "deal_id": "3",
            "customer_id": "3",
            "customer_name": "楽天グループ株式会社",
            "sales_user_id": "2",
            "sales_user_name": "佐藤花子",
            "deal_stage": "見込み",
            "deal_amount": 15000000,
            "service_type": "危機管理対策",
            "last_contact_date": "2026-02-15",
            "notes": "データセンターのBCP対策コンサルティング。初回ヒアリング済み。",
        },
        {
            "id": "4",
            "deal_id": "4",
            "customer_id": "1",
            "customer_name": "KDDI株式会社",
            "sales_user_id": "2",
            "sales_user_name": "佐藤花子",
            "deal_stage": "受注",
            "deal_amount": 80000000,
            "service_type": "通信インフラ構築",
            "last_contact_date": "2026-01-30",
            "notes": "光ファイバー網構築プロジェクト（受注済み）。3月着工予定。",
        },
        {
            "id": "5",
            "deal_id": "5",
            "customer_id": "2",
            "customer_name": "ソフトバンク株式会社",
            "sales_user_id": "1",
            "sales_user_name": "山田太郎",
            "deal_stage": "失注",
            "deal_amount": 20000000,
            "service_type": "技術人材派遣",
            "last_contact_date": "2026-01-15",
            "notes": "価格面で他社に決定。次回案件で再提案予定。",
        },
    ]

    for deal in demo_deals:
        try:
            deals_container.upsert_item(deal)
            print(
                f"✓ Deal created: {deal['customer_name']} - {deal['service_type']} ({deal['deal_stage']})"
            )
        except Exception as e:
            print(f"✗ Error creating deal {deal['deal_id']}: {e}")


def seed_all():
    """Seed all demo data."""
    print("🌱 Seeding demo data...")
    seed_users()
    seed_customers()
    seed_deals()
    print("✅ Demo data seeded successfully!")


if __name__ == "__main__":
    seed_all()
