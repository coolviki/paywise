from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class McpKeyCreate(BaseModel):
    name: str = Field(default="Claude", max_length=100)


class McpKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class McpKeyCreatedResponse(McpKeyResponse):
    # Returned only once, at creation time
    api_key: str
