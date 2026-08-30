"""The router path's model-id contract: spelling, and what ``auto`` means.

Both properties here were live failures against a 9router install, and both
were invisible to the existing tests because those assume CLIProxyAPI — a
router that serves RAW ids and rejects prefixes. 9router is the mirror image:
it publishes ``cx/gpt-5.5`` and answers the stripped spelling with
``{"code": "model_not_found"}``. Anything that hardcodes one router's
convention breaks the other, so the router's own catalog is the authority.
"""

from __future__ import annotations

import pytest

from kiro_crew.acp import client as c


@pytest.fixture(autouse=True)
def _clean_catalog():
    """Catalog state is module-level; keep each test independent."""
    saved_ids, saved_cache = set(c._ROUTER_CATALOG_IDS), dict(c._ROUTER_CATALOG_CACHE)
    c._ROUTER_CATALOG_IDS.clear()
    c._ROUTER_CATALOG_CACHE.clear()
    yield
    c._ROUTER_CATALOG_IDS.clear()
    c._ROUTER_CATALOG_IDS.update(saved_ids)
    c._ROUTER_CATALOG_CACHE.clear()
    c._ROUTER_CATALOG_CACHE.update(saved_cache)


class TestWireSpelling:
    def test_an_id_the_router_advertised_is_sent_verbatim(self):
        """9router: stripping its own published id is what produced 404s."""
        c._ROUTER_CATALOG_IDS.add("cx/gpt-5.5")
        assert c.strip_router_model_prefix("cx/gpt-5.5") == "cx/gpt-5.5"

    def test_unknown_router_still_gets_the_raw_id(self):
        """CLIProxyAPI: nothing advertised, so the historical strip stands."""
        assert c.strip_router_model_prefix("cmc/deepseek-v4-pro") == "deepseek/deepseek-v4-pro"

    def test_catalog_knowledge_does_not_leak_across_routers(self):
        """A prefix one router publishes must not suppress stripping generally."""
        c._ROUTER_CATALOG_IDS.add("cx/gpt-5.5")
        assert c.strip_router_model_prefix("cmc/deepseek-v4-pro") == "deepseek/deepseek-v4-pro"


class TestCatalogPassthrough:
    @pytest.mark.parametrize(
        "served",
        ["cx/gpt-5.5-review", "cx/gpt-5.3-codex-spark", "cc/claude-opus-5"],
    )
    def test_a_model_the_builtin_table_never_heard_of_still_reaches_the_picker(self, served):
        """Routers add models constantly; a stale table must not hide them."""
        assert c.prefixed_router_model_id(served, "") == served

    def test_an_unrecognised_namespace_is_still_refused(self):
        """Pass-through is scoped to known provider prefixes, not everything."""
        assert c.prefixed_router_model_id("bogus/whatever", "") is None


class TestAutoOnARouter:
    """``auto`` has no meaning without kiro-cli's entitlement service.

    Left unresolved, Claude Code picks its OWN default (claude-opus-5[1m]) —
    a Bedrock id no router serves — and every turn dies with model_not_found.
    """

    def _client(self, monkeypatch, served):
        monkeypatch.setattr(c, "load_router_catalog_ids", lambda *a, **k: list(served))
        return c.AcpClient(
            work_dir="/tmp/x",
            acp_backend=c.ACP_BACKEND_CLAUDE,
            model="auto",
            extra_env={"ANTHROPIC_BASE_URL": "http://localhost:20128"},
        )

    def test_auto_resolves_to_the_routers_first_model(self, monkeypatch):
        cl = self._client(monkeypatch, ["cc/claude-opus-5", "cx/gpt-5.5"])
        assert cl._extra_env["ANTHROPIC_MODEL"] == "cc/claude-opus-5"

    def test_the_resolved_model_is_also_what_gets_pinned(self, monkeypatch):
        """settings.local.json is authoritative OVER the env var, and it reads
        self._model — resolving only the env left "auto" pinned and the
        fallback happened anyway."""
        cl = self._client(monkeypatch, ["cc/claude-opus-5"])
        assert cl._model == "cc/claude-opus-5"

    def test_an_unreachable_router_leaves_auto_alone(self, monkeypatch):
        """A probe failure must not invent a model or block the spawn."""
        cl = self._client(monkeypatch, [])
        assert cl._model == "auto"
        assert "ANTHROPIC_MODEL" not in cl._extra_env

    def test_an_explicit_pick_is_never_overridden_by_the_catalog(self, monkeypatch):
        monkeypatch.setattr(c, "load_router_catalog_ids", lambda *a, **k: ["cc/claude-opus-5"])
        cl = c.AcpClient(
            work_dir="/tmp/x",
            acp_backend=c.ACP_BACKEND_CLAUDE,
            model="cx/gpt-5.5",
            extra_env={"ANTHROPIC_BASE_URL": "http://localhost:20128"},
        )
        assert cl._model == "cx/gpt-5.5"
