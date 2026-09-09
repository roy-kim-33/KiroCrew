"""Tests for the claude_code model list assembled by /api/models.

The live backend's advertised set is authoritative and used VERBATIM --
``_advertised_cc_models`` no longer remaps a modelId through the model
registry's canonical keys. That remap conflated Claude Code's own short
config-option aliases (``opus``, ``sonnet``) with Bedrock-flavored canonical
keys meant for a different id shape (kiro-cli/acp's own
``global.anthropic.claude-opus-4-8[1m]``-style ids), which a native
claude_code session never advertises in the first place. Selecting the
remapped row sent a value the adapter flatly rejected ("Invalid value for
config option model") -- confirmed live for both ``opus`` and ``sonnet``,
the two most commonly picked non-default models.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from kiro_crew.acp.client import AcpClient
from kiro_crew.config.paths import config_dir
from kiro_crew.dashboard.handlers.agents import (
    _LAST_CC_ROWS,
    _advertised_cc_models,
    _cc_models,
    _cc_models_response,
    _normalize_model_key,
)


def _request_with_providers(providers: dict) -> MagicMock:
    """Fake aiohttp request whose sessions.active_providers() yields `providers`.

    Mirrors the real SessionManager API (active_providers()) so the test can't
    pass against an attribute the production object doesn't have.
    """
    sessions = SimpleNamespace(active_providers=lambda: list(providers.values()))
    state = SimpleNamespace(sessions=sessions)
    req = MagicMock()
    req.app.__getitem__.return_value = state
    return req


def _FakeProvider(models, *, backend=None):
    """A provider double carrying a REAL capability record, not an identity flag.

    ``_advertised_cc_models`` selects a session by
    ``SessionCapabilities.resolves_model_from_advertised_list``, and
    ``capabilities_of`` requires a genuine record: a ``MagicMock(spec=...)``'s
    attributes are all truthy, so an attribute-shaped assertion would let this
    double claim every capability at once. Setting the real record is what makes
    the double describe a backend that exists.
    """
    from kiro_crew.acp_backends import ACP_BACKEND_CLAUDE
    from kiro_crew.agent_sdk.capabilities import capabilities_for
    from kiro_crew.providers.acp import AcpProvider

    provider = MagicMock(spec=AcpProvider)
    provider.capabilities = capabilities_for(ACP_BACKEND_CLAUDE if backend is None else backend)
    provider.available_models.return_value = models
    return provider


class TestAdvertisedCcModels:
    def test_maps_modelid_name_description(self):
        # An unknown provider id (not in the registry) passes through unchanged.
        prov = _FakeProvider(
            [
                {"modelId": "claude-sonnet-4-6", "name": "Sonnet 4.6", "description": "Everyday"},
            ]
        )
        out = _advertised_cc_models(_request_with_providers({"s": prov}))
        assert out == [
            {
                "model_name": "claude-sonnet-4-6",
                "display_name": "Sonnet 4.6",
                "description": "Everyday",
            }
        ]

<<<<<<< HEAD
    def test_short_alias_passes_through_unremapped(self):
        # A native claude_code session's own config-option value ("opus") must
        # reach the picker as-is, NOT folded onto a registry canonical key
        # ("opus-4.8-1m") -- that key is a Bedrock-shaped id shape this session
        # never advertises, and selecting the remapped row is rejected by the
        # adapter (verified live). The registry entry that used to own this
        # alias is untouched -- this only asserts the picker no longer
        # detours through it.
=======
    def test_known_provider_id_kept_verbatim(self):
        # The advertised id is the value set_config_option accepts.
>>>>>>> upstream/main
        prov = _FakeProvider(
            [{"modelId": "opus", "name": "Opus", "description": "Opus 5 · ..."}]
        )
        out = _advertised_cc_models(_request_with_providers({"s": prov}))
<<<<<<< HEAD
        assert out[0]["model_name"] == "opus"
=======
        assert out[0]["model_name"] == "global.anthropic.claude-opus-4-8[1m]"
>>>>>>> upstream/main

    def test_empty_when_no_active_sessions(self):
        assert _advertised_cc_models(_request_with_providers({})) == []

    def test_skips_provider_without_accessor(self):
        prov = _FakeProvider([])
        prov.available_models = None
        out = _advertised_cc_models(_request_with_providers({"s": prov}))
        assert out == []

    def test_skips_non_claude_providers(self):
        prov = _FakeProvider(
            [{"modelId": "claude-opus-5", "name": "Opus 5", "description": ""}],
            backend="",
        )
        out = _advertised_cc_models(_request_with_providers({"s": prov}))
        assert out == []

    def test_newest_session_wins_over_a_lingering_older_one(self):
        # dict insertion order == session creation order (active_providers()'s
        # real contract). A long-running tab that switched providers before
        # this fetch can still have the OLD session resident in `_sessions` --
        # reading oldest-first would serve its stale catalog forever, never
        # self-healing, which reads exactly like "still needs a reload" even
        # though the new session already has the right answer.
        old = _FakeProvider([{"modelId": "old-router-model", "name": "Old", "description": ""}])
        new = _FakeProvider([{"modelId": "claude-native-model", "name": "New", "description": ""}])
        out = _advertised_cc_models(_request_with_providers({"old": old, "new": new}))
        assert out == [
            {"model_name": "claude-native-model", "display_name": "New", "description": ""}
        ]


class TestRouterModelWhitelistMerge:
    """The router-model whitelist merges a local model_whitelist.json.

    _isolate_kirocrew_home (autouse in conftest) pins config_dir() to a per-test
    tmp dir, so writing model_whitelist.json there exercises the merge path
    without touching the developer's real home.
    """

    def _write_whitelist(self, models):
        path = config_dir() / "model_whitelist.json"
        path.write_text(json.dumps({"models": models}), encoding="utf-8")

    def test_local_json_models_merge_into_defaults(self):
        self._write_whitelist(["cmc/meta/muse-spark-1.2-contributor"])
        merged = AcpClient.router_model_whitelist()
        # built-in defaults still present
        assert "oc/deepseek-v4-flash" in merged
        # local override added
        assert "cmc/meta/muse-spark-1.2-contributor" in merged

    def test_missing_file_degrades_to_defaults(self):
        # no file written -> only built-in defaults, no error
        merged = AcpClient.router_model_whitelist()
        assert "oc/deepseek-v4-flash" in merged
        assert "cmc/meta/muse-spark-1.2-contributor" not in merged

    def test_corrupt_file_degrades_to_defaults(self):
        path = config_dir() / "model_whitelist.json"
        path.write_text("{not json", encoding="utf-8")
        merged = AcpClient.router_model_whitelist()
        assert "oc/deepseek-v4-flash" in merged
        assert "cmc/meta/muse-spark-1.2-contributor" not in merged

    def test_response_includes_local_override_models(self, monkeypatch):
        # The whitelist is a last resort now, reachable only when a router IS
        # configured and both the live session and the direct probe come up
        # empty -- so this needs a base_url, and the probe forced to fail
        # (an unreachable router), to still exercise that final fallback.
        import aiohttp

        from kiro_crew.config.loader import KiroCrewConfig

        self._write_whitelist(["cmc/meta/muse-spark-1.2-contributor"])
        cfg = KiroCrewConfig()
        cfg.agent = SimpleNamespace(
            provider_base_url="http://localhost:20128",
            provider_api_key="sk-x",
            model_whitelist=[],
            acp_backend="claude",
        )
        monkeypatch.setattr("kiro_crew.dashboard.handlers.agents.KiroCrewConfig.load", lambda: cfg)
        session = _FakeSession()
        session._fail = True
        monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)

        async def run():
            return await _cc_models_response(_request_with_providers({}))

        resp = _run_async(run())
        body = resp.body.decode("utf-8") if isinstance(resp.body, bytes) else resp.body
        payload = json.loads(body)
        names = {m["model_name"] for m in payload}
        assert "cmc/meta/muse-spark-1.2-contributor" in names
        assert "oc/deepseek-v4-flash" in names


class _FakeResp:
    def __init__(self, data):
        self.status = 200
        self._data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def json(self):
        return self._data


class _FakeSession:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def get(self, url, headers=None):
        if self._fail:
            raise _Boom("offline")
        return _FakeResp(
            {
                "data": [
                    {"id": "deepseek-v4-flash", "display_name": "DeepSeek V4 Flash"},
                    {"id": "gpt-5.6-sol", "display_name": "GPT 5.6 Sol"},
                ]
            }
        )


class _Boom(Exception):
    pass


def _opencode_config(monkeypatch):
    from kiro_crew.config.loader import KiroCrewConfig

    cfg = KiroCrewConfig()
    cfg.agent = SimpleNamespace(
        provider="opencode",
        provider_base_url="http://localhost:8317",
        provider_api_key="sk-x",
        provider_api_format="openai",
        model_whitelist=[],
    )
    monkeypatch.setattr("kiro_crew.dashboard.handlers.agents.KiroCrewConfig.load", lambda: cfg)
    return cfg


def test_opencode_models_response_uses_provider_catalog(monkeypatch):
    """opencode backend: /api/models serves the provider's /v1/models rows."""
    import aiohttp

    from kiro_crew.dashboard.handlers.agents import _opencode_models_response

    _opencode_config(monkeypatch)
    session = _FakeSession()
    session._fail = False
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)

    async def run():
        return await _opencode_models_response(MagicMock())

    resp = _run_async(run())
    rows = json.loads(resp.text)
    ids = [r["model_id"] for r in rows]
    assert "deepseek-v4-flash" in ids
    assert "gpt-5.6-sol" in ids
    by_id = {r["model_id"]: r for r in rows}
    assert by_id["deepseek-v4-flash"]["context_window_tokens"] > 0


