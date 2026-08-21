"""Tests for the fork's ``browse_outline`` / ``browse_search`` MCP tools.

Both take a raw browser_snapshot — an accessibility tree that can be tens of
thousands of tokens — and hand back a compressed view a model can afford to
read. They are the fork's own ports into upstream's modular ``mcp_tools``
layout, so the properties that matter are the ones the port could silently
drop: the redaction pass over whatever the page contained, and the audit
record. A snapshot is untrusted page text, so anything credential-shaped in it
must not survive into the model's context.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from kiro_crew.mcp_tools import browser


@pytest.fixture
def audited():
    with (
        patch.object(browser.mcp_core, "sel") as sel,
        patch.object(browser.mcp_core, "_resolve_session_key", return_value="s1"),
    ):
        sel.return_value = MagicMock()
        yield sel


SNAPSHOT = """
button "Sign in"
link "Docs" url=https://example.test/docs
text "token: ghp_0123456789abcdefghijklmnopqrstuvwxyzAB"
button "Settings"
"""


def test_outline_compresses_and_audits(audited):
    out = browser.browse_outline("browse_outline", {"snapshot": SNAPSHOT, "max_lines": 10})
    assert isinstance(out, str)
    audited.return_value.log_tool_invocation.assert_called_with(
        session_key="s1", source="mcp", tool_name="browse_outline", outcome="success"
    )


def test_outline_redacts_credentials_found_in_page_text(audited):
    out = browser.browse_outline("browse_outline", {"snapshot": SNAPSHOT, "max_lines": 50})
    assert "ghp_0123456789abcdefghijklmnopqrstuvwxyzAB" not in out


def test_search_returns_matches_and_audits(audited):
    out = browser.browse_search(
        "browse_search", {"snapshot": SNAPSHOT, "query": "Settings", "max_results": 5}
    )
    assert isinstance(out, str)
    audited.return_value.log_tool_invocation.assert_called_with(
        session_key="s1", source="mcp", tool_name="browse_search", outcome="success"
    )


def test_search_redacts_credentials_in_the_matched_text(audited):
    out = browser.browse_search(
        "browse_search", {"snapshot": SNAPSHOT, "query": "token", "max_results": 5}
    )
    assert "ghp_0123456789abcdefghijklmnopqrstuvwxyzAB" not in out


def test_both_tolerate_an_empty_snapshot(audited):
    assert isinstance(browser.browse_outline("browse_outline", {}), str)
    assert isinstance(browser.browse_search("browse_search", {}), str)


def test_handlers_expose_both_tools():
    for name in ("browse_outline", "browse_search"):
        assert name in browser.HANDLERS
