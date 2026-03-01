"""Deal-related tools for Gemini Function Calling Agent."""

import logging

from google.genai import types

from app.repositories.deal import DealRepository

logger = logging.getLogger(__name__)


# ========================================
# Tool Functions
# ========================================


async def search_deals(
    sales_user_id: str | None = None,
    deal_stage: str | None = None,
    customer_id: str | None = None,
) -> str:
    """Search deals by sales user, stage, or customer.

    Args:
        sales_user_id: Sales user ID to filter by
        deal_stage: Deal stage to filter by (見込み、提案、商談、受注、失注)
        customer_id: Customer ID to filter by

    Returns:
        Formatted list of deals
    """
    try:
        repo = DealRepository()
        deals = []

        # 営業担当者で検索
        if sales_user_id:
            deals = await repo.get_deals_by_user(sales_user_id)

        # 顧客で検索
        elif customer_id:
            deals = await repo.get_deals_by_customer(customer_id)

        # ステージで検索
        elif deal_stage:
            deals = await repo.get_deals_by_stage(deal_stage)

        # 条件がない場合は全件取得
        else:
            deals = await repo.get_all_deals()

        # フィルタリング（複数条件が指定された場合）
        if sales_user_id and deals:
            deals = [d for d in deals if d.sales_user_id == sales_user_id]
        if deal_stage and deals:
            deals = [d for d in deals if d.deal_stage == deal_stage]
        if customer_id and deals:
            deals = [d for d in deals if d.customer_id == customer_id]

        if not deals:
            return "該当する案件が見つかりませんでした。"

        result = f"{len(deals)}件の案件が見つかりました:\n\n"
        for deal in deals:
            result += f"- 案件ID: {deal.deal_id}\n"
            result += f"  顧客: {deal.customer_name or 'なし'}\n"
            result += f"  ステージ: {deal.deal_stage}\n"
            result += f"  金額: {deal.deal_amount:,.0f}円\n" if deal.deal_amount else "  金額: なし\n"
            result += f"  サービス: {deal.service_type or 'なし'}\n\n"

        return result
    except Exception as e:
        logger.error(f"Error in search_deals: {e}", exc_info=True)
        return f"エラーが発生しました: {str(e)}"


async def get_deal_details(deal_id: str) -> str:
    """Get deal details.

    Args:
        deal_id: Deal ID

    Returns:
        Formatted deal details
    """
    try:
        repo = DealRepository()
        deal = await repo.get_deal_by_id(deal_id)

        if not deal:
            return f"案件ID {deal_id} は見つかりませんでした。"

        return f"""案件詳細:
- 案件ID: {deal.deal_id}
- 顧客: {deal.customer_name or 'なし'}
- 営業担当: {deal.sales_user_name or 'なし'}
- ステージ: {deal.deal_stage}
- 金額: {deal.deal_amount:,.0f}円""" + (
            f"\n- サービス種別: {deal.service_type or 'なし'}"
            f"\n- 最終接触日: {deal.last_contact_date or 'なし'}"
            f"\n- メモ: {deal.notes or 'なし'}"
        )
    except Exception as e:
        logger.error(f"Error in get_deal_details: {e}", exc_info=True)
        return f"エラーが発生しました: {str(e)}"


# ========================================
# Gemini Tool Declarations
# ========================================


search_deals_declaration = types.FunctionDeclaration(
    name="search_deals",
    description=(
        "営業担当者、案件ステージ、顧客IDで案件を検索します。"
        "このツールは案件ID、顧客名、ステージ、金額、サービスなど全ての情報を返すので、"
        "通常はget_deal_detailsを追加で呼ぶ必要はありません。"
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "sales_user_id": types.Schema(
                type=types.Type.STRING,
                description="営業担当者のユーザーID",
            ),
            "deal_stage": types.Schema(
                type=types.Type.STRING,
                description="案件ステージ（見込み、提案、商談、受注、失注）",
                enum=["見込み", "提案", "商談", "受注", "失注"],
            ),
            "customer_id": types.Schema(
                type=types.Type.STRING, description="顧客ID"
            ),
        },
    ),
)

get_deal_details_declaration = types.FunctionDeclaration(
    name="get_deal_details",
    description=(
        "指定された案件IDの詳細情報を取得します。"
        "注意: search_dealsで既に主要な情報（顧客名、ステージ、金額）が取得できるため、"
        "特定の詳細情報（メモや最終接触日）が必要な場合のみ使用してください。"
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "deal_id": types.Schema(
                type=types.Type.STRING, description="案件ID"
            )
        },
        required=["deal_id"],
    ),
)
