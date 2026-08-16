"""Tests for /api/provider/test (api_provider_test) credential hygiene.

The endpoint probes ``{url}/v1/models``. When ``use_stored`` is set it
attaches the saved ``agent.provider_api_key`` — these tests pin the guard
that the stored key is only ever sent to the host:port it was saved for,
that non-http(s) schemes are rejected, and that redirects are not followed
with the credential attached.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from kiro_crew.dashboard.handlers.agents import api_provider_test


def _fake_config(base_url="http://127.0.0.1:8317", key="sekret"):
    return SimpleNamespace(agent=SimpleNamespace(provider_base_url=base_url, provider_api_key=key))


class _NoNetwork:
    """Fails the test if the handler opens an outbound session."""

    def __call__(self, *a, **kw):  # pragma: no cover - only on regression
        raise AssertionError("outbound request attempted before validation")


class _CapturingSession:
    """Stub aiohttp.ClientSession recording the GET it serves."""

    calls: list = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def get(self, url, **kw):
        _CapturingSession.calls.append((url, kw))

        class _Resp:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def json(self):
                return {"data": [{"id": "m1"}]}

        return _Resp()


async def _post(body, session_cls):
    app = web.Application()
    app.router.add_post("/api/provider/test", api_provider_test)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        with (
            patch("kiro_crew.dashboard.handlers.agents.KiroCrewConfig") as cfg,
            patch("aiohttp.ClientSession", session_cls),
        ):
            cfg.load.return_value = _fake_config()
            resp = await client.post("/api/provider/test", json=body)
            return resp.status, await resp.json()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_stored_key_refused_for_foreign_host():
    status, data = await _post(
        {"url": "http://evil.example.com:8317", "use_stored": True}, _NoNetwork()
    )
    assert status == 400
    assert data["code"] == "stored_key_host_mismatch"


@pytest.mark.asyncio
async def test_non_http_scheme_rejected():
    status, data = await _post({"url": "ftp://127.0.0.1/pwn", "use_stored": True}, _NoNetwork())
    assert status == 400
    assert data["code"] == "url_scheme"


@pytest.mark.asyncio
async def test_stored_key_sent_to_saved_host_without_redirects():
    _CapturingSession.calls = []
    status, data = await _post({"url": "http://127.0.0.1:8317", "use_stored": True}, _CapturingSession)
    assert status == 200 and data["ok"] is True and data["models"] == ["m1"]
    (url, kw), = _CapturingSession.calls
    assert url == "http://127.0.0.1:8317/v1/models"
    assert kw["allow_redirects"] is False
    assert kw["headers"]["Authorization"] == "Bearer sekret"