def test_opencode_models_response_falls_back_to_whitelist(monkeypatch):
    """Unreachable provider endpoint still yields the curated whitelist."""
    import aiohttp

    from kiro_crew.dashboard.handlers.agents import _opencode_models_response

    _opencode_config(monkeypatch)
    session = _FakeSession()
    session._fail = True
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)

    async def run():
        return await _opencode_models_response(MagicMock())

    resp = _run_async(run())
    rows = json.loads(resp.text)
    assert len(rows) > 0


def _run_async(coro):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(coro)


def test_opencode_models_response_filters_to_whitelist(monkeypatch):
    """The user model allowlist narrows the provider catalog."""
    import aiohttp

    from kiro_crew.dashboard.handlers.agents import _opencode_models_response

    cfg = _opencode_config(monkeypatch)
    cfg.agent.model_whitelist = ["gpt-5.6-sol"]
    session = _FakeSession()
    session._fail = False
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)

    async def run():
        return await _opencode_models_response(MagicMock())

    resp = _run_async(run())
    rows = json.loads(resp.text)
    ids = [r["model_id"] for r in rows]
    assert ids == ["gpt-5.6-sol"]


def _cc_router_config(monkeypatch, base_url="http://localhost:20128"):
    from kiro_crew.config.loader import KiroCrewConfig

    cfg = KiroCrewConfig()
    cfg.agent = SimpleNamespace(
        provider_base_url=base_url,
        provider_api_key="sk-x",
        model_whitelist=[],
        # Real configs always carry this on the branch that reaches
        # _cc_models_response (it only runs when acp_backend is claude), and it
        # is half the key the per-lane last-good store is scoped by.
        acp_backend="claude",
    )
    monkeypatch.setattr("kiro_crew.dashboard.handlers.agents.KiroCrewConfig.load", lambda: cfg)
    return cfg


