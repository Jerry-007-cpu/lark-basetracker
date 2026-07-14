"""Shared table tracking core and provider adapters."""

from .core import (
    auto_match_fields,
    build_state,
    diff_states,
    filter_records,
    load_state,
    norm,
    read_snapshot,
    render_diff,
    render_records,
    save_state,
)

__all__ = [
    "auto_match_fields",
    "build_state",
    "diff_states",
    "filter_records",
    "load_state",
    "norm",
    "read_snapshot",
    "render_diff",
    "render_records",
    "save_state",
]
