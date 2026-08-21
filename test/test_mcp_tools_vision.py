"""Tests for the fork's ``vision_analyze`` MCP tool.

The tool is the text-only escape hatch: when the main router model rejects
image input, this describes the image on a separate vision-capable model so
the image itself never reaches the rejecting upstream. Every branch here is a
way that can go wrong quietly — no provider configured, an unreadable or
sensitive path, a chain that raises, a chain that returns nothing — and each
must come back as a clean tool error rather than a spawn failure or a silent
empty answer.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from kiro_crew.mcp_tools import vision


def _cfg(**agent):
    base = dict(
        vision_fallback_model="cmc/mimo-v2.5",
        acp_backend="claude",
        provider_base_url="http://127.0.0.1:8317",
        provider_api_key="sekret",
        provider_api_format="openai",
        vision_providers=[],
        sandbox="off",
    )
    base.update(agent)
    return SimpleNamespace(agent=SimpleNamespace(**base))


@pytest.fixture
def wired(monkeypatch):
    """Patch the module's collaborators; yield the mocks the tests steer."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLIPROXY_API_KEY", raising=False)
    with (
        patch.object(vision, "KiroCrewConfig") as cfg,
        patch.object(vision, "resolve_vision_providers") as resolve,
        patch.object(vision, "describe_image_via_chain") as describe,
        patch.object(vision.mcp_core, "sel") as sel,
        patch.object(vision.mcp_core, "_resolve_session_key", return_value="s1"),
    ):
        cfg.load.return_value = _cfg()
        resolve.return_value = [{"model": "cmc/mimo-v2.5"}]
        sel.return_value = MagicMock()
        yield SimpleNamespace(cfg=cfg, resolve=resolve, describe=describe, sel=sel)


def test_schema_advertises_exactly_one_of_path_or_url():
    (tool,) = vision.schemas()
    assert tool["name"] == "vision_analyze"
    assert vision.HANDLERS["vision_analyze"] is vision.vision_analyze
    any_of = tool["inputSchema"]["anyOf"]
    assert {"required": ["path"]} in any_of and {"required": ["url"]} in any_of


def test_url_ref_is_described_and_audited(wired):
    async def _ok(*a, **k):
        return "a red bicycle"

    wired.describe.side_effect = _ok
    out = vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    assert out == "a red bicycle"
    wired.sel.return_value.log_tool_invocation.assert_called_with(
        session_key="s1", source="mcp", tool_name="vision_analyze", outcome="success"
    )


def test_router_credentials_reach_the_subagent(wired):
    """The vision subagent must inherit the router endpoint, not default to Bedrock."""

    async def _ok(*a, **k):
        return "ok"

    wired.describe.side_effect = _ok
    vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    env = wired.resolve.call_args.kwargs["main_env"]
    assert env["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:8317"
    assert env["ANTHROPIC_API_KEY"] == "sekret"
    assert wired.resolve.call_args.kwargs["main_backend"] == "claude"


def test_opencode_backend_carries_its_wire_format(wired):
    wired.cfg.load.return_value = _cfg(acp_backend="opencode")

    async def _ok(*a, **k):
        return "ok"

    wired.describe.side_effect = _ok
    vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    assert wired.resolve.call_args.kwargs["main_env"]["OPENCODE_API_FORMAT"] == "openai"


def test_env_api_key_is_the_fallback_when_config_has_none(wired, monkeypatch):
    monkeypatch.setenv("CLIPROXY_API_KEY", "from-env")
    wired.cfg.load.return_value = _cfg(provider_api_key="")

    async def _ok(*a, **k):
        return "ok"

    wired.describe.side_effect = _ok
    vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    assert wired.resolve.call_args.kwargs["main_env"]["ANTHROPIC_API_KEY"] == "from-env"


def test_no_configured_provider_is_a_clean_error(wired):
    wired.resolve.return_value = []
    out = vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    assert out == "Error: no vision provider configured"
    wired.describe.assert_not_called()


def test_missing_local_file_never_spawns_a_subagent(wired, tmp_path):
    out = vision.vision_analyze("vision_analyze", {"path": str(tmp_path / "nope.png")})
    assert out.startswith("Error: no such file:")
    wired.describe.assert_not_called()


def test_sensitive_path_refusal_is_reported_not_described(wired, tmp_path):
    img = tmp_path / "secret.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    with patch("kiro_crew.hooks.safe_read_file_bytes", return_value=None):
        out = vision.vision_analyze("vision_analyze", {"path": str(img)})
    assert out.startswith("Error: image read refused (sensitive path):")
    wired.describe.assert_not_called()


def test_readable_local_file_is_described(wired, tmp_path):
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    async def _ok(*a, **k):
        return "a screenshot of a terminal"

    wired.describe.side_effect = _ok
    with patch("kiro_crew.hooks.safe_read_file_bytes", return_value=b"x"):
        out = vision.vision_analyze("vision_analyze", {"path": str(img)})
    assert out == "a screenshot of a terminal"


def test_chain_exception_is_surfaced_and_audited(wired):
    async def _boom(*a, **k):
        raise RuntimeError("endpoint down")

    wired.describe.side_effect = _boom
    out = vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    assert out == "Error: vision describe failed: endpoint down"
    wired.sel.return_value.log_tool_invocation.assert_called_with(
        session_key="s1", source="mcp", tool_name="vision_analyze", outcome="error"
    )


@pytest.mark.parametrize("answer", ["", "unavailable"])
def test_empty_description_is_an_error_not_a_silent_pass(wired, answer):
    async def _nothing(*a, **k):
        return answer

    wired.describe.side_effect = _nothing
    out = vision.vision_analyze("vision_analyze", {"url": "https://x.test/a.png"})
    assert out == "Error: vision describe failed (no description returned)"
    wired.sel.return_value.log_tool_invocation.assert_called_with(
        session_key="s1", source="mcp", tool_name="vision_analyze", outcome="no_description"
    )
