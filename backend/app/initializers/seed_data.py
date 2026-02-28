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


def seed_all():
    """Seed all demo data."""
    print("🌱 Seeding demo data...")
    seed_users()
    seed_customers()
    print("✅ Demo data seeded successfully!")


if __name__ == "__main__":
    seed_all()
