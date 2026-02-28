"""エージェント関連のスキーマ定義"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ProgressEventType(str, Enum):
    """進捗イベントの種類"""

    THINKING = "thinking"  # 思考中
    FUNCTION_CALL = "function_call"  # ツール呼び出し
    FUNCTION_RESULT = "function_result"  # ツール実行結果
    RESPONSE_CHUNK = "response_chunk"  # レスポンス（部分）
    FINAL_RESPONSE = "final_response"  # 最終レスポンス
    ERROR = "error"  # エラー


class ProgressEvent(BaseModel):
    """進捗イベント"""

    type: ProgressEventType
    message: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    result: str | None = None
    content: str | None = None


class AgentQueryRequest(BaseModel):
    """エージェントクエリリクエスト"""

    user_id: str
    query: str


class AgentQueryResponse(BaseModel):
    """エージェントクエリレスポンス（非ストリーミング）"""

    response: str
