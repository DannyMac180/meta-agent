from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

BUNDLE_SCHEMA_VERSION = "1.0"


class BundleMetadata(BaseModel):
    """Metadata describing a generated agent bundle."""

    schema_version: str = Field(
        default=BUNDLE_SCHEMA_VERSION,
        description="Version of the bundle metadata schema.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the bundle was created (UTC).",
    )
    meta_agent_version: Optional[str] = Field(
        default=None,
        description="Version of Meta Agent that produced the bundle.",
    )
    custom: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata fields for extensibility.",
    )

    class Config:
        extra = "allow"  # Preserve unknown fields for forward compatibility
