"""Pydantic schemas for API models."""

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model."""

    user_id: str
    name: str
    email: str
    department: str | None = None
    role: str | None = None


class Customer(BaseModel):
    """Customer model."""

    customer_id: str
    name: str
    industry: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None


class Deal(BaseModel):
    """Deal model."""

    deal_id: str
    customer_id: str
    customer_name: str | None = None  # 顧客名（JOIN結果用）
    sales_user_id: str
    sales_user_name: str | None = None  # 営業担当者名（JOIN結果用）
    deal_stage: str  # 見込み、提案、商談、受注、失注
    deal_amount: float | None = None  # 案件金額
    service_type: str | None = None  # サービス種別（通信インフラ構築、人材派遣、危機管理対策）
    last_contact_date: str | None = None  # 最終接触日（YYYY-MM-DD形式）
    notes: str | None = None  # メモ・提案内容


class ChatRequest(BaseModel):
    """Chat request model."""

    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="User's question")


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="AI-generated response")
