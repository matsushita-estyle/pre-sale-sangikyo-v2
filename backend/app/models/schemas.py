"""Pydantic schemas for API models."""
from typing import Optional, List
from pydantic import BaseModel


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
