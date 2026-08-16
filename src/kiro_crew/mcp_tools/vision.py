"""Fork: describe an image for a text-only model via the configured vision chain.

``schemas()`` returns the ADVERTISEMENT half of the tool -- its name, the
model-facing description, and the JSON Schema a call is validated against.
``HANDLERS`` maps that name to the function that runs it. See
:mod:`kiro_crew.mcp_tools.knowledge` for why both halves live together and why
handlers reach ``mcp_core``'s shared plumbing as attributes rather than direct
imports.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kiro_crew.acp.vision import describe_image_via_chain, resolve_vision_providers
from kiro_crew.config.loader import KiroCrewConfig
from kiro_crew.validation import VISION_ANALYZE_SCHEMA, validate_tool_args


def schemas() -> list[dict[str, Any]]:
    """Descriptor for the vision_analyze tool."""
    return [
        {
            "name": "vision_analyze",
            "description": (
                "Describe an image for a text-only model: pass a local absolute "
                "path (e.g. a screenshot you just captured at /tmp/shot.png) or an "
                "http(s) image URL, and get back a 1-3 sentence text description "
                "from a vision-capable model. Use this INSTEAD of trying to inline "
                "an image on a model that rejects image input (deepseek-v4-flash "
                "family) — the image never reaches the text-only upstream. "
                "Exactly one of path or url is required."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to a local image file",
                    },
                    "url": {
                        "type": "string",
                        "description": "http(s) URL of an image",
                    },
                },
                "anyOf": [{"required": ["path"]}, {"required": ["url"]}],
            },
        },
    ]


def vision_analyze(name: str, args: dict[str, Any]) -> str:
    """Describe an image (path or url) via the configured vision provider chain.

    Runs synchronously in the MCP stdio worker thread: the vision subagent is a
    one-shot ``AcpClient`` on the configured vision fallback chain (default
    ``cmc/mimo-v2.5``) against the same router proxy the main session uses (or
    each ``vision_providers`` entry's own Anthropic-compatible endpoint), and
    is torn down after the turn. A text-only main model never sees the image —
    only the returned description.
    """
    args = validate_tool_args(args, VISION_ANALYZE_SCHEMA)
    ref = args.get("path") or args.get("url") or ""
    cfg = KiroCrewConfig.load()
    vision_fallback = (cfg.agent.vision_fallback_model or "").strip() or "cmc/mimo-v2.5"

    # Mirror the provider factory's env wiring for the vision subagent: the
    # router base URL + API key (config key > ANTHROPIC_API_KEY env >
    # CLIPROXY_API_KEY env, exactly the loader's precedence). A harness is
    # selected at agent.acp_backend, never agent.provider (harness-parity).
    backend = cfg.agent.acp_backend if cfg.agent.acp_backend in ("claude", "opencode") else ""
    env: dict[str, str] = {}
    base_url = (cfg.agent.provider_base_url or "").strip()
    api_key = (
        (cfg.agent.provider_api_key or "").strip()
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("CLIPROXY_API_KEY")
    )
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    if backend == "opencode":
        env.setdefault("OPENCODE_API_FORMAT", cfg.agent.provider_api_format or "openai")

    providers = resolve_vision_providers(
        vision_providers=list(cfg.agent.vision_providers or []),
        vision_fallback_model=vision_fallback,
        main_env=env,
        main_backend=backend,
    )
    if not providers:
        return "Error: no vision provider configured"

    # For a local path, verify readability + sensitive-path gate up front so a
    # bad ref returns a clean error instead of a subagent spawn failure.
    if args.get("path"):
        p = Path(ref)
        if not p.is_file():
            return f"Error: no such file: {ref}"
        try:
            from kiro_crew.hooks import safe_read_file_bytes

            if safe_read_file_bytes(str(p)) is None:
                return f"Error: image read refused (sensitive path): {ref}"
        except Exception:
            # Fall through to the subagent which surfaces its own error.
            pass

    try:
        description = asyncio.run(
            describe_image_via_chain(
                ref,
                providers,
                sandbox_mode=cfg.agent.sandbox,
            )
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean tool error
        return f"Error: vision describe failed: {exc}"
    if not description or description == "unavailable":
        return "Error: vision describe failed (no description returned)"
    return description


HANDLERS: dict[str, Callable[[str, dict[str, Any]], str]] = {
    "vision_analyze": vision_analyze,
}