class TestCcModelsResponseRace:
    """Both reported bugs traced back to one race: switching backend/preset
    invalidates the model-list query the instant the config PATCH resolves,
    well before any session has (re)spawned against the new backend and
    captured its real catalog. `_cc_models_response` used to have no fallback
    for that window other than a generic, cross-provider static whitelist --
    wrong for whichever router is actually configured, and actively
    misleading on the native lane, which the whitelist was never built for.
    """

    @pytest.fixture(autouse=True)
    def _clear_lane_memory(self):
        """The last-good store is module state, so it outlives a test and would
        otherwise answer a later one that expects an empty lane."""
        _LAST_CC_ROWS.clear()
        yield
        _LAST_CC_ROWS.clear()

    def test_native_lane_serves_its_own_last_list_during_the_respawn_window(self, monkeypatch):
        """The reported "9router -> native empties the picker" bug.

        Native has no session-independent source: the router lane can always
        probe {base_url}/v1/models, but native's only source is a live
        session's advertised list, and switching provider tears every session
        down before respawning one. That window returned [], so the picker
        dropped to the bare "auto" sentinel for several seconds and read as
        the switch having wiped the model list.

        The remembered rows must be the NATIVE lane's own -- keyed by
        (acp_backend, base_url), so a router's catalog can never answer here.
        """
        prov = _FakeProvider(
<<<<<<< HEAD
=======
            [{"modelId": "global.anthropic.claude-sonnet-4-6[1m]", "name": "Sonnet 4.6"}]
        )
        out = _cc_models(_request_with_providers({"s": prov}))
        names = [m["model_name"] for m in out]
        assert names[0] == "auto"
        assert "global.anthropic.claude-sonnet-4-6[1m]" in names
        # The flagship is in the registry but was NOT advertised → filtered out.
        assert "opus-4.8-1m" not in names
        assert "opus-4.8" not in names

    def test_registry_display_name_wins_for_survivors(self):
        """Filtering keeps the registry's cleaner display name, not the adapter's,
        while the row's wire value stays the advertised id the backend accepts."""
        prov = _FakeProvider(
            [{"modelId": "global.anthropic.claude-sonnet-4-6[1m]", "name": "sonnet-4-6-v1-ugly"}]
        )
        out = _cc_models(_request_with_providers({"s": prov}))
        row = next(m for m in out if m["model_name"] == "global.anthropic.claude-sonnet-4-6[1m]")
        assert row["display_name"] == "Sonnet 4.6 (1M context)"

    def test_unknown_advertised_models_still_pass_through(self):
        # Forward-compat: a model the registry does not list is still offered when
        # the backend advertises it, otherwise a newly-served model is unreachable.
        prov = _FakeProvider(
>>>>>>> upstream/main
            [
                {"modelId": "opus", "name": "Opus", "description": ""},
                {"modelId": "sonnet", "name": "Sonnet", "description": ""},
            ]
        )
        _cc_router_config(monkeypatch, base_url="")

        async def run(req):
            return await _cc_models_response(req)

        # A live native session advertises its list -> remembered for this lane.
        first = json.loads(_run_async(run(_request_with_providers({"s": prov}))).text)
        assert {r["model_id"] for r in first} == {"opus", "sonnet"}

        # Switch tears the session down: nothing advertised, no router to probe.
        during = json.loads(_run_async(run(_request_with_providers({}))).text)
        assert {r["model_id"] for r in during} == {"opus", "sonnet"}

