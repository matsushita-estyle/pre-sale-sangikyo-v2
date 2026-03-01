"""User-related tools for Gemini Function Calling Agent."""

import logging

from google.genai import types

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


# ========================================
# Gemini Tool Declarations
# ========================================


get_user_info_declaration = types.FunctionDeclaration(
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
)
