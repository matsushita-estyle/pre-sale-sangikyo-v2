"""Tools for Gemini Function Calling Agent."""

from typing import Any

from google.genai import types

from app.agent.tools.customer_tools import (
    get_customer_details,
    get_customer_details_declaration,
    search_customers,
    search_customers_declaration,
)
from app.agent.tools.deal_tools import (
    get_deal_details,
    get_deal_details_declaration,
    search_deals,
    search_deals_declaration,
)
from app.agent.tools.news_tools import (
    search_latest_news,
    search_latest_news_declaration,
)
from app.agent.tools.user_tools import get_user_info, get_user_info_declaration

__all__ = [
    "get_tools",
    "execute_tool",
    "get_user_info",
    "search_customers",
    "get_customer_details",
    "search_deals",
    "get_deal_details",
    "search_latest_news",
]


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
                get_user_info_declaration,
                search_customers_declaration,
                get_customer_details_declaration,
                search_deals_declaration,
                get_deal_details_declaration,
                search_latest_news_declaration,
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