<<<<<<< HEAD
    def test_a_routers_list_never_answers_for_the_native_lane(self, monkeypatch):
        """Scoping proof: the store is keyed by lane, so the list a router
        advertised cannot be served once the base URL is cleared. Serving it
        is the cross-provider bug in its server-side form -- router ids are
        not selectable on native."""
        prov = _FakeProvider([{"modelId": "oc/kimi-k3", "name": "K3", "description": ""}])
        _cc_router_config(monkeypatch, base_url="http://localhost:20128")
        served = json.loads(_run_async(_cc_models_response(_request_with_providers({"s": prov}))).text)
        assert {r["model_id"] for r in served} == {"oc/kimi-k3"}

        # Base URL cleared (-> native lane) and no session yet: the router's
        # remembered list belongs to a different lane and must not appear.
        _cc_router_config(monkeypatch, base_url="")
        native = json.loads(_run_async(_cc_models_response(_request_with_providers({}))).text)
        assert native == []
=======
    def test_no_duplicate_when_adapter_lists_known_model(self):
        # The adapter advertises provider ids that ARE in the registry; each
        # collapses to one row carrying the advertised wire id (registry display).
        prov = _FakeProvider(
            [
                {
                    "modelId": "global.anthropic.claude-sonnet-4-6[1m]",
                    "name": "Sonnet 4.6",
                    "description": "",
                },
                {
                    "modelId": "global.anthropic.claude-opus-4-8[1m]",
                    "name": "Opus 4.8",
                    "description": "",
                },
            ]
        )
        out = _cc_models(_request_with_providers({"s": prov}))
        names = [m["model_name"] for m in out]
        assert names.count("global.anthropic.claude-opus-4-8[1m]") == 1
        assert names.count("global.anthropic.claude-sonnet-4-6[1m]") == 1

    def test_registry_row_keeps_friendly_display_name(self):
        # When the adapter advertises a known id, the registry's friendly display
        # name wins while the wire value stays the advertised id.
        prov = _FakeProvider(
            [
                {
                    "modelId": "global.anthropic.claude-opus-4-8[1m]",
                    "name": "Opus 4.8",
                    "description": "",
                },
            ]
        )
        out = _cc_models(_request_with_providers({"s": prov}))
        opus48 = next(m for m in out if m["model_name"] == "global.anthropic.claude-opus-4-8[1m]")
        assert opus48["display_name"] == "Opus 4.8 (1M context)"
