"""Introspection over the agent's tool set."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..tools import tool_registry

router = APIRouter(tags=["tools"])


class ToolDescription(BaseModel):
    name: str
    description: str
    parameters: list[str]
    is_async: bool


@router.get("/tools", response_model=list[ToolDescription])
async def list_tools() -> list[ToolDescription]:
    """The tools the agent runs, with the argument schema inferred from each signature."""
    return [
        ToolDescription(
            name=name,
            description=tool.description,
            parameters=sorted(tool.args),
            is_async=tool.func is None,
        )
        for name, tool in sorted(tool_registry().items())
    ]
