"""Customer-related tools for Gemini Function Calling Agent."""

import logging

from google.genai import types

from app.repositories.customer import CustomerRepository

logger = logging.getLogger(__name__)


# ========================================
# Tool Functions
# ========================================


async def search_customers(
    industries: list[str] | None = None, keyword: str | None = None
) -> str:
    """Search customers by industries or keyword.

    Args:
        industries: List of industries to filter by
        keyword: Keyword to search in customer name

    Returns:
        Formatted list of customers
    """
    try:
        repo = CustomerRepository()
        customers = []

        # 業界で検索
        if industries:
            for industry in industries:
                industry_customers = await repo.get_customers_by_industry(industry)
                customers.extend(industry_customers)

        # キーワードで検索
        if keyword:
            keyword_customers = await repo.search_customers(keyword)
            customers.extend(keyword_customers)

        # 条件がない場合は全件取得
        if not industries and not keyword:
            customers = await repo.get_all_customers()

        # 重複除去
        unique_customers = list({c.customer_id: c for c in customers}.values())

        if not unique_customers:
            return "該当する顧客が見つかりませんでした。"

        result = f"{len(unique_customers)}件の顧客が見つかりました:\n\n"
        for customer in unique_customers:
            result += f"- {customer.name} (ID: {customer.customer_id})\n"
            result += f"  業界: {customer.industry or 'なし'}\n"
            result += f"  担当者: {customer.contact_person or 'なし'}\n\n"

        return result
    except Exception as e:
        logger.error(f"Error in search_customers: {e}", exc_info=True)
        return f"エラーが発生しました: {str(e)}"


async def get_customer_details(customer_id: str) -> str:
    """Get customer details.

    Args:
        customer_id: Customer ID

    Returns:
        Formatted customer details
    """
    try:
        repo = CustomerRepository()
        customer = await repo.get_customer_by_id(customer_id)

        if not customer:
            return f"顧客ID {customer_id} は見つかりませんでした。"

        return f"""顧客詳細:
- 顧客名: {customer.name}
- 業界: {customer.industry or 'なし'}
- 担当者: {customer.contact_person or 'なし'}
- メール: {customer.email or 'なし'}
- 電話番号: {customer.phone or 'なし'}"""
    except Exception as e:
        logger.error(f"Error in get_customer_details: {e}", exc_info=True)
        return f"エラーが発生しました: {str(e)}"


# ========================================
# Gemini Tool Declarations
# ========================================


search_customers_declaration = types.FunctionDeclaration(
    name="search_customers",
    description="業界やキーワードで顧客を検索します。複数の条件を指定可能です。",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "industries": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="業界のリスト（例: ['IT', '通信', '製造']）。指定した業界のいずれかに該当する顧客を検索します。",
            ),
            "keyword": types.Schema(
                type=types.Type.STRING,
                description="顧客名に含まれるキーワード（部分一致）",
            ),
        },
    ),
)

get_customer_details_declaration = types.FunctionDeclaration(
    name="get_customer_details",
    description="指定された顧客IDの詳細情報を取得します。",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "customer_id": types.Schema(
                type=types.Type.STRING, description="顧客ID"
            )
        },
        required=["customer_id"],
    ),
)
