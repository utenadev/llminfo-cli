"""Pydantic data models for llminfo-cli"""

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Model information data model"""

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable model name")
    context_length: int | None = Field(None, description="Context window size")
    pricing: dict | None = Field(None, description="Pricing information")


class CreditInfo(BaseModel):
    """Credit information data model"""

    total_credits: float = Field(..., description="Total purchased credits")
    usage: float = Field(..., description="Total usage")
    remaining: float = Field(..., description="Remaining credits")
