"""Pydantic schemas for API models."""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class User(BaseModel):
    """User model."""

    user_id: str
    name: str
    email: str
    department: Optional[str] = None
    role: Optional[str] = None


class Customer(BaseModel):
    """Customer model."""

    customer_id: str
    name: str
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


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


class ChatRequest(BaseModel):
    """Chat request model."""

    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="User's question")


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="AI-generated response")