>>>>>>> upstream/main

    def test_live_probe_used_when_nothing_advertised_yet(self, monkeypatch):
        """A router configured but not yet session-captured: probe it directly
        rather than falling back to the whitelist immediately. This is the
        exact "native -> 9router: updates immediately, but to the wrong
        models" bug -- the whitelist's `ag/`, `cmc/`, `oc/`, `ol/` entries have
        nothing to do with the router actually configured."""
        import aiohttp

        _cc_router_config(monkeypatch)
        session = _FakeSession()
        session._fail = False
        monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)

        async def run():
            return await _cc_models_response(_request_with_providers({}))

        resp = _run_async(run())
        rows = json.loads(resp.text)
        ids = {r["model_id"] for r in rows}
        # _FakeSession's fixed catalog -- proves these came from the probe,
        # not the static whitelist (which does not contain these bare ids).
        assert ids == {"deepseek-v4-flash", "gpt-5.6-sol"}

    def test_advertised_session_still_wins_over_the_probe(self, monkeypatch):
        """A live session's captured list is the freshest, tier-aware signal
        and must not be overridden by a same-moment probe of the router."""
        import aiohttp

        _cc_router_config(monkeypatch)
        session = _FakeSession()
        session._fail = False
        monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)
        prov = _FakeProvider([{"modelId": "cc/claude-opus-5", "name": "Opus 5", "description": ""}])

        async def run():
            return await _cc_models_response(_request_with_providers({"s": prov}))

        resp = _run_async(run())
        rows = json.loads(resp.text)
        ids = {r["model_id"] for r in rows}
        assert ids == {"cc/claude-opus-5"}

    def test_native_lane_returns_empty_rather_than_the_whitelist(self, monkeypatch):
        """No router configured, nothing advertised yet: this is the "9router
        -> native: fails to update" bug's data-layer half. The whitelist is
        built from router-prefixed ids (`ag/`, `cmc/`, ...), which are not
        Claude Code's own alias names (`opus`, `sonnet`, ...) -- confidently
        serving it is a namespace mismatch, not a real answer. An empty
        result lets the frontend's existing "still loading" state show
        instead of 94 models this account cannot select."""
        _cc_router_config(monkeypatch, base_url="")

        async def run():
            return await _cc_models_response(_request_with_providers({}))

        resp = _run_async(run())
        rows = json.loads(resp.text)
        assert rows == []

    def test_whitelist_is_the_true_last_resort_when_the_router_is_unreachable(self, monkeypatch):
        """A router IS configured, nothing advertised, AND the probe itself
        fails (router down): only then does the generic whitelist step in,
        so a genuinely cold dashboard still shows something selectable."""
        import aiohttp

        _cc_router_config(monkeypatch)
        session = _FakeSession()
        session._fail = True
        monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: session)

        async def run():
            return await _cc_models_response(_request_with_providers({}))

        resp = _run_async(run())
        rows = json.loads(resp.text)
        assert len(rows) > 0

    def test_configured_default_auto_does_not_insert_blank_row(self):
        # cc_model="auto" round-trips to "" (auto's provider id is empty), which
        # must NOT be inserted as a blank-named row at the top of the dropdown —
        # the "auto" registry row already covers it.
        out = _cc_models(_request_with_providers({}), configured_default="auto")
        names = [m["model_name"] for m in out]
        assert "" not in names
        assert all(m["model_name"] for m in out)
        # the canonical "auto" row is still present, exactly once.
        assert names.count("auto") == 1


