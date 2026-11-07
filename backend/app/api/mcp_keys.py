"""Manage personal API keys for the Claude connector (Settings > Connect to Claude)."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..schemas.mcp_key import McpKeyCreate, McpKeyCreatedResponse, McpKeyResponse
from ..services.mcp_key_service import McpKeyLimitError, McpKeyService

router = APIRouter()


@router.get("", response_model=List[McpKeyResponse])
async def list_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return McpKeyService.list_keys(db, current_user.id)


@router.post("", response_model=McpKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    body: McpKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        record, raw_key = McpKeyService.create_key(db, current_user.id, body.name)
    except McpKeyLimitError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return McpKeyCreatedResponse(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
        api_key=raw_key,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not McpKeyService.revoke_key(db, current_user.id, key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
