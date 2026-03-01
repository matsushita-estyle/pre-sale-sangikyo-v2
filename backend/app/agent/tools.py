"""Tools for Gemini Function Calling Agent."""

import logging
from typing import Any

from google.genai import types

from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


# ========================================
# Tool Functions
# ========================================


async def get_user_info(user_id: str) -> str:
    """Get user information.

    Args:
        user_id: User ID

    Returns:
        Formatted user information string
    """
    try:
        repo = UserRepository()
        user = await repo.get_user_by_id(user_id)

        if not user:
            return f"ユーザーID {user_id} は見つかりませんでした。"

        return f"""ユーザー情報:
- 名前: {user.name}
- メール: {user.email}
- 部署: {user.department or 'なし'}
- 役職: {user.role or 'なし'}"""
    except Exception as e:
        logger.error(f"Error in get_user_info: {e}", exc_info=True)
        return f"エラーが発生しました: {str(e)}"


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


async def search_latest_news(keywords: list[str], days: int = 7) -> str:
    """Search latest news using Google Search Grounding.

    Args:
        keywords: List of keywords to search for
        days: Number of days to look back (default: 7)

    Returns:
        Formatted list of news articles
    """
    import asyncio
    import os
    from google import genai
    from google.genai import types

    keyword_str = "、".join(keywords)

    try:
        # Gemini APIキーを取得
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found")
            return "エラー: Gemini APIキーが設定されていません。"

        # Gemini clientを作成
        client = genai.Client(api_key=api_key)

        # Google Search Groundingを使用してニュース検索
        prompt = (
            f"「{keyword_str}」に関する最新ニュース（過去{days}日間）を検索し、"
            f"実際のニュース記事を3〜5件、日付と概要付きで教えてください。\n"
            f"各ニュースは以下の形式で出力してください:\n"
            f"- タイトル\n"
            f"  日付: YYYY-MM-DD\n"
            f"  概要: (100文字程度)\n"
        )

        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.3,
        )

        # 非同期実行
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        )

        # レスポンステキストを取得
        if response.text:
            return f"{keyword_str} に関する最新ニュース:\n\n{response.text}"
        else:
            return f"{keyword_str} に関するニュースが見つかりませんでした。"

    except Exception as e:
        logger.error(f"Error in search_latest_news: {e}", exc_info=True)
        return f"ニュース検索中にエラーが発生しました: {str(e)}"


# ========================================
# Gemini Tool Declarations
# ========================================


def get_tools() -> list[types.Tool]:
    """Get Gemini tool declarations.

    Returns:
        List of Gemini Tool objects
    """
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="get_user_info",
                    description="指定されたユーザーIDのユーザー情報（名前、メールアドレス、部署、役職）を取得します。",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "user_id": types.Schema(
                                type=types.Type.STRING,
                                description="ユーザーID（例: 1, 2, 3）",
                            )
                        },
                        required=["user_id"],
                    ),
                ),
                types.FunctionDeclaration(
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
                ),
                types.FunctionDeclaration(
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
                ),
                types.FunctionDeclaration(
                    name="search_deals",
                    description="営業担当者、案件ステージ、顧客IDで案件を検索します。",
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
                ),
                types.FunctionDeclaration(
                    name="get_deal_details",
                    description="指定された案件IDの詳細情報を取得します。",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "deal_id": types.Schema(
                                type=types.Type.STRING, description="案件ID"
                            )
                        },
                        required=["deal_id"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="search_latest_news",
                    description="指定されたキーワードで最新のニュースを検索します。",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "keywords": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.STRING),
                                description="検索キーワードのリスト（例: ['KDDI', '5G']）",
                            ),
                            "days": types.Schema(
                                type=types.Type.INTEGER,
                                description="過去何日分のニュースを検索するか（デフォルト: 7日）",
                            ),
                        },
                        required=["keywords"],
                    ),
                ),
            ]
        )
    ]


# ========================================
# Tool Executor
# ========================================


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name.

    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool

    Returns:
        Tool execution result as a string

    Raises:
        ValueError: If tool name is unknown
    """
    if tool_name == "get_user_info":
        return await get_user_info(**arguments)
    elif tool_name == "search_customers":
        return await search_customers(**arguments)
    elif tool_name == "get_customer_details":
        return await get_customer_details(**arguments)
    elif tool_name == "search_deals":
        return await search_deals(**arguments)
    elif tool_name == "get_deal_details":
        return await get_deal_details(**arguments)
    elif tool_name == "search_latest_news":
        return await search_latest_news(**arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