class TestNormalizeModelKey:
    """`_normalize_model_key` routes through the canonical registry (#5339).

    Mirror of the frontend `normalizeModelKey` unit tests in
    `website/src/test/model.displayModel.test.ts` -- the two must agree, which is
    the whole point of folding through the shared `model_registry.json`.
    """

    def test_auto_default_and_unset(self):
        # auto/default fold to the sentinel; an unset id stays "" (distinct).
        assert _normalize_model_key(" auto ") == "auto"
        assert _normalize_model_key("default") == "auto"
        assert _normalize_model_key("DEFAULT") == "auto"
        assert _normalize_model_key("") == ""
        assert _normalize_model_key("   ") == ""

    def test_alias_key_and_provider_id_fold_to_one_key(self):
        # An alias, the canonical key, and the claude_code provider id (with or
        # without a routing prefix) all resolve to one canonical key, any case.
        assert _normalize_model_key("claude-opus-4.8") == "opus-4.8-1m"
        assert _normalize_model_key("Claude-Opus-4.8") == "opus-4.8-1m"
        assert _normalize_model_key("opus-4.8-1m") == "opus-4.8-1m"
        assert _normalize_model_key("opus") == "opus-4.8-1m"
        assert _normalize_model_key("global.anthropic.claude-opus-4-8[1m]") == "opus-4.8-1m"
        # The "fold a provider/partition prefix" half of #5339: a regional
        # profile id that is not itself a registry entry folds after the peel.
        assert _normalize_model_key("us.anthropic.claude-opus-4-8[1m]") == "opus-4.8-1m"

    def test_distinct_context_window_variants_stay_apart(self):
        # The old dot->dash fold made both of these `claude-opus-4-8`, equating a
        # 200K model with a 1M one. The registry lists them as separate entries.
        assert _normalize_model_key("claude-opus-4-8") == "opus-4.8"  # 200K
        assert _normalize_model_key("claude-opus-4.8") == "opus-4.8-1m"  # 1M
        assert _normalize_model_key("claude-opus-4-8") != _normalize_model_key("claude-opus-4.8")

    def test_kiro_distinct_models_stay_apart_via_acp_first_fold(self):
        # The claude_code index aliases these onto Sonnet/Opus 4.8 for dropdown
        # dedup, but kiro serves them as DISTINCT real models. Resolving the acp
        # index first (canonical_key's documented order) keeps them apart, so the
        # shared fold cannot equate a Haiku pin with Sonnet 4.6 (a real 1M->200K
        # swap the downgrade flag must catch).
        assert _normalize_model_key("claude-haiku-4.5") == "haiku-4.5"
        assert _normalize_model_key("claude-sonnet-4.5") == "sonnet-4.5"
        assert _normalize_model_key("claude-sonnet-4") == "sonnet-4"
        assert _normalize_model_key("claude-opus-4.6") == "opus-4.6-1m"
        assert _normalize_model_key("claude-sonnet-4.6") == "sonnet-4.6-1m"
        assert _normalize_model_key("claude-haiku-4.5") != _normalize_model_key("claude-sonnet-4.6")
        assert _normalize_model_key("claude-opus-4.6") != _normalize_model_key("claude-opus-4.8")
        # acp-only canonical keys resolve to themselves.
        assert _normalize_model_key("haiku-4.5") == "haiku-4.5"
        assert _normalize_model_key("opus-4.6-1m") == "opus-4.6-1m"

    def test_unregistered_id_uses_the_string_fold(self):
        # GPT/DeepSeek/Qwen and future models are absent from the (Anthropic-only)
        # registry, so they keep the historical trim/lowercase/dot->dash fold.
        assert _normalize_model_key("GPT-5.6") == "gpt-5-6"
        assert _normalize_model_key("deepseek-3.2") == "deepseek-3-2"
        assert _normalize_model_key("claude-opus-5") == "claude-opus-5"
