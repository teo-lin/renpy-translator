"""
Data models for poly_trans translation pipeline.

Minimal subset of models needed for translation operations.
"""

from typing import TypedDict, Optional


class ParsedBlock(TypedDict, total=False):
    """
    Represents a block after extraction (clean text, no tags).

    Used in YAML format for human editing.
    """
    en: str                         # Clean English text (tags removed)
    ro: str                         # Clean Romanian translation (tags removed)
    type: Optional[str]             # Only present for separators


def parse_block_id(block_id: str) -> tuple[int, str]:
    """
    Parse a composite block ID.

    Args:
        block_id: Composite ID like "1-Jasmine"

    Returns:
        Tuple of (index, character_name)
    """
    parts = block_id.split('-', 1)
    if len(parts) == 2:
        try:
            return int(parts[0]), parts[1]
        except ValueError:
            pass
    # Fallback for invalid format
    return 0, block_id


def is_separator_block(block_id: str, block_data: ParsedBlock) -> bool:
    """
    Check if a block is a separator.

    Args:
        block_id: Block ID
        block_data: Parsed block data

    Returns:
        True if block is a separator
    """
    return (
        block_id.startswith("separator-") or
        block_data.get("type") == "separator"
    )
