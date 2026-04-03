"""Tool implementations for Meta Ad Creative operations."""

from __future__ import annotations

from typing import Any

from meta_ads_mcp.api.client import MetaAPIClient
from meta_ads_mcp.api.pagination import extract_pagination_info
from meta_ads_mcp.security import validate_id

DEFAULT_CREATIVE_FIELDS: list[str] = [
    "name",
    "status",
    "title",
    "body",
    "image_url",
    "thumbnail_url",
    "object_story_spec",
    "url_tags",
    "effective_object_story_id",
    "created_time",
]


def get_creative(
    client: MetaAPIClient,
    creative_id: str,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Get details of a specific ad creative.

    Args:
        client: Meta API client.
        creative_id: Ad creative ID.
        fields: Fields to retrieve. Defaults to standard creative fields.
    """
    validate_id(creative_id, "creative_id")

    response = client.get_node(
        creative_id,
        fields=fields or DEFAULT_CREATIVE_FIELDS,
    )

    return {"data": response}


def list_creatives_by_ad(
    client: MetaAPIClient,
    ad_id: str,
    fields: list[str] | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """List ad creatives associated with an ad.

    Args:
        client: Meta API client.
        ad_id: Ad ID.
        fields: Fields to retrieve. Defaults to standard creative fields.
        limit: Maximum number of creatives to return (default: 25).
    """
    validate_id(ad_id, "ad_id")

    response = client.get_edge(
        ad_id,
        "adcreatives",
        fields=fields or DEFAULT_CREATIVE_FIELDS,
        limit=limit,
    )

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
    }
