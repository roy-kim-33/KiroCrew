"""Agent administration HTTP handlers: the facade over :mod:`kiro_crew.dashboard.agent_admin`.

Routes, the handlers package, sibling handlers and tests import and patch every
agents handler through this module. The handler families live in the
``agent_admin`` owners -- ``app_mcp_ownership``, ``agent_config``,
``default_agent``, ``capabilities``, ``template_lineage``, ``fork_publish``,
``agent_detail``, ``roster``, ``installed_agents``, ``crew_records``,
``crew_update``, ``crew_removal`` and ``avatars`` -- and ``agent_admin.compose``
runs them on this module's globals, so a patch of ``agents.<name>`` reaches them.

This module keeps the imports, constants and seams the owners read (``_err500``,
``_sel``, ``_require_owner``, the ``_get_config_lock`` every config writer in the
dashboard takes), the config schema route, the model and picker reads
(``GET /api/models`` with its catalog cache and entitlement narrowing, effort
levels, slash commands) with the crew model-pin checks, and the two routes
repository guards read here by path: ``GET /api/agents`` and the avatar ``GET``.
New work goes to the owner of its family;
``docs/system-specs/modules/learn-cron-dashboard.md`` records the map.
"""

from __future__ import annotations

import asyncio
import contextlib  # noqa: F401
import copy  # noqa: F401
import dataclasses
import functools
import hashlib  # noqa: F401
import json
import logging
import os
import re
import stat  # noqa: F401
import subprocess
import time
import uuid
from collections.abc import Sequence  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Any

from aiohttp import BodyPartReader, web  # noqa: F401

from kiro_crew import agent_state  # noqa: F401
from kiro_crew import crew_teams as teams_mod  # noqa: F401
from kiro_crew import model_registry, model_scope
from kiro_crew.acp.client import advertised_model_ids, model_is_unusable
<<<<<<< HEAD
from kiro_crew.acp.types import ACP_BACKEND_CLAUDE, ACP_BACKEND_OPENCODE
from kiro_crew.acp_backends import selectable_backend_values
from kiro_crew.agent import (
=======
from kiro_crew.acp_backends import (
    ACP_BACKEND_CLAUDE,
    ACP_BACKEND_KIRO,
    model_registry_namespace,
    selectable_backend_values,
)
from kiro_crew.agent import (  # noqa: F401
>>>>>>> upstream/main
    AGENT_FILENAME,
    OWNED_KIRO_AGENT_FILES,
    _atomic_json_write,
    _is_confirmed_managed_dashboard_author,
    _refresh_forked_templates,
    _spec_path_is_safe,
    agents_spec_lock,
    clear_model_pin,
    emission_eligible_mcp_servers,
    get_shipped_tools,
    install_agent,
    kiro_agents_dir_path,
)
from kiro_crew.agent_capabilities import CapabilityError, require_unmanaged_template  # noqa: F401
from kiro_crew.agent_discovery import (  # noqa: F401
    SCOPE_GLOBAL,
    AgentInfo,
    _read_agent_spec,
    clear_list_agents_cache,
    list_agents,
    project_agent_names,
    spec_model,
    spec_str,
)
<<<<<<< HEAD
from kiro_crew.agent_sdk.drivers.acp import resolve_pin_spelling
from kiro_crew.apps.bridges import _mcp_lock as _agent_file_lock
from kiro_crew.apps.bridges import _registration_source
from kiro_crew.apps.manager import (
=======
from kiro_crew.agent_files import (  # noqa: F401
    DASHBOARD_AUTHOR_AGENT_FILENAME,
    KAS_RESERVED_AGENT_IDS,
)
from kiro_crew.agent_sdk.capabilities import capabilities_for, capabilities_of
from kiro_crew.agent_sdk.drivers.acp import (
    EntitlementRevalidating,
    catalog_row_would_drop,
    resolve_kiro_bin_for_spawn,
    resolve_pin_spelling,
    resolve_ssh_auth_sock,
)
from kiro_crew.agent_sdk.provider_identity import is_claude_code
from kiro_crew.agent_spec_format import (  # noqa: F401
    agent_spec_candidates,
    is_markdown_spec,
    iter_agent_spec_files,
)
from kiro_crew.apps.bridges import _mcp_lock as _agent_file_lock  # noqa: F401
from kiro_crew.apps.bridges import _registration_source  # noqa: F401
from kiro_crew.apps.manager import (  # noqa: F401
>>>>>>> upstream/main
    INSTALLED_META_FILENAME,
    app_dir,
    app_enabled_state,
    apps_dir,
)
from kiro_crew.atomic_write import replace_with_retry  # noqa: F401
from kiro_crew.config.loader import (  # noqa: F401
    ConfigReadError,
    KiroCrewAgentConfig,
    KiroCrewConfig,
    _safe_color,
    coerce_dict_section,
    coerce_effort,
    config_local_path,
    config_path,
    dispatch_kiro_agent,
    inject_kiro_cli_api_key,
    normalize_agent_model,
    read_config_text,
    resolve_agent_config_path,
    resolve_agent_identity,
    resolve_effective_model,
    update_config_locked,
    write_config_atomically,
)
from kiro_crew.config.paths import data_home  # noqa: F401
from kiro_crew.config.schema import SCHEMA_REGISTRY, config_entry_to_dict
from kiro_crew.config.sections import (  # noqa: F401
    _AVATAR_FILE_PIN_RE,
    _AVATAR_GHOST_BOOL_TRAITS,
    _AVATAR_GHOST_STR_TRAITS,
)
from kiro_crew.config.sections import _AVATAR_IMAGE_EXTS as _LOADER_AVATAR_IMAGE_EXTS
from kiro_crew.config.sections import (  # noqa: F401
    _safe_avatar,
)
from kiro_crew.dashboard import agent_admin as _agent_admin
from kiro_crew.dashboard.agent_admin import agent_config as _owner_agent_config
from kiro_crew.dashboard.agent_admin import agent_detail as _owner_agent_detail
from kiro_crew.dashboard.agent_admin import app_mcp_ownership as _owner_app_mcp_ownership
from kiro_crew.dashboard.agent_admin import avatars as _owner_avatars
from kiro_crew.dashboard.agent_admin import capabilities as _owner_capabilities
from kiro_crew.dashboard.agent_admin import crew_records as _owner_crew_records
from kiro_crew.dashboard.agent_admin import crew_removal as _owner_crew_removal
from kiro_crew.dashboard.agent_admin import crew_update as _owner_crew_update
from kiro_crew.dashboard.agent_admin import default_agent as _owner_default_agent
from kiro_crew.dashboard.agent_admin import fork_publish as _owner_fork_publish
from kiro_crew.dashboard.agent_admin import installed_agents as _owner_installed_agents
from kiro_crew.dashboard.agent_admin import roster as _owner_roster
from kiro_crew.dashboard.agent_admin import template_lineage as _owner_template_lineage
from kiro_crew.dashboard.agent_admin.agent_config import (  # noqa: F401
    _commit_agent_config,
    _commit_agent_config_locked,
    _find_agent_config,
    _installed_agent_config,
    _write_installed_config,
    api_agent_config,
)
from kiro_crew.dashboard.agent_admin.agent_detail import (  # noqa: F401
    _agent_detail_candidates,
    _merge_resources_delta,
    _reorder_named,
    api_agent_detail,
)
from kiro_crew.dashboard.agent_admin.app_mcp_ownership import (  # noqa: F401
    AppOwnershipUnreadable,
    _app_declared_server_names,
    _app_or_host_owned,
    _drop_unbacked_app_entries,
    _merge_unowned_servers,
    _on_disk_mcp_servers,
    _require_present_shape,
)
from kiro_crew.dashboard.agent_admin.avatars import (  # noqa: F401
    _avatar_stem,
    _avatar_variant_paths,
    _avatars_dir,
    _carry_motions_through_motionless_save,
    _carry_pack_through_faceless_save,
    _commit_promoted_avatar,
    _discard_pending_avatar,
    _image_body_complete,
    _is_ghost_shaped,
    _live_avatar_file,
    _pending_avatar_path,
    _promote_pending_avatar,
    _read_avatar_file,
    _remove_avatar_files,
    _rollback_promoted_avatar,
    _sniff_image_ext,
    _staging_token,
    api_kirocrew_agent_avatar_upload,
)
from kiro_crew.dashboard.agent_admin.capabilities import (  # noqa: F401
    _audit_capability,
    _is_valid_capability_package,
    _mutate_agent_package,
    api_capability_agents_install,
    api_capability_agents_list,
    api_capability_agents_uninstall,
    api_capability_mcp_install,
    api_capability_mcp_list,
    api_capability_mcp_registry,
    api_capability_mcp_uninstall,
    api_capability_plugins_list,
    api_capability_plugins_sync,
    api_capability_skills_install,
    api_capability_skills_list,
    api_capability_skills_uninstall,
)
from kiro_crew.dashboard.agent_admin.crew_records import (  # noqa: F401
    _crew_effort_rejected,
    _crew_memory_store_rejected,
    _refresh_session_defaults,
    api_kirocrew_agent_resolved_model,
    api_kirocrew_agents_create,
)
from kiro_crew.dashboard.agent_admin.crew_removal import (  # noqa: F401
    _member_slug_is_claimed,
    _prune_private_copy_of_deleted_crew,
    _reclaim_deleted_member_crew_log,
    api_kirocrew_agent_delete,
)
from kiro_crew.dashboard.agent_admin.crew_update import (  # noqa: F401
    _effort_inputs,
    api_kirocrew_agent_update,
)
from kiro_crew.dashboard.agent_admin.default_agent import (  # noqa: F401
    _alias_binding_template,
    _AmbiguousDefaultTarget,
    _AppRegisteredTemplate,
    _binds_template,
    _installed_template_alias,
    _is_app_registered,
    api_default_agent,
)
from kiro_crew.dashboard.agent_admin.fork_publish import (  # noqa: F401
    api_agent_fork,
    api_agent_publish,
    api_agent_reset,
)
from kiro_crew.dashboard.agent_admin.installed_agents import (  # noqa: F401
    _do_agents_sync,
    _namespaced_agent_file_exists,
    api_agents_installed,
    api_kirocrew_agents_sync,
)
from kiro_crew.dashboard.agent_admin.roster import (  # noqa: F401
    _agent_roster_row,
    _carries_mask,
    _name_would_be_masked,
    _roster_avatar,
    _roster_mask,
)
from kiro_crew.dashboard.agent_admin.template_lineage import (  # noqa: F401
    _AmbiguousTemplateName,
    _foreign_private_copy_owner,
    _ForeignPrivateCopy,
    _ForkBookkeepingFailed,
    _is_reserved_basename,
    _load_template_specs,
    _PublishNameBound,
    _rebind_crew_locked,
    _reserved_binding_names,
    _spec_stem_on_disk,
    _StaleBinding,
    _unlink_copy_unless_referenced,
    _UnverifiableLineage,
    _write_spec_file,
)
from kiro_crew.dashboard.chat_persistence import get_reasoning_effort_ordered
from kiro_crew.dashboard.chat_utils import (  # noqa: F401
    _BLOCKED_SLASH_COMMANDS,
    _SLASH_COMMANDS,
    SLASH_COMMAND_DESCRIPTIONS,
    _history_key_for,
    drained_to_thread,
    is_deprecated_model,
    run_config_write,
)
from kiro_crew.dashboard.conditional_get import conditional_response, strong_content_etag
from kiro_crew.dashboard.handlers._shared import (  # noqa: F401
    MAX_AGENT_SKILLS,
    SkillCatalogSnapshot,
    _capability_manager,
    _read_session_key,
    active_project_dir,
    agent_skill_keys,
    agent_skill_views,
    apply_skill_mapping,
    enumerate_skill_catalog,
    read_bounded_json,
)
from kiro_crew.dashboard.handlers.agent_templates import (  # noqa: F401
    TEMPLATE_DEFINITION_KEYS,
    apply_definition_patch,
    read_only_reason_for_path,
    validate_definition_patch,
)
from kiro_crew.dashboard.kiro_readiness import reject_if_kiro_unverified
from kiro_crew.dashboard.state import DashboardState
from kiro_crew.effort import EFFORT_LEVELS, EFFORT_VALUES  # noqa: F401
from kiro_crew.executors import discovery_executor, maintenance_executor, subprocess_executor
from kiro_crew.external_text import redact_external_text as _redact_external  # noqa: F401
from kiro_crew.kiro_prerequisite import spawn_supervised_oneshot
from kiro_crew.loop_lock import LoopBoundLock
from kiro_crew.members import MemberNameError, key_new_crew, validate_member_name  # noqa: F401
from kiro_crew.memory_stores import (  # noqa: F401
    DEFAULT_MEMORY_STORE,
    MemberAlreadyExists,
    UnknownMemoryStore,
    memory_store_binding_defect,
    memory_store_namespace_lock,
    persist_member_config,
    provision_member_memory,
    retire_unpublished_allocation,
)
from kiro_crew.platform.governance import sanitize_agent_config_governance  # noqa: F401
from kiro_crew.platform_compat import is_link_or_junction, kill_and_reap  # noqa: F401
from kiro_crew.sandbox import (
    SandboxUnavailableError,
    cgroup_scope_argv,
    configured_sandbox_mode,
    scrub_agent_subprocess_env,
    wrap_argv,
)
from kiro_crew.user_json import loads_user_json  # noqa: F401
from kiro_crew.validation import TEMPLATE_NAME_RE  # noqa: F401

_MODEL_LIST_STDERR_TAIL_CHARS = 1000
# How long one GET /api/models waits for a catalog before answering the degraded
# 503. Unchanged: a remote hub still budgets its whole cold path against this
# bound (see api_models), so raising it would move
# DEFAULT_MODELS_CAPABILITY_PROXY_TIMEOUT_SECS with it.
_LIST_MODELS_SUBPROCESS_TIMEOUT_SECS: float = 10.0
# How long the SHARED background catalog fetch may run, decoupled from any one
# request. On a host where a cold `kiro-cli --list-models` spawn always exceeds
# the request bound, killing it at that bound meant no call ever finished, so
# every 8s poll started another doomed cold spawn and the picker never left
# `auto`. The fetch now outlives the request that started it: the request still
# answers 503 after _LIST_MODELS_SUBPROCESS_TIMEOUT_SECS, but the spawn keeps
# running under this ceiling and the next poll is served from its result.
_LIST_MODELS_BACKGROUND_TIMEOUT_SECS: float = 90.0
# A cached catalog younger than this is served straight away; an older one is
# served straight away too and refreshed behind the reply (stale-while-
# revalidate). The catalog changes rarely, so a few minutes stale costs nothing
# the per-request entitlement narrowing does not already correct.
_LIST_MODELS_CATALOG_TTL_SECS: float = 300.0
# The cache is the one place ``--list-models`` output is held past the request,
# so retention is bounded before it is stored. Row count and identifying-field
# length reuse the repo's ONE shared admission bound
# (``model_registry.ADVERTISED_MODELS_MAX_IDS`` /
# ``ADVERTISED_MODEL_ID_MAX_CHARS``) so the picker cannot serve an id the window
# / advertised stores refused — an over-long id is REFUSED (the whole row
# skipped), never truncated, matching ``admit_catalog_rows``. This cap bounds
# only the non-identifying extra fields a row may carry (the shared admission
# does not speak to those): each is clamped to the id-length bound and a row
# keeps at most this many.
_CATALOG_CACHE_MAX_FIELDS_PER_ROW = 64

logger = logging.getLogger(__name__)


def _err500(exc: BaseException) -> web.Response:
    """Return a generic 500 with a correlation id; log the detail server-side.

    Browser-facing 5xx bodies must not echo raw backend exception text
    (CWE-209). The short correlation id ties the sanitized client response to
    the full server-side log line (which retains the traceback).
    """
    corr = uuid.uuid4().hex[:12]
    logger.error("agents handler error [%s]", corr, exc_info=exc)
    return web.json_response({"error": "internal error", "id": corr}, status=500)


def _sel():
    """Late-binding _sel() for test monkeypatch compatibility."""
    import kiro_crew.dashboard.handlers as _pkg  # noqa: F811

    return _pkg.sel()


async def _require_owner(request: web.Request, operation: str) -> web.Response | None:
    """Owner gate shared by every mutating agents handler, here and in the owners.

    ``~/.kiro/agents`` and ``cfg.agents`` are machine-global: a write there
    installs tool grants and MCP server commands that later sessions execute,
    so mutations are owner-only — the same server-side boundary
    ``mcp_apps.api_mcp_apps_call`` enforces. The caller identity comes from
    the token-auth middleware (``request["user"]`` / ``request["app"]``),
    never from a client-set header. Returns the 403 to send, or ``None`` when
    the caller is the owner.
    """
    from kiro_crew.dashboard.handlers._shared import require_owner_dashboard_request

    return await require_owner_dashboard_request(request, operation)


# ── Config Schema ──


_CONFIG_SCHEMA_ACP_BACKEND = "agent.acp_backend"


def _supply_live_enum(entry: dict) -> None:
    """In place: give ``agent.acp_backend`` the values this build can actually serve.

    The field carries no static ``enum`` on purpose (see ``AgentConfig``): an
    edition registers its backends at boot, strictly after ``SCHEMA_REGISTRY`` is
    built, so a frozen list could only be wrong — it would omit a registered
    backend from the dashboard while the PATCH allowlist accepted it.

    Resolved from the same owner as the PATCH allowlist and the config load path,
    so the three cannot disagree. One binding today, so it is spelled once rather
    than made a registry; turn it into a path -> callable map when a second
    dynamic enum appears.
    """
    if entry.get("path") == _CONFIG_SCHEMA_ACP_BACKEND:
        entry["enumValues"] = selectable_backend_values()


async def api_config_schema(request: web.Request) -> web.Response:
    """GET /api/config/schema — return config schema entries."""
    entries = SCHEMA_REGISTRY

    # Filter by tags (comma-separated, intersection)
    tags_param = request.query.get("tags", "").strip()
    if tags_param:
        requested_tags = {t.strip() for t in tags_param.split(",") if t.strip()}
        entries = [e for e in entries if set(e.tags) & requested_tags]

    # Filter out deprecated entries when deprecated=false
    dep_param = request.query.get("deprecated", "").strip().lower()
    if dep_param == "false":
        entries = [e for e in entries if not e.deprecated]

    # Serialize, masking sensitive defaultValues and converting dataclass
    # defaults to None (they aren't JSON-serializable).
    result = []
    for entry in entries:
        d = config_entry_to_dict(entry)
        if entry.sensitive or dataclasses.is_dataclass(d.get("defaultValue")):
            d["defaultValue"] = None
        _supply_live_enum(d)
        result.append(d)

    return web.json_response({"entries": result})


_CAPABILITY_UNAVAILABLE = "capability manager not available"

#: Upper bound on a capability package name. Generous for a real package id, but
#: it stops an unbounded string from reaching an edition's argv or a path join.
_MAX_CAPABILITY_PACKAGE_LEN = 200
#: Package-name charset. Deliberately permissive enough for the real shapes
#: (scoped npm ids, ``Pkg-1.0``, ``package/skill`` paths) while excluding
#: whitespace and every shell metacharacter.
#:
#: A leading ``@`` is allowed so a bare scoped npm id (``@scope/pkg``) is accepted,
#: but it must be FOLLOWED by an alphanumeric: what excluding ``-`` at position 0
#: buys is that a flag-shaped value can never be read as an option, and ``@-evil``
#: would hand ``-evil`` to an installer that strips the scope prefix.
_VALID_CAPABILITY_PACKAGE_RE = re.compile(r"^@?[A-Za-z0-9][A-Za-z0-9._@:/-]*$")


def _normalize_model_key(name: str) -> str:
    """Canonical key for de-duping CC model ids across spelling variants.

    Mirrors ``normalizeModelKey`` in ``website/src/lib/model.ts``: both route a
    model id through the shared canonical registry (``model_registry.json``) so
    "same model?" has ONE definition across the dashboard (dropdown dedup, slot
    display, and the subagent downgrade flag).

    Resolution order:
    1. ``auto``/``default``/unset -> the ``auto`` sentinel (both mean "let the
       backend pick"); an empty id stays ``""`` (no pin, distinct from Auto).
    2. Registry canonical key: a canonical key, a registry alias, or a
       claude_code provider id -- with or without a region/vendor routing prefix
       (``us.anthropic.…``, ``global.anthropic.…``) -- folds to its canonical
       key. This makes an alias and its provider-prefixed canonical id equal
       (``us.anthropic.claude-opus-4-8[1m]`` == ``claude-opus-4.8`` ->
       ``opus-4.8-1m``) while keeping DISTINCT registry entries distinct -- the
       advertised dashed ``claude-opus-4-8`` (200K, ``opus-4.8``) does NOT fold
       onto dotted ``claude-opus-4.8`` (1M, ``opus-4.8-1m``); a bare
       ``.``->``-`` fold conflates those two different-window models.
    3. Fallback for an id the registry does not list (GPT/DeepSeek/Qwen, future
       models, operator-typed ids): a lossless fold -- lowercase,
       ``.``->``-`` -- so behavior is identity-preserving off the registered set,
       matching ``from_provider_id``'s pass-through contract.
    """
    string_fold = (name or "").strip().lower().replace(".", "-")
    if not string_fold:
        return ""
    if string_fold in ("default", "auto"):
        return "auto"
    # Registry lookups are exact and its keys/aliases/provider-ids are all
    # lowercase, so resolve on the lowercased id. canonical_key resolves
    # acp-first then claude_code AND peels a known routing prefix, so it covers
    # both spelling halves above; a miss returns None.
    resolved = model_registry.canonical_key((name or "").strip().lower())
    if resolved is not None:
        return resolved
    return string_fold


<<<<<<< HEAD
def _advertised_cc_models(request: web.Request) -> list[dict]:
    """Map the most recently started active CC provider's advertised models.

    Iterates newest-first (see :func:`_entitled_kiro_models`'s identical
    rationale): ``active_providers()`` returns sessions in creation order, and
    a session started before a provider/backend switch still holds the
    advertised list it captured at its own session/new. On a long-running tab
    that has switched providers before, the old session can outlive the
    switch in ``_sessions`` -- reading oldest-first picked it up permanently
    (never self-healing, since nothing ever reorders or expires it), which is
    exactly what a stale in-flight-refetch race would look like but isn't.

    claude-agent-acp captures its real versioned list at session init (see
    AcpClient._capture_available_models). The raw advertised id is used
    VERBATIM, never remapped through the registry's ``from_provider_id`` --
    that remap folds Claude Code's own short config-option aliases (``opus``,
    ``sonnet``) onto Bedrock-flavored canonical keys (``opus-4.8-1m``,
    ``sonnet-4.6-1m``) meant for a DIFFERENT id shape (kiro-cli/acp's own
    ``global.anthropic.claude-opus-4-8[1m]``-style ids). A native claude_code
    session never advertises that shape -- it only ever reports its own
    aliases -- so the remap did nothing useful and broke the wire: selecting
    the remapped row sent a value the adapter flatly rejects with "Invalid
    value for config option model" (verified live -- ``opus``/``sonnet`` are
    the two most-used non-default models, and both were unselectable from
    this exact list). The remap's sole purpose was dedup against the static
    registry catalog in :func:`_cc_models`, which has no live caller.
    Returns ``[]`` when no session has initialized or the backend advertised
    nothing.
=======
def _advertised_cc_models(request: web.Request, namespace: str) -> list[dict]:
    """Map a live provider's advertised models to the API shape, per namespace.

    ``model_name`` is the advertised id verbatim: it is the wire value sent back
    on selection, and the adapter only accepts ids it advertised. Returns ``[]``
    when no session of that namespace has initialized or the backend advertised
    nothing.

    Two filters, and both are load-bearing. The CAPABILITY gate
    (``SessionCapabilities.resolves_model_from_advertised_list``) is the property
    this list depends on: a backend whose served list is the only source of ids it
    accepts back is exactly the backend whose advertised list has to be read. The
    NAMESPACE gate (``model_id_namespace``) is whose ids these are. Harnesses
    can advertise different served ids, so a retained claude session would
    otherwise answer the codex picker with claude ids --
    every one of which codex refuses.

    Newest matching session first, like :func:`_entitled_kiro_models`: forward
    order is creation order, so the most recently started session carries the most
    recent snapshot of what the account is served.
>>>>>>> upstream/main
    """
    try:
        state: DashboardState = request.app["state"]
        providers = state.sessions.active_providers()
    except (KeyError, AttributeError):
        return []
    for provider in reversed(providers):
<<<<<<< HEAD
=======
        # Read each field straight off ``capabilities_of(provider)``: binding it to a
        # local would be a second spelling of the question, which the one-spelling
        # ratchet in test_agent_sdk_capabilities.py exists to keep greppable.
        if not capabilities_of(provider).resolves_model_from_advertised_list:
            continue
        if capabilities_of(provider).model_id_namespace != namespace:
            continue
>>>>>>> upstream/main
        getter = getattr(provider, "available_models", None)
        if not callable(getter):
            continue
        try:
            advertised = getter()
        except Exception:
            continue
        if advertised:
            return [
                {
                    "model_name": m.get("modelId", ""),
                    "display_name": m.get("name", "") or m.get("modelId", ""),
                    "description": m.get("description", ""),
                }
                for m in advertised
                if m.get("modelId")
            ]
    return []


async def _entitled_kiro_models(request: web.Request, models: list[dict]) -> list[dict]:
    """Narrow the ``--list-models`` catalog to what a live session advertises.

    ``kiro chat --list-models`` is a CATALOG, not an entitlement: it returns the
    same rows whatever the account's tier, so after a downgrade it still offers
    (and still SHOWS as selected) a model no turn can run. The per-session
    ``session/new`` ``availableModels`` list is the tier-aware one — the same
    signal ``model_is_unusable`` pre-flights against before the wire — so when a
    live session has one, it wins here too. Same rule as the claude_code branch
    in :func:`_cc_models`: advertised is authoritative when present.

    The keep/drop decision delegates to ``model_is_unusable`` rather than
    comparing ids here, so the picker cannot disagree with the wire about what
    "this account can run" means. A local comparison would be a second spelling
    of that question — the exact drift that predicate exists to prevent — and any
    difference in how the two fold spelling variants shows up as a row the picker
    offers and the wire then withholds. A literal miss is retried through
    ``resolve_pin_spelling``, the same namespace fold the wire sites apply
    before withholding — but the row is REWRITTEN to the advertised spelling
    the fold answers with (and dropped when another row already offers that
    spelling): the selection sinks (the agent/crew pin validator and
    ``set_model``'s pre-flight) compare the picked value literally, so a row
    must carry an id they accept verbatim, not the catalog's stale
    ``<namespace>::<bare-id>`` qualifier it resolved from.

    The ``auto`` sentinel is never filtered: it means "inherit whatever the
    session already resolved", so it stays selectable even on a backend that does
    not advertise it by name.

    Only a session whose ids live in the catalog's own namespace can narrow it
    (``capabilities_of(provider).model_id_namespace``, the same gate
    :func:`_advertised_cc_models` applies). A live claude session advertises
    ``global.anthropic.…[1m]`` ids; ``resolve_pin_spelling`` folds those onto the
    catalog's bare ids because they name the same models, so without the gate a
    claude list would rewrite kiro's picker rows into claude's spelling and narrow
    them to claude's entitlements. Namespace is the question here, not spelling.

    Fails open in every unknowable case — no live session in this namespace, a
    backend that advertises nothing, or an advertised set that does not intersect
    the catalog at all under any spelling. Filtering on any of those would empty
    the picker, which is worse than listing one model too many.
    """
    try:
        state: DashboardState = request.app["state"]
        providers = state.sessions.active_providers()
    except (KeyError, AttributeError):
        return models
    advertised: list[str] = []
    catalog_ids = [m.get("model_name", "") for m in models]
    # Newest session first. `active_providers()` walks a dict of live sessions, so
    # forward order is creation order — and a session that started BEFORE a plan
    # change still holds the advertised list it captured at its own session/new.
    # Reading the oldest one would narrow the catalog to pre-downgrade
    # entitlements, i.e. keep offering exactly the models this narrowing exists to
    # hide. The most recently started session carries the most recent snapshot.
    for provider in reversed(providers):
        if capabilities_of(provider).model_id_namespace != model_registry_namespace(
            ACP_BACKEND_KIRO
        ):
            continue
        getter = getattr(provider, "available_models", None)
        if not callable(getter):
            continue
        try:
            ids = advertised_model_ids(getter())
        except Exception:
            continue
        if not ids:
            continue
        # The snapshot for the session that will narrow the picker gets a chance
        # to prove itself first. When it would drop a catalog model, the read
        # path has no explicit-pick refusal to trigger the refresh-before-refuse
        # heal, so an unconfirmed startup-race snapshot would silently hide
        # entitled models here. ``maybe_refresh_available_models`` is declared on
        # the provider ABC (default: return the current snapshot), owns the
        # staleness heuristic and the single-flight, fail-open probe; a probe
        # that fails or agrees leaves ``ids`` exactly as they were.
        try:
            refreshed = advertised_model_ids(
                await provider.maybe_refresh_available_models(catalog_ids)
            )
            if refreshed:
                ids = refreshed
        except EntitlementRevalidating:
            # The probe is in flight past the deadline. Propagate so the endpoint
            # returns its degraded response and the frontend polls again rather
            # than caching the un-revalidated snapshot; the next read serves the
            # landed result. Never swallowed as a fail-open.
            raise
        except Exception:
            pass
        advertised = ids
        break
    if not advertised:
        return models
    advertises_auto = any(_normalize_model_key(i) == "auto" for i in advertised)
    offered: set[str] = {
        _normalize_model_key(m.get("model_name", ""))
        for m in models
        if _normalize_model_key(m.get("model_name", "")) == "auto"
        or not model_is_unusable(m.get("model_name", ""), advertised)
    }
    kept: list[dict] = []
    for m in models:
        name = m.get("model_name", "")
        # The per-row keep/drop verdict is shared with the read-path
        # revalidation, so the probe decision and this filter agree on which
        # rows a snapshot hides.
        if catalog_row_would_drop(name, advertised):
            continue
        if _normalize_model_key(name) == "auto" or not model_is_unusable(name, advertised):
            kept.append(m)
            continue
        resolved = resolve_pin_spelling(name, advertised)
        if not resolved:
            continue
        key = _normalize_model_key(resolved)
        # Another row (literal or already-rewritten) offers this advertised
        # spelling: emitting a second one would show duplicate rows for one
        # model, so the qualified duplicate drops.
        if key in offered:
            continue
        offered.add(key)
        kept.append({**m, "model_name": resolved})
    # Tell "not comparable" apart from "entitled to almost nothing". A backend
    # that advertises `auto` shares a namespace with the catalog by definition, so
    # `auto` alone is a real answer — the most restricted tier there is — and must
    # narrow the picker to it. Only when nothing at all lines up, `auto` included,
    # is this a namespace mismatch (bare vs prefixed provider ids) where showing
    # the whole catalog beats emptying the picker. `auto` is always kept, so it can
    # never serve as the evidence that the two sides are comparable. A row
    # rewritten through the ``resolve_pin_spelling`` retry IS such evidence: a
    # peeled match proves the two vocabularies line up once the qualifier is
    # removed.
    if not advertises_auto and not any(
        _normalize_model_key(m.get("model_name", "")) != "auto" for m in kept
    ):
        return models
    return kept


def _cc_models(request: web.Request, configured_default: str = "") -> list[dict]:
    """Assemble the CC model dropdown, scoped to what the account can actually use.

    The live backend's advertised set is AUTHORITATIVE when present. It is the
    only source that reflects entitlement: claude-agent-acp captures it at session
    init from what the signed-in account is actually served. The registry is a
    static catalog of everything KiroCrew knows how to name, so a free-tier user
    shown it unfiltered is offered the full flagship list and discovers the truth
    only when a prompt fails.

    So when anything is advertised, registry rows are FILTERED DOWN to it (keeping
    the registry's cleaner display names for the survivors), and advertised models
    the registry does not list are appended for forward-compat.

    When NOTHING is advertised the registry is shown unfiltered. That is not a
    preference for the unfiltered list -- an empty advertised set means
    "no session has initialized yet", which is indistinguishable from "this account
    gets nothing", and showing an empty picker on a cold dashboard would be worse
    than showing a superset.

    ``auto`` is always present and always FIRST. It is the configured default
    (``config.agent.model``) and a sentinel rather than a real model, so it is
    never filtered by entitlement. It leads the list because the registry's own
    ``default: true`` flag sorts the current flagship to the top, which would
    present a specific paid model as the default in the picker.
    """
    advertised = _advertised_cc_models(request, "claude_code")
    registry_rows = model_registry.display_list("claude_code")

    if advertised:
        advertised_keys = {
            _normalize_model_key(e.get("model_name", ""))
            for e in advertised
            if _normalize_model_key(e.get("model_name", ""))
        }
        # Keep registry rows only when the backend also advertises them; "auto" is
        # a sentinel, not an entitlement, so it survives regardless.
        registry_rows = [
            e
            for e in registry_rows
            if _normalize_model_key(e.get("model_name", "")) in advertised_keys
            or _normalize_model_key(e.get("model_name", "")) == "auto"
        ]

    merged: list[dict] = []
    seen: dict[str, int] = {}
    for entry in (*registry_rows, *advertised):
        name = entry.get("model_name", "")
        key = _normalize_model_key(name)
        if not key:
            continue
        if key in seen:
            # Collision: registry keeps display, advertised id keeps the wire value.
            if key != "auto":
                merged[seen[key]] = {**merged[seen[key]], "model_name": name}
            continue
        seen[key] = len(merged)
        merged.append(entry)
    # "auto" leads. It may be absent entirely if a future registry drops the row,
    # so synthesize it rather than assuming the filter above preserved one.
    merged = [e for e in merged if _normalize_model_key(e.get("model_name", "")) == "auto"] + [
        e for e in merged if _normalize_model_key(e.get("model_name", "")) != "auto"
    ]
    if not any(_normalize_model_key(e.get("model_name", "")) == "auto" for e in merged):
        merged.insert(0, {"model_name": "auto", "display_name": "Auto", "description": ""})
        seen = {_normalize_model_key(e.get("model_name", "")): i for i, e in enumerate(merged)}
    # Guarantee the configured default is present (e.g. a custom cc_model the
    # backend doesn't advertise) so the selected model never vanishes. Resolve it
    # to its canonical key first (it may be stored as a provider id or alias) so a
    # default that already maps to a registry row does NOT produce a duplicate.
    if configured_default:
        canonical_default = model_registry.from_provider_id(
            model_registry.to_provider_id(configured_default, "claude_code"), "claude_code"
        )
        # Skip a blank canonical key: cc_model="auto" round-trips to "" (auto's
        # provider id is empty), and _normalize_model_key("")=="" is never in
        # `seen` (which holds "auto"), so without the `if key` guard — the same
        # one the merge loop above uses — a blank-named row would be inserted as
        # the first/selected dropdown option. The "auto" registry row already
        # covers this case.
        key = _normalize_model_key(canonical_default)
        # Only resurrect the configured default when entitlement cannot contradict
        # it: either nothing was advertised (unknown, so trust config) or it WAS
        # advertised but the registry lacked a row. Force-including a model the
        # backend did not advertise would reintroduce exactly the unusable option
        # this filter removes -- a stale config pick outliving the entitlement.
        may_include = not advertised or key in {
            _normalize_model_key(e.get("model_name", "")) for e in advertised
        }
        if key and key not in seen and may_include:
            # After "auto", never before it: "auto" is the configured default in
            # the general case and leads the list.
            merged.insert(
                (
                    1
                    if merged and _normalize_model_key(merged[0].get("model_name", "")) == "auto"
                    else 0
                ),
                {
                    "model_name": canonical_default,
                    "display_name": canonical_default,
                    "description": "Configured default",
                },
            )
    # Enrich every row with a context_window via the central authority so the CC
    # dropdown carries the same field the kiro branch does (the frontend picker
    # + tooltip read it uniformly). None -> reference (never a silent 200k).
    for entry in merged:
        if "context_window" not in entry:
            name = entry.get("model_name", "")
            entry["context_window"] = (
                model_registry.model_window(name) or model_registry.REFERENCE_WINDOW_TOKENS
            )
    return merged


def _advertised_backend_models(
    request: web.Request, backend: str, configured_default: str = ""
) -> list[dict]:
    """Assemble model choices from one ACP backend's advertised namespace.

    A live session wins over the cross-session cache. Both sources retain the
    adapter's exact model ids, which may be provider/model pairs for Pi. A cold
    cache offers ``auto`` and, when set, the configured default until the first
    session advertises its choices.
    """
    namespace = model_registry_namespace(backend)
    advertised = _advertised_cc_models(request, namespace)
    if not advertised:
        cached = model_registry.advertised_models(namespace)
        advertised = [{"model_name": m, "display_name": m, "description": ""} for m in cached]

    rows: list[dict] = [
        {"model_name": "auto", "display_name": "Auto", "description": "Backend default"}
    ]
    seen: set[str] = {"auto"}
    for entry in advertised:
        name = str(entry.get("model_name", "") or "").strip()
        if not name or _normalize_model_key(name) == "auto" or name in seen:
            continue
        seen.add(name)
        rows.append(
            {
                "model_name": name,
                "display_name": entry.get("display_name") or name,
                "description": entry.get("description", ""),
            }
        )
    default = (configured_default or "").strip()
    if (
        default
        and _normalize_model_key(default) != "auto"
        and default not in seen
        and not advertised
    ):
        rows.insert(
            1, {"model_name": default, "display_name": default, "description": "Configured default"}
        )
    for entry in rows:
        entry["context_window"] = (
            model_registry.model_window(entry["model_name"])
            or model_registry.REFERENCE_WINDOW_TOKENS
        )
    return rows


def _wrap_list_models_argv(argv: list[str]) -> tuple[list[str], str | None]:
    """Sandbox-wrap the ``--list-models`` argv at the configured tier.

    Runs in an executor, never on the loop: :func:`configured_sandbox_mode` stats
    (and on a cache miss re-reads and revalidates) ``config.json``, and
    ``wrap_argv`` -> ``detect_backend`` can cold-probe the sandbox backend with a
    synchronous ``subprocess.run(..., timeout=5)``. Resolving the mode here rather
    than passing it in keeps BOTH blocking reads in the worker thread.

    ``is_kiro_cli=True`` is explicit because ``_spawns_kiro_cli``'s basename test
    only matches a literal ``kiro-cli``: a Windows ``kiro-cli.exe``, a wrapper
    shim, or a ``KIROCREW_KIRO_BIN`` pointing at a nonstandard launch path all
    read as "not kiro-cli". The positive classification is also the security gate
    for default Windows delegation to Kiro's internal sandbox; basename inference
    cannot grant it. Both ACP spawn paths pass this flag for the same reason.
    """
    return wrap_argv(argv, mode=configured_sandbox_mode(), is_kiro_cli=True)


<<<<<<< HEAD
_NATIVE_VISION_FAMILY_PREFIXES = frozenset({"cmc", "oc", "ol", "cx", "ag"})


def _model_supports_vision(model_id: str) -> bool | None:
    """Reported vision capability for a model id, or None when unknown."""
    from kiro_crew.acp.vision import decide_image_input_mode  # noqa: F811

    try:
        from kiro_crew.model_registry import model_supports_vision  # noqa: F811

        flag = model_supports_vision(model_id)
        if flag is not None:
            return bool(flag)
    except Exception:
        pass
    # Router-prefixed ids are not canonical registry keys, so the registry
    # returns None for them — route via the same decision the runtime uses.
    # Thread the text-only denylist so oc/deepseek-v4-flash and
    # ol/deepseek-v4-flash:0731 report as text, matching the ACP redirect gate.
    try:
        from kiro_crew.acp.client import _DEFAULT_TEXT_ONLY_MODELS  # noqa: F811
        from kiro_crew.config.loader import KiroCrewConfig as _KC  # noqa: F811

        try:
            cfg_text_only = _KC.load().agent.text_only_models  # type: ignore[attr-defined]
            text_only: tuple[str, ...] | None = tuple(cfg_text_only) if cfg_text_only else None
        except Exception:
            text_only = None
        if text_only is None:
            text_only = tuple(_DEFAULT_TEXT_ONLY_MODELS)
        mode = decide_image_input_mode(model_id, image_input_mode="auto", text_only_models=text_only)
        if mode != "auto":
            return mode == "native"
    except Exception:
        pass
    return None


def _cc_model_row(model_id: str, description: str = "") -> dict:
    """One curated router-model row in the wire shape the picker SPA expects.

    ``context_window_tokens`` comes from the central resolver (kiro-list cache >
    static registry > supplementary map > ``[1m]`` heuristic), never a hardcoded
    literal — the fork previously pinned every router model at 200k, which made
    a 1M model (e.g. ``ocg/deepseek-v4-flash``) read as 200K in the picker. The
    frontend learns this value into ``LIVE_WINDOWS``, so the composer's context
    meter follows it too. Unknown ids resolve to the 1M reference rather than a
    silent 200k.

    ``supports_vision`` (when not None) is the single capability flag the
    frontend picker groups on, so a Vision section can feel native in the
    AppImage rather than bolted on via text filters. Router-prefixed ids
    (``cmc/``, ``ol/``, …) are not canonical registry keys, so they are tagged
    as vision-capable when they belong to a vision provider family — the same
    families the ACP image-input routing treats as native.
    """
    if not description:
        family = model_id.split("/", 1)[0] if "/" in model_id else model_id
        description = f"{model_id.split('/')[-1]} via {family}"
    row: dict[str, object] = {
        "model_name": model_id,
        "model_id": model_id,
        "description": description,
        "context_window_tokens": (
            model_registry.model_window(model_id) or model_registry.REFERENCE_WINDOW_TOKENS
        ),
        "rate_multiplier": 1.0,
        "rate_unit": "Credit",
    }
    flag = _model_supports_vision(model_id)
    if flag is not None:
        row["supports_vision"] = flag
    return row


async def _opencode_models_response(request: web.Request) -> web.Response:
    """Model catalog for /api/models on the opencode backend.

    Fetches the provider's ``/v1/models`` (both Anthropic- and
    OpenAI-compatible endpoints expose it; the auth header differs by format).
    Context windows come from the central resolver (model_registry), same as
    the claude_code path. Falls back to the curated router whitelist when the
    endpoint is unreachable, so a cold dashboard never shows an empty picker.
    """
    import aiohttp

    cfg = KiroCrewConfig.load()
    base = (cfg.agent.provider_base_url or "").rstrip("/")
    rows: list[dict] = []
    if base:
        api_format = cfg.agent.provider_api_format or "openai"
        headers: dict[str, str] = {}
        if cfg.agent.provider_api_key:
            if api_format == "anthropic":
                headers["x-api-key"] = cfg.agent.provider_api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {cfg.agent.provider_api_key}"
        url = f"{base}/v1/models"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("data", []):
                            mid = item.get("id") or ""
                            if mid:
                                row = _cc_model_row(
                                    mid,
                                    item.get("display_name") or item.get("description") or "",
                                )
                                # Prefer the catalog's own vision flag when it ships one
                                # (router /v1/models may report capabilities.supports_vision,
                                # capabilities.vision, or a top-level supports_vision).
                                caps = (
                                    item.get("capabilities")
                                    if isinstance(item.get("capabilities"), dict)
                                    else {}
                                )
                                catalog_flag: bool | None = None
                                for key in ("supports_vision", "vision", "vision_capable"):
                                    val = item.get(key) if key in item else caps.get(key)
                                    if isinstance(val, bool):
                                        catalog_flag = val
                                        break
                                if catalog_flag is not None:
                                    row["supports_vision"] = catalog_flag
                                rows.append(row)
        except Exception:
            logger.debug("opencode /v1/models fetch failed: %s", url, exc_info=True)
    if cfg.agent.model_whitelist:
        rows = [r for r in rows if r["model_id"] in cfg.agent.model_whitelist]
    if not rows:
        from kiro_crew.acp.client import AcpClient  # noqa: F811

        rows = [_cc_model_row(mid) for mid in sorted(AcpClient.router_model_whitelist())]
    return web.json_response(rows)


async def _live_router_cc_models(base_url: str, api_key: str) -> list[dict]:
    """Probe ``{base_url}/v1/models`` directly, in the picker row shape.

    Mirrors :func:`_opencode_models_response`'s live probe -- the claude_code
    path had none, and depended entirely on ``_advertised_cc_models`` (a live
    session's own captured catalog). That capture only exists once a session
    has actually spawned against the CURRENT ``provider_base_url``, which the
    picker's own invalidation fires well before: switching backend/preset
    invalidates ``available-models`` the instant the config PATCH resolves,
    but the old session (if any) was just torn down and the new one has not
    spawned yet. That refetch landed on this function's static-whitelist
    fallback below -- a generic cross-provider snapshot (``ag/``, ``cmc/``,
    ``oc/``, ``ol/`` families) that has nothing to do with whichever router is
    actually configured, and reads as a data problem even when the switch
    itself worked. A direct probe has no such dependency: it is correct on
    the very first fetch, race or not. Same header convention as
    ``load_router_catalog_ids`` (``x-api-key`` -- claude_code speaks Anthropic
    wire format only, no format branch needed here).
    """
    import aiohttp

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(
                f"{base_url}/v1/models", headers={"x-api-key": api_key}
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
    except Exception:
        logger.debug("claude_code router /v1/models probe failed: %s", base_url, exc_info=True)
        return []
    rows: list[dict] = []
    for item in data.get("data", []) if isinstance(data, dict) else []:
        mid = item.get("id") or item.get("model") or ""
        if mid:
            rows.append(_cc_model_row(mid))
    return rows


# Last non-empty model list served per claude_code lane, keyed by the pair that
# decides WHICH catalog is correct: (acp_backend, provider_base_url). Scoping to
# that pair is the whole point -- a router's list must never answer for the
# native lane, or vice versa, which is exactly the bug an unscoped browser-side
# cache produced.
#
# It exists because the native lane has no session-independent source. The
# router lane can always probe {base_url}/v1/models, but native's ONLY source is
# a live session's advertised list, and a provider switch tears every session
# down (reload_provider_factory) before respawning one. For those seconds
# /api/models had nothing to say and returned [], so every picker collapsed to
# the "auto" sentinel until a session came back -- reading as "the switch
# emptied my model list" rather than "still starting". This remembers what the
# same lane last advertised so the gap is covered by the right answer.
_LAST_CC_ROWS: dict[tuple[str, str], list[dict]] = {}


async def _cc_models_response(request: web.Request) -> web.Response:
    """Curated router-catalog response for /api/models on the claude_code path.
    The upstream handler spawns ``kiro-cli chat --list-models``, which returns
    Kiro's Bedrock catalog — useless (and wrong) when the backend is Claude
    Code talking to a custom LLM router. Precedence: live advertised rows from
    a session that has already captured them (freshest -- tier-aware), else a
    direct probe of the configured router (no session-timing dependency),
    else the static whitelist so a cold dashboard never shows an empty picker
    -- but only when a router is actually configured. On the native lane
    (no ``provider_base_url``) that whitelist is never correct either -- it is
    built from router-prefixed ids, not Claude Code's own alias names -- so an
    empty result (the picker's existing "still loading" state) beats
    confidently showing 94 models that namespace-mismatch this account.
    """
    from kiro_crew.acp.client import AcpClient  # noqa: F811

    cfg = KiroCrewConfig.load()
    base_url = (cfg.agent.provider_base_url or "").rstrip("/")
    rows: list[dict] = []
    for entry in _advertised_cc_models(request):
        mid = entry.get("model_name") or ""
        # Advertised wins outright. Intersecting it with the static whitelist
        # dropped models the connected router was actively serving.
        if mid:
            rows.append(
                _cc_model_row(
                    mid,
                    entry.get("description") or entry.get("display_name") or "",
                )
            )
    if not rows and base_url:
        rows = await _live_router_cc_models(base_url, cfg.agent.provider_api_key or "")
    if not rows and base_url:
        rows = [_cc_model_row(mid) for mid in sorted(AcpClient.router_model_whitelist())]
    lane = (cfg.agent.acp_backend or "", base_url)
    if rows:
        _LAST_CC_ROWS[lane] = rows
    else:
        # Nothing live to report. On the native lane this is the post-switch
        # respawn window, not a real "no models" answer -- serve what this same
        # lane last advertised rather than an empty picker. Still empty on a
        # lane never seen before, which is the honest answer there.
        rows = _LAST_CC_ROWS.get(lane, [])
    if cfg.agent.model_whitelist:
        rows = [r for r in rows if r["model_id"] in cfg.agent.model_whitelist]
    return web.json_response(rows)


async def api_models(request: web.Request) -> web.Response:
    """GET /api/models — list available models from the live kiro-cli ACP session."""
    # Fork: on the claude_code (custom LLM router) path the picker must show
    # the curated router catalog, not kiro-cli's Bedrock list.
    cfg = KiroCrewConfig.load()
    if cfg.agent.acp_backend == ACP_BACKEND_CLAUDE:
        return await _cc_models_response(request)
    if cfg.agent.acp_backend == ACP_BACKEND_OPENCODE:
        return await _opencode_models_response(request)
=======
def _scoped_default(cfg: Any, backend: str) -> str:
    """The stored pin, but only when *backend*'s own harness can claim it.

    A pin chosen in another harness is not a default here: marking it as one puts
    an id the returned list does not even contain into the picker's selected slot,
    while every turn runs the harness default. Same rule the provider factory
    sends by, so the marker and the wire agree.

    Called from the two branches that read the pin rather than once above them:
    the kiro branch does not consult ``agent.model`` at all, and pulling the read
    up would make it pay for a value it never uses (harness-parity H13 -- the
    test is whether the kiro path changed, not whether it still works).
    """
    return model_scope.scoped_pin(
        getattr(cfg.agent, "model", "") or "",
        capabilities_for(backend).model_id_namespace,
        source="api_models",
        log_level=logging.DEBUG,
    )


class _CatalogUnavailable(Exception):
    """A degraded catalog fetch outcome that maps to one 503 body.

    The fetch runs in a shared background task that cannot return an HTTP
    response, so each degraded outcome (binary unresolved, timeout, non-zero
    exit, empty / invalid output) raises this carrying its error message, and
    the request path renders a dict-literal 503 body from it — one 503 per
    outcome. The message is carried, not a response dict, so the single render
    site stays a dict literal the error-code ratchet can scan.
    """

    def __init__(self, error: str):
        super().__init__(error)
        self.error = error


def _bounded_catalog(models: list[dict]) -> list[dict]:
    """Clamp a parsed catalog to what the cache may safely retain.

    The retention point (:data:`_catalog_cache`) holds the list past the request,
    so it is bounded here before it is stored, through the SAME admission the
    window / advertised stores use — ``model_registry.ADVERTISED_MODELS_MAX_IDS``
    rows, each identifying field (``model_name`` / ``model_id``) at most
    ``ADVERTISED_MODEL_ID_MAX_CHARS`` — so the cache cannot serve an id those
    stores refused. An over-long id is REFUSED (its whole row skipped), never
    truncated, matching :func:`model_registry.admit_catalog_rows`'s own
    invariant; the picker reads the name, so a sliced name would name a different
    model or none.

    Each remaining scalar field (str / int / float / bool / None) is kept, with
    strings clamped to the id-length bound and a row holding at most
    :data:`_CATALOG_CACHE_MAX_FIELDS_PER_ROW`; a non-scalar field (nested object
    or array) is dropped — no reader of the cached list consumes one, and it is
    the unbounded edge the retention bound exists to close. Row ORDER is
    preserved (readers treat catalog order as meaningful). Rows and fields
    discarded for any reason are counted and logged once per snapshot.
    """
    max_rows = model_registry.ADVERTISED_MODELS_MAX_IDS
    max_chars = model_registry.ADVERTISED_MODEL_ID_MAX_CHARS
    bounded: list[dict] = []
    dropped_rows = 0
    dropped_fields = 0
    for row in models:
        if len(bounded) >= max_rows:
            dropped_rows += 1
            continue
        if not isinstance(row, dict):
            dropped_rows += 1
            continue
        # Refuse (skip) a row whose identifying field is over-long, rather than
        # slicing it into an id no store retained.
        ident = row.get("model_name") or row.get("model_id")
        if isinstance(ident, str) and len(ident) > max_chars:
            dropped_rows += 1
            continue
        kept: dict = {}
        for key, value in row.items():
            if len(kept) >= _CATALOG_CACHE_MAX_FIELDS_PER_ROW:
                dropped_fields += 1
                continue
            # The KEY is a retained string too: refuse (skip) an over-long one
            # rather than cache it, so no retained string is unbounded.
            if isinstance(key, str) and len(key) > max_chars:
                dropped_fields += 1
                continue
            if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
                kept[key] = value
            elif isinstance(value, str):
                kept[key] = value[:max_chars]
            else:
                # Non-scalar (nested dict/list): dropped — unbounded and unread.
                dropped_fields += 1
        bounded.append(kept)
    if dropped_rows or dropped_fields:
        logger.warning(
            "api_models: catalog cache dropped %d row(s) and %d field(s) over the "
            "retention bound (max_rows=%d, max_id_chars=%d)",
            dropped_rows,
            dropped_fields,
            max_rows,
            max_chars,
        )
    return bounded


@dataclasses.dataclass
class _CatalogCache:
    """The last good ``--list-models`` catalog, kept in memory only.

    One slow success is enough: once ``models`` is set, every request is served
    from it (after per-request entitlement narrowing) while a stale entry is
    refreshed behind the reply. A gateway restart drops it, so the first request
    after a restart pays the cold start again — the catalog is not persisted,
    which keeps a downgraded account's stale rows from surviving a restart.

    ``task`` single-flights the fetch: concurrent polls (and the 8s self-heal
    loop) share one spawn rather than each starting its own cold start.
    """

    models: list[dict] | None = None
    fetched_at: float = 0.0
    task: "asyncio.Task[list[dict]] | None" = None


_catalog_cache = _CatalogCache()


async def _fetch_kiro_catalog() -> list[dict]:
    """Spawn ``kiro-cli --list-models`` once and return the catalog rows.

    Calls the module-level ``resolve_kiro_bin_for_spawn`` /
    ``resolve_ssh_auth_sock`` wrappers directly. They are imported from
    ``kiro_crew.agent_sdk.drivers.acp`` — the agent-SDK surface, not a forbidden
    root — so this background worker reaches the spawn helpers without adding an
    ACP-layer edge (see ``scripts/check_agent_sdk_boundary.py``).

    Returns the deprecated-stripped list, each row under the ``model_id`` its
    session advertises (see ``wire_row`` below), and seeds the window/advertised caches —
    the UNFILTERED-then-deprecated-stripped list, i.e. the response body before
    per-request entitlement narrowing. Raises :class:`_CatalogUnavailable` for a
    degraded outcome (binary unresolved, timeout, non-zero exit, empty / invalid
    output) and lets :class:`SandboxUnavailableError` propagate; the request path
    renders each as its own 503.

    Bounded by :data:`_LIST_MODELS_BACKGROUND_TIMEOUT_SECS`, NOT the request wait,
    so a cold start that outlasts one poll still finishes and warms the cache for
    the next one.
    """
    from kiro_crew.env import augmented_path  # noqa: F811

    kiro_bin = await resolve_kiro_bin_for_spawn()
    if not kiro_bin:
        # Degraded (binary not resolved yet), NOT a genuine "zero models" result.
        # 503 so the client retries instead of caching an empty list — a cached
        # [] renders an empty picker that only a manual page refresh recovers from.
        raise _CatalogUnavailable("kiro binary not resolved")
    argv = [kiro_bin, "chat", "--list-models", "--format", "json", "--no-interactive"]
    # Mirror AcpClient._spawn() sandbox: wrap_argv + env + process isolation.
    # Note: AcpClient._spawn() is for interactive ACP sessions (stdin/stdout
    # pipes); this is a one-shot read-only command, so we replicate the
    # sandbox setup directly.  See the security-controls rule.
    #
    # The configured tier is passed EXPLICITLY rather than left to
    # wrap_argv's "auto" parameter default, so this endpoint can never ask
    # for stricter isolation than the chat spawn of the same binary. It
    # matters wherever the operator set agent.sandbox="off" (deferring
    # isolation to kiro-cli's own internal sandbox): the one-shot and chat
    # path must have one posture. The explicit Kiro classification also
    # makes the shipped "auto" tier work on Windows via Kiro's built-in
    # sandbox instead of answering 503 on every 8s poll.
    #
    # OFF the loop: `configured_sandbox_mode()` stats (and on a cache miss
    # re-reads + revalidates) config.json, and `wrap_argv` -> `detect_backend`
    # can cold-probe the backend with a synchronous
    # `subprocess.run(..., timeout=5)`. This runs behind the request, but a
    # blocking call on the event loop still stalls chat, cron and the liveness
    # heartbeat on exactly the host where the probe is slowest. Both reads run
    # in the worker, so the mode is resolved there too rather than passed in.
    #
    # A remote hub proxying this endpoint budgets its WHOLE cold path (the
    # sandbox detection, the list-models subprocess, and the up to
    # _READ_PATH_PROBE_DEADLINE_SECS the read-path entitlement revalidation
    # waits in _entitled_kiro_models) via
    # DEFAULT_MODELS_CAPABILITY_PROXY_TIMEOUT_SECS in
    # kiro_crew/instances/constants.py — 5 + 10 + 3 < 20. The per-request wait
    # (_LIST_MODELS_SUBPROCESS_TIMEOUT_SECS) is what that budget sizes against,
    # NOT the longer background ceiling; growing the request wait means moving
    # that constant with it.
    argv, cleanup = await asyncio.get_running_loop().run_in_executor(
        subprocess_executor(), _wrap_list_models_argv, argv
    )
    argv = cgroup_scope_argv(argv)  # cgroup DoS ceiling
    try:
        env = {**os.environ}
        env["PATH"] = augmented_path(env.get("PATH", ""))
        # OFF the loop: the resolver globs /tmp/ssh-*/agent.* and stats
        # every hit, so its latency scales with the /tmp entry count. Its
        # sibling wrapper's contract states it must never run on the event loop.
        await asyncio.to_thread(resolve_ssh_auth_sock, env)
        # The Docker entrypoint removes credentials from the long-lived
        # gateway environment.  This fixed-argv child is the official
        # kiro-cli and KIRO_API_KEY is its own model credential, so settle
        # the same single key the interactive ACP spawn receives.  Keep
        # the protected .env read off the gateway loop.
        await asyncio.to_thread(inject_kiro_cli_api_key, env)
        env = scrub_agent_subprocess_env(env)
        # Supervised so the call ends whatever it leaves behind. A kiro-cli
        # launcher wrapper can start a ~140-thread credential helper for each
        # call and leave it running; the self-heal loop re-polls every 8s while
        # degraded, so on a gateway on that path every poll leaked one until
        # the agent cgroup ran out of pids.
        proc = await spawn_supervised_oneshot(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=_LIST_MODELS_BACKGROUND_TIMEOUT_SECS
            )
        except asyncio.TimeoutError:
            # The whole group, while the supervisor still leads it: killing
            # only the leader would leave the command and its helpers running.
            await kill_and_reap(proc)
            # A cold CLI spawn exceeded even the background ceiling. 503 so the
            # client keeps its last-good list and polls again rather than caching
            # a successful empty result.
            logger.warning("api_models: --list-models timed out; returning 503")
            raise _CatalogUnavailable("model list timed out")
    finally:
        if cleanup and callable(cleanup):
            cleanup()

    if proc.returncode != 0:
        from kiro_crew.platform import redact_via_context  # noqa: F811

        stderr_tail = stderr.decode(errors="replace").strip()
        stderr_tail = redact_via_context(stderr_tail)[-_MODEL_LIST_STDERR_TAIL_CHARS:]
        logger.warning(
            "api_models: --list-models exited %s: %s; returning 503",
            proc.returncode,
            stderr_tail or "<no stderr>",
        )
        raise _CatalogUnavailable("model list command failed")

    if not stdout.strip():
        logger.warning("api_models: --list-models returned empty output; returning 503")
        raise _CatalogUnavailable("model list returned empty output")

    try:
        data = json.loads(stdout.decode(errors="replace"))
    except json.JSONDecodeError as exc:
        logger.warning(
            "api_models: --list-models returned invalid JSON (%s); returning 503",
            exc,
        )
        raise _CatalogUnavailable("model list returned invalid JSON")
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        logger.warning("api_models: --list-models returned an invalid payload; returning 503")
        raise _CatalogUnavailable("model list returned an invalid payload")
    models = data["models"]
    # Seed the central window authority from kiro's authoritative structured
    # 'context_window_tokens' field (keyed by model_id/model_name). This is
    # the ONE place these rows enter the system; every other consumer (the
    # ACP backfill, the context-budget scaler, the live meter) then resolves
    # through model_registry.model_window() rather than re-reading kiro. The
    # in-memory update is synchronous (cheap dict mutation); only the disk
    # persist is offloaded to an executor so the event loop never blocks on
    # filesystem I/O (no blocking call on the event loop).
    #
    # This fork keeps kiro's bare-dotted ids as the picker WIRE FORMAT
    # (guarded by _model_rejected_reason / api_chat_slot_model, which rejects
    # canonical registry keys the ACP CLI can't accept). The upstream
    # registry-key canonicalization is deliberately NOT ported — it is
    # incompatible with this fork's _model_rejected_reason guard. The window
    # seeding above uses kiro's authoritative context_window_tokens to give
    # the backfill real GPT/DeepSeek/Qwen windows, independent of the
    # wire-format choice.
    #
    # The same rows also warm the ``acp`` advertised-model cache, kiro's
    # VOCABULARY: which ids are kiro's own, so model_scope can tell a pin
    # chosen for another harness from one chosen here before any session
    # exists (the chip and the provider factory judge from the cache; the
    # wire holds the live list). ONE admission feeds both caches
    # (refresh_kiro_catalog), so an id the bound refuses gets no row in
    # either. Fed from the UNFILTERED catalog on purpose: a deprecated or
    # unentitled row is still a kiro id, and dropping it here would make
    # model_scope call a native pin foreign. Entitlement stays with the
    # live ``session/new`` list downstream (_entitled_kiro_models,
    # model_is_unusable) -- ``--list-models`` is a catalog and no reader
    # of this cache treats it as more. Sourced here rather than from any
    # ``session/new`` payload because the registry attributes that payload
    # to claude-agent-acp and a kiro session's list is scoped to the agent
    # that session started. In-memory updates on the loop, disk persists
    # off it.
    windows_changed, advertised_changed = model_registry.refresh_kiro_catalog(
        models, model_registry_namespace(ACP_BACKEND_KIRO)
    )
    if windows_changed:
        await asyncio.get_running_loop().run_in_executor(
            maintenance_executor(), model_registry.persist_kiro_windows
        )
    if advertised_changed:
        await asyncio.get_running_loop().run_in_executor(
            maintenance_executor(), model_registry.persist_advertised_models
        )

    def wire_row(row: dict) -> dict:
        # Every reader downstream treats a row's ``model_name`` as the model id:
        # the entitlement narrowing judges it against the live ``session/new``
        # ``availableModels`` ids, the pin validators compare it literally, and
        # the picker sends it to ``session/set_model``. kiro-cli prints a
        # ``model_id`` beside the name, and a model can carry a display name that
        # differs from its id. ``session/new`` advertises the ``model_id``, so a
        # row left under its printed name is never found among the advertised ids
        # and the picker hides a model the account can run. Such a row is served
        # under the ``model_id``, with the printed name kept as ``display_name``;
        # a row with no usable ``model_id`` is returned unchanged. Nested rather
        # than module-level: the facade's definitions are pinned by
        # ``test/test_dashboard_agents_composition_contract.py``.
        model_id = row.get("model_id")
        name = row.get("model_name")
        if not isinstance(model_id, str) or not model_id.strip() or model_id == name:
            return row
        label = name if isinstance(name, str) and name.strip() else model_id
        return {**row, "model_name": model_id, "display_name": row.get("display_name") or label}

    return [wire_row(m) for m in models if not is_deprecated_model(m.get("model_name", ""))]


def _shared_catalog_fetch() -> "asyncio.Task[list[dict]]":
    """Return the in-flight catalog fetch, starting one if none is running.

    Single-flight: concurrent polls share one spawn. The task caches its result
    (and clears itself) when it finishes, so the next poll after a slow success
    is served straight from the cache rather than starting another cold start.
    """
    existing = _catalog_cache.task
    if existing is not None and not existing.done():
        return existing

    async def _run() -> list[dict]:
        try:
            models = await _fetch_kiro_catalog()
        finally:
            # Release the single-flight slot the moment this attempt ends,
            # win or lose, so a failed fetch does not wedge every later poll.
            _catalog_cache.task = None
        # Bound the retained list before it enters the one store that outlives
        # the request (see _bounded_catalog).
        bounded = _bounded_catalog(models)
        _catalog_cache.models = bounded
        _catalog_cache.fetched_at = time.monotonic()
        return bounded

    task = asyncio.ensure_future(_run())
    _catalog_cache.task = task
    # A stale-while-revalidate refresh is fire-and-forget: the request path
    # returns the cached list without awaiting this task, so a degraded refresh
    # (expired auth, background-ceiling timeout, SandboxUnavailableError) would
    # leave an unretrieved exception that crash_guard's asyncio handler logs as a
    # full crash record at the 8s poll cadence. Consume it here: a failed refresh
    # keeps the last-good cache and is a debug line, not a crash.
    task.add_done_callback(_consume_refresh_exception)
    return task


def _consume_refresh_exception(task: "asyncio.Task[list[dict]]") -> None:
    """Retrieve a finished refresh task's exception so it is never 'unhandled'.

    A cached catalog means a degraded background refresh is non-fatal — the
    request path already served the last-good list — so its exception is logged
    at debug and swallowed rather than left for ``Task.__del__`` to escalate.
    """
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.debug("api_models: background catalog refresh failed (serving cached)", exc_info=exc)


async def api_models(request: web.Request) -> web.Response:
    """GET /api/models — the model list for the configured backend.

    kiro-family backends read kiro-cli's ``--list-models`` catalog (narrowed to a
    live session's entitlement); advertised-selection backends read their own
    adapter's namespace, because they do not accept ids from that catalog.
    """
    cfg = await asyncio.to_thread(KiroCrewConfig.load)
    backend = getattr(cfg.agent, "acp_backend", "")
    if backend == ACP_BACKEND_CLAUDE:
        return web.json_response(
            _cc_models(request, configured_default=_scoped_default(cfg, backend))
        )
    if capabilities_for(backend).resolves_model_from_advertised_list:
        return web.json_response(
            _advertised_backend_models(
                request, backend, configured_default=_scoped_default(cfg, backend)
            )
        )
>>>>>>> upstream/main
    # Signed-out gateways must never reach the spawn below. kiro-cli auto-opens
    # an interactive browser login for ANY subcommand run unauthenticated
    # (--no-interactive does not suppress it, and there is no opt-out env var),
    # and the frontend polls this endpoint every 8s while the model list is
    # degraded — which is exactly the signed-out state. Ungated, that pairing
    # opened a browser window every 8s indefinitely. The 503 is the same
    # degraded response the timeout/unresolved branches already return, so the
    # client contract is unchanged; only the subprocess is skipped.
    #
    # Keep the tight destructive bound here: this endpoint polls only while the
    # model list is a degraded fallback and stops the instant a live fetch wins
    # (website/src/providers/modelListHealth.ts), so it is not polled at all when
    # healthy and gains no latency from a wider window. It has no server-side
    # cooldown on its kiro-cli spawn, so a wide stale-authorize window would let a
    # stale ready=True latch spawn a browser-opening login on most degraded ticks.
    blocked = await reject_if_kiro_unverified(request)
    if blocked is not None:
        return blocked
    try:
        cached = _catalog_cache.models
        if cached is not None:
            # Serve the last good catalog straight away; a stale one is refreshed
            # behind the reply (stale-while-revalidate). Entitlement narrowing
            # still runs on every request, so a plan change is reflected now even
            # when the catalog rows themselves are a few minutes old.
            if time.monotonic() - _catalog_cache.fetched_at >= _LIST_MODELS_CATALOG_TTL_SECS:
                _shared_catalog_fetch()
            models = await _entitled_kiro_models(request, list(cached))
            return web.json_response(models)

        # No catalog yet. Join (or start) the one shared background fetch and wait
        # at most the per-request bound for it — the SAME 10s a request waited
        # before. On timeout we answer the same degraded 503, but the fetch is NOT
        # cancelled: it runs on under its own longer ceiling and warms the cache,
        # so the next 8s poll is served from its result instead of starting
        # another doomed cold start.
        task = _shared_catalog_fetch()
        try:
            models = await asyncio.wait_for(
                asyncio.shield(task), timeout=_LIST_MODELS_SUBPROCESS_TIMEOUT_SECS
            )
        except asyncio.TimeoutError:
            # The cold spawn outran one request. Keep the shared fetch running
            # (shield already detached it from this await) so the next poll lands
            # on the warmed cache rather than re-spawning.
            logger.warning("api_models: --list-models slower than the request bound; returning 503")
            return web.json_response({"error": "model list timed out"}, status=503)
        models = await _entitled_kiro_models(request, list(models))
        return web.json_response(models)
    except _CatalogUnavailable as exc:
        # A degraded fetch outcome (binary unresolved, timeout, non-zero exit,
        # empty / invalid output). The carried body is the 503 for that outcome.
        return web.json_response({"error": exc.error}, status=503)
    except EntitlementRevalidating:
        # An entitlement revalidation is in flight past the read deadline. The
        # picker snapshot might narrow the catalog on an un-revalidated answer,
        # and the frontend caches any non-empty 200 with no refetch — so serve
        # the degraded 503 contract instead: the frontend keeps its last-good
        # list and polls again in 8s, and the next read (once the probe has
        # landed, whether it corrected the list or failed open) returns 200.
        logger.info("api_models: entitlement revalidation in flight; returning 503 to re-poll")
        return web.json_response(
            {"error": "model list revalidating", "code": "model_list_revalidating"},
            status=503,
        )
    except SandboxUnavailableError as exc:
        # Narrower than the generic clause below, and BEFORE it: this is the one
        # degraded cause that no amount of retrying fixes, so it must not be
        # reported as an anonymous "model list unavailable". Reached only when the
        # tier resolved to "auto" (the shipped default) on a host with no
        # backend, where a configured "off" passes through
        # configured_sandbox_mode() above and never lands here.
        #
        # Still a 503: the client contract for "degraded, keep the last-good list
        # and poll" is what keeps the picker from caching an empty result, and a
        # 4xx here would make the frontend treat a host-capability problem as a
        # bad request. The `code` is what lets the UI tell this apart from a
        # timeout, and the log carries the sandbox layer's own remedy text (which
        # names the agent.sandbox_allow_unsandboxed_exec opt-in).
        logger.warning(
            "api_models: sandbox refused the --list-models spawn (kind=%s, detail=%s); "
            "returning 503. Retrying will not clear this — %s",
            exc.kind,
            exc.detail,
            exc,
        )
        return web.json_response(
            {"error": "model list unavailable", "code": "model_list_sandbox_unavailable"},
            status=503,
        )
    except Exception:
        # Spawn failure, JSON parse error, etc. — degraded, not "zero models".
        # 503 so the client retries instead of caching an empty picker.
        logger.warning("api_models failed; returning 503 for client retry", exc_info=True)
        return web.json_response({"error": "model list unavailable"}, status=503)


async def api_effort_levels(request: web.Request) -> web.Response:
    """GET /api/effort-levels — list available reasoning effort levels.

    Per-slot: when a ``?slot=`` query param resolves to a live ACP provider,
    return the levels that slot's CURRENT model reported (ACP escalation order),
    so concurrent slots on different models/backends each see their own set and
    a model switch is reflected immediately. Falls back to the process-global
    ordered list (cold start / no live provider / provider without the getter).
    """
    slot = request.query.get("slot")
    if slot:
        try:
            state: DashboardState = request.app["state"]
            provider = state.sessions.get_provider(_history_key_for(slot))
            getter = getattr(provider, "get_valid_effort_levels", None) if provider else None
            if callable(getter):
                levels = getter()
                if levels:
                    return web.json_response(levels)
        except (KeyError, AttributeError):
            pass
    return web.json_response(get_reasoning_effort_ordered())


async def api_slash_commands(request: web.Request) -> web.Response:
    """GET /api/slash-commands — list available slash commands (provider-aware)."""
    cfg = KiroCrewConfig.load()
<<<<<<< HEAD
    if cfg.agent.acp_backend == ACP_BACKEND_CLAUDE:
=======
    # This global endpoint has no session/member key; the configured default
    # backend is its capability authority, independent of the provider label.
    blocked_commands = _BLOCKED_SLASH_COMMANDS
    if capabilities_for(cfg.agent.acp_backend).supports_native_todos:
        blocked_commands = blocked_commands - {"/todos"}
    if is_claude_code(cfg.agent.provider):
>>>>>>> upstream/main
        state: DashboardState = request.app["state"]
        cc_commands: list[str] = []
        for provider in state.sessions.active_providers():
            cmds = getattr(provider, "_slash_commands", [])
            if cmds:
                cc_commands = cmds
                break
        if not cc_commands:
            cc_commands = [
                "compact",
                "clear",
                "context",
                "help",
                "init",
                "review",
                "security-review",
                "usage",
            ]
        result = [
            {"name": f"/{c}", "description": SLASH_COMMAND_DESCRIPTIONS.get(f"/{c}", "")}
            for c in cc_commands
            if f"/{c}" not in blocked_commands
        ]
        for command in ("/side", "/workflow"):
            if not any(item["name"] == command for item in result):
                result.append(
                    {"name": command, "description": SLASH_COMMAND_DESCRIPTIONS.get(command, "")}
                )
        return web.json_response(result)

    # Blocked commands stay in _SLASH_COMMANDS (typing one still gets the
    # explicit "not available in the dashboard" rejection in chat_runner), but
    # the suggestion payload must not advertise them: a menu entry that only
    # ever produces a warning is an inert affordance.
    return web.json_response(
        [
            {"name": c, "description": SLASH_COMMAND_DESCRIPTIONS.get(c, "")}
            for c in sorted(_SLASH_COMMANDS - blocked_commands)
        ]
    )


# Windows reserves these basenames (before the first dot, any extension) at the
# filesystem level: creating CON.json raises, and some transports mangle them.
# Checked wherever a template filename is chosen — user-supplied publish names
# are refused, generated fork names are suffixed past them.
_WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


# ── Kiro Crew Agent CRUD API ──


async def api_kirocrew_agents(request: web.Request) -> web.Response:
    """GET /api/agents — list all Kiro Crew agent definitions, most-used first.

    Also surfaces the requesting session's project-scope agents
    (``<project>/.kiro/agents``, resolved via ``X-Session-Key``) tagged
    ``scope="project"`` — these dispatch from that slot because kiro-cli runs
    with the slot's project as cwd, so the picker must offer them. A config
    alias of the same name is listed once, as the alias:
    dispatch resolves aliases first, so the alias is what would answer.
    """
    cfg = KiroCrewConfig.load()
    # Caller class, resolved once for the whole response. It decides only VALUE
    # treatment, never the key set -- see ``_roster_mask``.
    #
    # The OWNER predicate, not an app-token check. `request.get("app", "")` alone
    # asks "is this an app?", and a non-owner DASHBOARD session answers no: an
    # allow-listed messaging user running `!dashboard` holds a dashboard token
    # with `app == ""` and would have sailed through, which is the same
    # caller-class hole that keeps reappearing when this question is hand-rolled
    # per class instead of delegated to the one predicate that already answers
    # it. `is_owner_dashboard_request` is what `_require_owner` resolves to for
    # the mutating agents routes, so the read and write sides now agree
    # on who the owner is.
    #
    # Fails CLOSED -- treated as NOT the owner, so masked -- when the app carries
    # no state to resolve an owner against. The predicate subscripts
    # `app["state"]`, and for a disclosure control "unknown caller" must mean
    # "mask", not "show".
    from kiro_crew.dashboard.handlers.source_providers import is_owner_dashboard_request

    redact = request.app.get("state") is None or not is_owner_dashboard_request(request)
    agents = [
        _agent_roster_row(name, "global", agent_cfg, redact=redact)
        for name, agent_cfg in cfg.agents.items()
    ]

    state: DashboardState | None = request.app.get("state")

    # Project rows come from a directory scan, so it runs on the discovery
    # pool — same rule as every other agent listing: no filesystem I/O on the
    # event loop. Failure costs only the project rows, never the roster.
    project_dir = active_project_dir(state, _read_session_key(request)) if state else ""
    if project_dir:
        try:
            project_names = await asyncio.get_running_loop().run_in_executor(
                discovery_executor(),
                functools.partial(
                    project_agent_names,
                    project_dir,
                    operation="api_kirocrew_agents",
                    source="dashboard",
                ),
            )
        except Exception:
            logger.warning("Failed to list project agents for %s", project_dir, exc_info=True)
            project_names = frozenset()
        # One shared default record for every project row — they carry no
        # per-agent config of their own (nothing on disk to read without a
        # second scan), so the row is the default record under a project tag.
        project_default = KiroCrewAgentConfig()
        agents.extend(
            _agent_roster_row(name, "project", project_default, redact=redact)
            for name in sorted(project_names - set(cfg.agents.keys()))
        )

    # Reorder by usage frequency (most-used first). Derived read-only from chat
    # history; degrade to config-insertion order on any failure so the dropdown
    # never breaks or drops agents when history is unreadable.
    conversation_log = state.conversation_log if state else None
    if conversation_log:
        try:
            usage = await asyncio.to_thread(conversation_log.agent_usage)
            # Default missing agents to (0, 0) — keeps the sort key total and
            # deterministic (never negates None); never-used agents collapse to
            # their config-insertion index and form a stable bottom block.
            sorted_agents = sorted(
                enumerate(agents),
                # ``str(...)`` because the row's value type widened to ``object``
                # for ``avatar`` (the one structured field); ``name`` is always a
                # ``str`` -- masked or verbatim, ``_roster_mask`` returns one.
                key=lambda item: (
                    -usage.get(str(item[1]["name"]), (0, 0.0))[0],
                    -usage.get(str(item[1]["name"]), (0, 0.0))[1],
                    item[0],
                ),
            )
            agents = [a for _, a in sorted_agents]
        except Exception:
            logger.warning("Failed to sort agents by usage; using config order", exc_info=True)

    return web.json_response(
        {
            "agents": agents,
            "default_agent": cfg.default_agent,
        }
    )


_config_lock = LoopBoundLock()


def _get_config_lock() -> LoopBoundLock:
    """Return the config lock (loop-bound; rebinds when the running loop changes)."""
    return _config_lock


def _pin_entitlement_backend(cfg: Any) -> str:
    """The harness whose live catalog may judge a crew's model pin.

    Every agent the crew create and update handlers write is a Crew Member whose DM slot
    (``member-<slug>``) routes through ``agent.member_acp_backend`` — not
    through the configured default harness ``agent.acp_backend``. When the two
    share a model-registry namespace, the default backend scopes the
    entitlement evidence correctly (kiro, including the empty default backend,
    and kas share ``acp``). When they do not, the default's catalog cannot
    establish whether the pin the DM thread will actually run is usable — a
    live kiro session's catalog would deterministically reject a
    claude-advertised id — so the evidence must come from the harness the DM
    thread will ACTUALLY run on, which is ``member_backend``. Returning it (not
    ``None``) keeps the scope on the member's own namespace: a provider from an
    unrelated harness can neither admit nor reject the pin, and when no member
    -namespace provider is live the catalog is simply unknown (fail-open) rather
    than judged by the wrong backend's advertised ids.
    """
    default_backend = getattr(cfg.agent, "acp_backend", "")
    member_backend = getattr(cfg.agent, "member_acp_backend", "")
    if (
        capabilities_for(member_backend).model_id_namespace
        != capabilities_for(default_backend).model_id_namespace
    ):
        return member_backend
    return default_backend


async def _revalidate_crew_pin(model: str, request: web.Request) -> str | None:
    """Revalidate the snapshot a crew's model pin is about to be judged by.

    Awaited BEFORE the handlers take the config lock: :func:`_model_pin_rejected`
    runs synchronously inside it and cannot probe, and a probe must not hold the
    lock for its read deadline. Resolves the same entitlement backend the locked
    check will use and hands off to the role-pin revalidation, which heals the
    live snapshot in place. Returns a denial reason only while that probe is still
    in flight past its deadline; ``None`` otherwise.

    Skips the cases the locked check answers without the live list -- inherit,
    the retained claude_code seam and a known wrong-flavour spelling -- so no probe
    is spent on a value the snapshot does not decide.
    """
    if not model or model == "auto" or model_registry.acp_id_correction(model):
        return None
    cfg = await asyncio.to_thread(KiroCrewConfig.load)
    if is_claude_code(cfg.agent.provider):
        return None
    # circular import: see _model_pin_rejected.
    from kiro_crew.dashboard.handlers.core import _revalidate_role_pin_evidence

    return await _revalidate_role_pin_evidence(
        model, request, backend=_pin_entitlement_backend(cfg)
    )


<<<<<<< HEAD
def _effort_inputs(crew: KiroCrewAgentConfig | None) -> tuple[str, str] | None:
    """The crew fields `resolve_session_effort` reads, or ``None`` for no crew.

    Derived from the resolver's inputs rather than enumerated per call site. The
    chain reads two things off the record -- the pin itself, and the bound
    ``kiro_agent`` the role default keys on -- and the factory answers from the
    config it captured, so ANY change to either (including a crew appearing or
    disappearing) must invalidate that capture. Three rounds of review found the
    per-condition version incomplete one case at a time (an unpinned crew whose
    binding makes it a background worker; a re-bound `kiro_agent`); comparing this
    tuple before and after a write is the invariant those cases are instances of,
    and a future field the chain starts reading is added here once instead of at
    every handler.
    """
    if crew is None:
        return None
    return (crew.kiro_agent, coerce_effort(crew.reasoning_effort))


async def _refresh_session_defaults(request: web.Request, crew: str) -> None:
    """Rebuild the provider factory so a crew's new effort pin reaches new sessions.

    The factory resolves the pin from the config it captured when it was built, so
    a write alone stays invisible until a restart. That is the same staleness
    ``api_kirocrew_config_patch`` already handles for ``agent.reasoning_effort``
    and ``agent.role_efforts.*``, and for the same reason it uses
    ``refresh_defaults()`` rather than ``reload_provider_factory()``: the factory
    is rebuilt and the warm pool drained WITHOUT touching live sessions, so an
    in-flight turn is not killed because a default changed. The pool must drain
    either way -- a pre-warmed child carries the old effort overlay, and the claim
    path never re-pushes effort.

    Best-effort: the write is already durable, so a crew save must not fail
    because the refresh did. A failure costs one gateway lifetime of staleness,
    which is what the behaviour was before this call existed.
    """
    state = request.app.get("state")
    sessions = getattr(state, "sessions", None)
    if sessions is None:
        return
    try:
        await sessions.refresh_defaults()
    except Exception:
        logger.warning(
            "Could not refresh session defaults after saving crew %r; the pin "
            "applies from the next gateway start",
            crew,
            exc_info=True,
        )


def _crew_effort_rejected(raw: object) -> str | None:
    """Reason a crew's reasoning-effort pin is unusable, or ``None`` to allow it.

    Rejects rather than coercing, which is the opposite of the config-file load
    path (:func:`coerce_effort`). The difference is who is watching: a typo in a
    hand-edited file must not stop the gateway from booting, but a typo sent by
    the crew form has an author on the other end, and silently storing ``""``
    would read back as "inherits" and look like the save was lost.

    ``""`` is the inherit sentinel and always allowed -- it is how a pin is
    cleared.
    """
    if not isinstance(raw, str):
        return "reasoning_effort must be a string"
    val = raw.strip()
    if val in EFFORT_VALUES:
        return None
    return "reasoning_effort must be one of: " + ", ".join(("(empty)", *EFFORT_LEVELS))


def _model_pin_rejected(model: str, request: web.Request, backend: str) -> str | None:
=======
def _model_pin_rejected(
    model: str, request: web.Request, provider: str, *, backend: str | None = None
) -> str | None:
>>>>>>> upstream/main
    """Reason a crew's model pin is unusable, or ``None`` to allow it.

    An agent's ``model`` is read by kiro-cli when the child starts, so a pin the
    account cannot serve kills every session and subagent using that agent
    seconds after spawn, before anything can inspect it. Rejecting it here — at
    the one moment a human is looking at the value — turns that into a single
    message on the surface that authored it.

    *backend* is passed in rather than resolved here so this whole path adds no
    config read of its own: every caller already holds a loaded config, and
    ``KiroCrewConfig.load()`` deep-copies the validated dict even on a cache
    hit — work that must not land on the event loop while the config lock is
    held. It is forwarded to the validator for the same reason.

    A known wrong-flavour registry spelling is reported before entitlement: a
    live advertised set would otherwise replace the actionable ACP-id mapping
    with a generic "not available" error. All other values delegate to the
    per-role validator so the crew form, the role pins and the session-init
    withhold apply one predicate. ``""``/``"auto"`` mean inherit and always
    pass; an unknown advertised set means entitlement is unknowable, and the
    validator accepts rather than accusing on no evidence.
    """
    # The retained claude_code seam accepts canonical and registered Bedrock
    # wire ids that the ACP correction and advertised-id comparison below
    # intentionally map away from. Its entitlement guard lives in its own
    # provider path, where full configured ids and bare advertised ids can be
    # canonicalized before comparison.
    # Harness selection is agent.acp_backend (harness-parity); "claude" is the
    # backend upstream calls claude_code.
    if backend == ACP_BACKEND_CLAUDE:
        return None

    # The registry knows each model under several spellings and only one is what
    # kiro-cli serves; the others reach the child verbatim and kill it at startup.
    # Check this before live entitlement because a wrong-flavour id is naturally
    # absent from that set and would otherwise produce a less actionable error.
    correction = model_registry.acp_id_correction(model)
    if correction:
        # Deliberately NOT prescriptive. Upstream naming does not line up across
        # providers — Bedrock's ``claude-opus-4-8`` is the registry's
        # ``claude-opus-4.5``, while ``claude-opus-4-8[1m]`` is ``claude-opus-4.8``
        # — so a user who typed the Bedrock spelling meaning "Opus 4.8" may not
        # want the id this maps to. Telling them to adopt it would steer a
        # plausible-intent user into a quieter capability change than the one
        # they asked for. Report the mapping, show what is actually served, and
        # let them choose.
        served = ", ".join(model_registry.available_models("acp")[:8]) or "auto"
        return (
            f"{model!r} is not a model kiro-cli serves. The registry maps that "
            f"spelling to {correction!r} — confirm that is the model you want, or "
            f"pick one of: {served}, or 'auto'."
        )
    # circular import: handlers.core resolves _get_config_lock from this module,
    # so importing it at module scope would close the cycle.
    from kiro_crew.dashboard.handlers.core import _validate_role_model

<<<<<<< HEAD
    return _validate_role_model(model, request, backend=backend)


async def api_kirocrew_agents_create(request: web.Request) -> web.Response:
    """POST /api/agents — create a new KiroCrew agent."""

    denied = await _require_owner(request, "agent.create")
    if denied is not None:
        return denied
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    if not isinstance(body, dict):
        return web.json_response(
            {"error": "body must be an object", "code": "body_not_object"}, status=400
        )
    name = body.get("name", "").strip()
    if not name:
        return web.json_response({"error": "Agent name is required"}, status=400)
    # The template pointer must be EXPLICIT. It used to default to "kirocrew",
    # which made every crew created without naming a template an alias for the
    # DEFAULT agent: dispatch flattens an alias to its `kiro_agent`
    # (config.loader.resolve_agent_bindings), so the crew was offered in the chat
    # picker and then the default answered — the "picker reverts to default"
    # report behind #1684. "kirocrew" is still a perfectly valid CHOICE here (a
    # crew booting the built-in agent against its own workspace/memory store is
    # the common case); only the silent default is refused.
    kiro_agent = str(body.get("kiro_agent") or "").strip()
    if not kiro_agent:
        return web.json_response(
            {
                "error": "kiro_agent is required — name the agent this crew boots "
                "from (pass 'kirocrew' for the built-in agent)",
                "code": "kiro_agent_required",
            },
            status=400,
        )
    # Grammar-checked before the name is persisted or used to look anything up.
    # This is the one shared agent-name grammar every other boundary uses, so a
    # value that cannot name an agent (path separators, traversal, wildcards,
    # over-length) is refused here rather than stored as a dangling pointer.
    if not _AGENT_NAME_RE.match(kiro_agent):
        return web.json_response(
            {"error": "invalid kiro_agent name", "code": "invalid_kiro_agent_name"},
            status=400,
        )
    # Existence is resolved through `list_agents()`, which reads every spec via the
    # hardened reader: it resolves symlinks, refuses a spec whose REAL target is
    # sensitive, and goes through the same gate as every other dashboard file read.
    # A direct filename probe here called `Path.read_text()` itself, so a namespaced
    # agent file symlinked at a credentials path would have been read outside that
    # gate. `list_agents()` is also the broader and more accurate notion of
    # existence: it includes edition-provided rows that are ACP-resolvable with no
    # on-disk file, which is what "will this actually dispatch" means.
    # Off the loop: it scans and parses the agent directories.
    known_agents = await asyncio.get_running_loop().run_in_executor(
        discovery_executor(), lambda: {a.name for a in list_agents()}
    )
    template_missing = kiro_agent not in known_agents
    # Unknown-but-accepted: an edition may resolve a row this listing cannot see,
    # so refusing here would break a legitimate crew. WARN instead — the same
    # posture, and for the same reason, as the sync path's EXECUTABLE INVARIANT
    # check — so a crew that will fail at spawn leaves a trace rather than
    # failing silently later.
    if template_missing:
        logger.warning(
            "creating crew %r against template %r, which is not in the installed "
            "agent listing — if it is not ACP-resolvable the crew will fail at spawn",
            name,
            kiro_agent,
        )
    # Passed RAW, not str()-coerced: normalize_agent_model is total and maps a
    # non-string to "" (inherit). Wrapping in str() first would turn
    # {"model": 123} into the literal "123", which normalizes to a string the
    # backend then rejects as an unknown model id.
    model = normalize_agent_model(body.get("model"))
    _raw_color = body.get("session_color", "")
    session_color = _safe_color(_raw_color)
    if _raw_color not in ("", None) and not session_color:
        return web.json_response(
            {"error": "session_color must be #rrggbb or empty", "code": "invalid_color_hex"},
            status=400,
        )
    _raw_effort = body.get("reasoning_effort", "")
    effort_reason = _crew_effort_rejected(_raw_effort)
    if effort_reason:
        return web.json_response(
            {"error": effort_reason, "code": "invalid_reasoning_effort"}, status=400
        )
    reasoning_effort = _raw_effort.strip()
    # Same convention as session_color: a non-empty raw value that the coercer
    # collapses to "no override" is a caller mistake worth a 400, not a silent
    # fallback to the name-derived face. The one exception is a well-formed
    # ghost override whose traits all coerce to absent: that collapse is the
    # validator's own all-empty→reset rule, not caller junk, so it stores as
    # the canonical reset rather than being refused.
    _raw_avatar = body.get("avatar")
    avatar = _safe_avatar(_raw_avatar)
    if _raw_avatar not in (None, {}) and not avatar and not _is_ghost_shaped(_raw_avatar):
        return web.json_response(
            {
                "error": "avatar must be {'kind': 'ghost', 'traits': {...}}, {'kind': 'image'}, or empty",
                "code": "invalid_avatar",
            },
            status=400,
        )
    if avatar.get("kind") == "image":
        # A crew that does not exist yet cannot have staged a picture (the
        # upload endpoint 404s for unknown names), so an image override on
        # create can never have a file to commit.
        return web.json_response(
            {
                "error": "upload the picture after creating the crew",
                "code": "avatar_file_missing",
            },
            status=400,
        )
    async with _get_config_lock():
        cfg = KiroCrewConfig.load()
        if name in cfg.agents:
            return web.json_response({"error": f"Agent '{name}' already exists"}, status=409)
        model_reason = _model_pin_rejected(model, request, getattr(cfg.agent, "acp_backend", ""))
        if model_reason:
            return web.json_response({"error": model_reason, "code": "invalid_model"}, status=400)
        cfg.agents[name] = KiroCrewAgentConfig(
            kiro_agent=kiro_agent,
            workspace=body.get("workspace", "default"),
            memory_store=body.get("memory_store", "default"),
            model=model,
            reasoning_effort=reasoning_effort,
            description=body.get("description", ""),
            triggers=body.get("triggers", ""),
            source=body.get("source", "kirocrew"),
            session_color=session_color,
            avatar=avatar,
        )
        cfg.save()
    # A crew APPEARING changes what the effort chain resolves even with no pin of
    # its own: the factory's captured config does not know the crew, so it cannot
    # read the binding the role default keys on, and a scheduled or messaging
    # session naming that crew would take the chat default instead. Creation is
    # therefore always a change by `_effort_inputs` (None -> a tuple).
    await _refresh_session_defaults(request, name)
    _sel().log_api_access(
        caller=request.get("user", "dashboard"),
        operation="agent.create",
        outcome="success",
        source="dashboard",
        resources=name,
    )
    return web.json_response({"ok": True, "name": name})


async def api_kirocrew_agent_update(request: web.Request) -> web.Response:
    """PUT /api/agents/{name} — update a KiroCrew agent."""

    denied = await _require_owner(request, "agent.update")
    if denied is not None:
        return denied
    name = request.match_info["name"]
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    if not isinstance(body, dict):
        return web.json_response(
            {"error": "body must be an object", "code": "body_not_object"}, status=400
        )
    if "model" in body:
        pending_model = normalize_agent_model(body["model"])
    # Rejected before the config is even loaded: the check is pure, and every
    # validation must land before the first field assignment below so a bad value
    # cannot leave the in-memory record half-updated.
    if "reasoning_effort" in body:
        effort_reason = _crew_effort_rejected(body["reasoning_effort"])
        if effort_reason:
            return web.json_response(
                {"error": effort_reason, "code": "invalid_reasoning_effort"}, status=400
            )
    async with _get_config_lock():
        cfg = KiroCrewConfig.load()
        if name not in cfg.agents:
            return web.json_response({"error": f"Agent '{name}' not found"}, status=404)
        if "model" in body:
            # Validated before the write, reusing the config loaded just above so
            # this costs no extra read.
            model_reason = _model_pin_rejected(pending_model, request, getattr(cfg.agent, "acp_backend", ""))
            if model_reason:
                return web.json_response(
                    {"error": model_reason, "code": "invalid_model"}, status=400
                )
        agent = cfg.agents[name]
        # Captured BEFORE any mutation: what the effort chain reads today.
        effort_inputs_before = _effort_inputs(agent)
        changed: list[str] = []
        if "kiro_agent" in body:
            agent.kiro_agent = body["kiro_agent"]
            changed.append("kiro_agent")
        if "workspace" in body:
            agent.workspace = body["workspace"]
            changed.append("workspace")
        if "memory_store" in body:
            agent.memory_store = body["memory_store"]
            changed.append("memory_store")
        if "model" in body:
            # "auto"/"" both mean inherit; store the single "" spelling so the
            # agent keeps deferring to the kiro pin / global fallback. Raw, not
            # str()-coerced — see the create path for why.
            agent.model = normalize_agent_model(body["model"])
            changed.append("model")
        if "reasoning_effort" in body:
            # Already validated above; "" is the inherit sentinel and clears a pin.
            agent.reasoning_effort = body["reasoning_effort"].strip()
            changed.append("reasoning_effort")
        if "description" in body:
            agent.description = body["description"]
            changed.append("description")
        if "triggers" in body:
            agent.triggers = body["triggers"]
            changed.append("triggers")
        if "session_color" in body:
            _sc = body["session_color"]
            _norm = _safe_color(_sc)
            if _sc not in ("", None) and not _norm:
                return web.json_response(
                    {
                        "error": "session_color must be #rrggbb or empty",
                        "code": "invalid_color_hex",
                    },
                    status=400,
                )
            agent.session_color = _norm
            changed.append("session_color")
        _avatar_promoted = False
        _avatar_pin = ""
        _prior_pin: object = None
        _remove_files_after_save = False
        if "avatar" in body:
            _raw_av = body["avatar"]
            _av = _safe_avatar(_raw_av)
            # Same 400 convention as session_color: junk that coerces to "no
            # override" is refused rather than silently clearing the face.
            # None/{} are the explicit "reset to name-derived" spellings, and
            # a well-formed ghost override that collapses all-empty is the
            # validator's own reset rule, not caller junk.
            if _raw_av not in (None, {}) and not _av and not _is_ghost_shaped(_raw_av):
                return web.json_response(
                    {
                        "error": "avatar must be {'kind': 'ghost', 'traits': {...}}, {'kind': 'image'}, or empty",
                        "code": "invalid_avatar",
                    },
                    status=400,
                )
            if _av.get("kind") == "image":
                # THE commit point for pictures, under this same config lock.
                # `promote` is a wire-only directive (never persisted — the
                # validator drops it): the client sets it exactly when THIS
                # save staged a fresh upload. Without it, a leftover staging
                # from an earlier failed or abandoned save must NOT ride along
                # into an unrelated edit — it is discarded instead, and the
                # crew keeps wearing its current picture.
                _tok = _raw_av.get("token") if isinstance(_raw_av, dict) else None
                _wants_promote = isinstance(_raw_av, dict) and _raw_av.get("promote") is True
                _prior_pin = agent.avatar.get("file")
                if _wants_promote and not isinstance(_tok, str):
                    # `promote` without its staging token must not slide into
                    # the picture-keeping branch: that would discard the
                    # staged replacement and report success for a save that
                    # installed nothing.
                    return web.json_response(
                        {
                            "error": "promote requires the staging token from the upload",
                            "code": "avatar_file_missing",
                        },
                        status=400,
                    )
                if _wants_promote and isinstance(_tok, str):
                    _promoted = await _drained_to_thread(_promote_pending_avatar, name, _tok)
                    _avatar_promoted = _promoted is not None
                    if _promoted is None:
                        # The bytes THIS save staged are gone (a newer save
                        # re-staged the slot, or staging was cleaned up).
                        # Falling back to the current live picture would
                        # report success while silently dropping the user's
                        # selected replacement — fail the commit instead.
                        return web.json_response(
                            {
                                "error": "staged avatar no longer matches this save"
                                " — upload the picture again",
                                "code": "avatar_file_missing",
                            },
                            status=400,
                        )
                    stamp, _avatar_pin = _promoted
                else:
                    await _drained_to_thread(_discard_pending_avatar, name)
                    # A picture-keeping edit (no fresh upload): stamp from the
                    # file the config's pin already selects.
                    _live = await asyncio.to_thread(_live_avatar_file, name, _prior_pin)
                    stamp = None
                    if _live is not None:
                        _avatar_pin = _live.name[len(_avatar_stem(name)) + 1 :]
                        try:
                            stamp = int((await asyncio.to_thread(_live.stat)).st_mtime_ns)
                        except OSError:
                            stamp = None
                if stamp is None:
                    return web.json_response(
                        {
                            "error": "no uploaded avatar file to commit — POST the picture first",
                            "code": "avatar_file_missing",
                        },
                        status=400,
                    )
                _av = {"kind": "image", "v": stamp, "file": _avatar_pin}
            elif agent.avatar.get("kind") == "image":
                # Leaving the picture tier: the stored file must not linger
                # as a silently-retrievable orphan — but only once the config
                # write that stops selecting it has actually succeeded.
                _remove_files_after_save = True
            agent.avatar = _av
            changed.append("avatar")
        if "source" in body:
            agent.source = body["source"]
            changed.append("source")
        effort_inputs_after = _effort_inputs(agent)
        # The config write is the transaction's point of no return: on
        # failure the orphaned install is removed; on success the commit
        # reaps every variant except the newly pinned one.
        # `Exception`, NOT `BaseException`: a cancellation arriving here does
        # not mean the save failed — the drained worker runs to completion,
        # so on cancellation the save either fully landed (config and pin
        # consistent; only the commit-time reap is skipped, leaving orphan
        # variants the pin never serves) or raised a real exception, which
        # takes the rollback path below. Rolling back on the cancellation
        # itself would delete the file a completed save now pins.
        try:
            await _drained_to_thread(cfg.save)
        except Exception:
            if _avatar_promoted:
                await _drained_to_thread(_rollback_promoted_avatar, name, _avatar_pin, _prior_pin)
            raise
        if _avatar_promoted:
            await _drained_to_thread(_commit_promoted_avatar, name, _avatar_pin)
        if _remove_files_after_save:
            await _drained_to_thread(_remove_avatar_files, name)
    # Compared, not merely "the body carried the field": the crew form sends
    # reasoning_effort on every save (that is what makes clearing a pin possible)
    # and refresh_defaults drains the warm pool, so refreshing on presence would
    # cost a cold start on every unrelated crew edit. A re-bound kiro_agent counts
    # too -- the role default reads it. Outside the config lock, because the
    # refresh takes the session locks.
    if effort_inputs_after != effort_inputs_before:
        await _refresh_session_defaults(request, name)
    _sel().log_api_access(
        caller=request.get("user", "dashboard"),
        operation="agent.update",
        outcome="success",
        source="dashboard",
        resources=f"{name} ({','.join(changed)})",
    )
    return web.json_response({"ok": True, "name": name})


async def api_kirocrew_agent_delete(request: web.Request) -> web.Response:
    """DELETE /api/agents/{name} — delete a KiroCrew agent."""

    denied = await _require_owner(request, "agent.delete")
    if denied is not None:
        return denied
    name = request.match_info["name"]
    async with _get_config_lock():
        cfg = KiroCrewConfig.load()
        if name not in cfg.agents:
            return web.json_response({"error": f"Agent '{name}' not found"}, status=404)
        if name == cfg.default_agent:
            return web.json_response(
                {"error": f"Cannot delete default agent '{name}'. Change default_agent first."},
                status=409,
            )
        del cfg.agents[name]
        await _drained_to_thread(cfg.save)
        # The crew is gone; its uploaded picture must not outlive it. Inside
        # the same lock so the cleanup cannot run AFTER a concurrent
        # same-name recreation has already uploaded and committed a new
        # picture under the same digest stem.
        await _drained_to_thread(_remove_avatar_files, name)
    # A crew DISAPPEARING is the other half of the same invariant: the captured
    # config still holds the record, so a cron or messaging job still naming the
    # crew would keep resolving its old pin and binding.
    await _refresh_session_defaults(request, name)
    _sel().log_api_access(
        caller=request.get("user", "dashboard"),
        operation="agent.delete",
        outcome="success",
        source="dashboard",
        resources=name,
    )
    return web.json_response({"ok": True})
=======
    return _validate_role_model(model, request, provider=provider, backend=backend)
>>>>>>> upstream/main


# ── Per-crew uploaded avatars ────────────────────────────────────────
#
# The "image" tier of per-crew custom avatars: the picture lives as a file
# under the data home, the config field only records `{"kind": "image"}`
# (see config.sections._safe_avatar). Serving goes through the authenticated API —
# never a raw filesystem path — so remote dashboards work unchanged.

#: Accepted image formats, sniffed from magic bytes — the client-sent
#: Content-Type is attacker-controlled and is deliberately ignored. The set
#: itself lives in the config loader, which validates the ``ext`` pin the
#: committed config carries against the same vocabulary.
_AVATAR_IMAGE_EXTS = _LOADER_AVATAR_IMAGE_EXTS
_AVATAR_CONTENT_TYPES = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
#: Upload ceiling. The client downscales to 512px before upload, so a
#: compliant upload is tens of KB; 1 MB tolerates a generous margin while
#: keeping a hostile body from ballooning memory (parts accumulate in RAM).
_AVATAR_MAX_BYTES = 1024 * 1024


# ``asyncio.to_thread`` that a cancellation cannot abandon mid-mutation --
# moved to chat_utils so the files handler's staging copy can share the one
# implementation; the local name is kept for its callers.
_drained_to_thread = drained_to_thread


async def api_kirocrew_agent_avatar_get(request: web.Request) -> web.Response:
    """GET /api/agents/{name}/avatar — serve the crew's uploaded picture.

    Owner-gated and SEL-audited like its POST/DELETE peers. ``ETag`` derives
    from the bytes served, so a replaced picture invalidates even when size
    and second-granularity mtime coincide.
    """
    denied = await _require_owner(request, "agent.avatar_get")
    if denied is not None:
        return denied
    name = request.match_info["name"]
    # The file is served only while the crew's config actually selects it —
    # a leftover file after an out-of-band config edit or a failed cleanup
    # must not remain silently retrievable. The file pin narrows that further:
    # only the exact committed file is served, so an uncommitted install left
    # by a mid-save crash cannot impersonate the saved picture.
    cfg = await asyncio.to_thread(KiroCrewConfig.load)
    agent = cfg.agents.get(name)
    if agent is None or agent.avatar.get("kind") != "image":
        return web.json_response(
            {"error": "no uploaded avatar", "code": "avatar_not_found"}, status=404
        )
    path = await asyncio.to_thread(_live_avatar_file, name, agent.avatar.get("file"))
    if path is None:
        return web.json_response(
            {"error": "no uploaded avatar", "code": "avatar_not_found"}, status=404
        )
    data = await asyncio.to_thread(_read_avatar_file, path)
    if data is None:
        return web.json_response(
            {"error": "no uploaded avatar", "code": "avatar_not_found"}, status=404
        )
    _sel().log_api_access(
        caller=request.get("user", "dashboard"),
        operation="agent.avatar_get",
        outcome="success",
        source="dashboard",
        resources=name,
    )
    return conditional_response(
        request,
        data,
        _AVATAR_CONTENT_TYPES[path.suffix.lstrip(".")],
        etag=strong_content_etag(data),
        cache_control="private, max-age=0, must-revalidate",
    )


<<<<<<< HEAD
async def api_kirocrew_agent_avatar_upload(request: web.Request) -> web.Response:
    """POST /api/agents/{name}/avatar — STAGE the crew's picture (multipart).

    Staging only: the file lands as ``<stem>.pending.<ext>`` and nothing the
    roster serves changes. The commit point is the ordinary agent update
    (`PUT /api/agents/{name}` with ``avatar: {"kind": "image"}``), which
    promotes the staged file and writes the field under one config lock —
    so a failed or abandoned Save can never have replaced the live picture,
    and the editor's Apply→Save two-step holds for images exactly as it
    does for ghost traits.
    """
    denied = await _require_owner(request, "agent.avatar_upload")
    if denied is not None:
        return denied
    name = request.match_info["name"]
    if not (request.content_type or "").startswith("multipart/"):
        return web.json_response(
            {"error": "expected multipart/form-data", "code": "not_multipart"}, status=400
        )
    data = bytearray()
    try:
        reader = await request.multipart()
        part = await reader.next()
        # `next()` may yield a nested MultipartReader (multipart/mixed); only
        # a concrete body part carries a file, so anything else is skipped.
        while part is not None and (not isinstance(part, BodyPartReader) or part.name != "file"):
            part = await reader.next()
        if part is None:
            return web.json_response(
                {"error": "missing 'file' part", "code": "missing_file_part"}, status=400
            )
        while True:
            chunk = await part.read_chunk(64 * 1024)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > _AVATAR_MAX_BYTES:
                return web.json_response(
                    {
                        "error": f"avatar exceeds {_AVATAR_MAX_BYTES // 1024} KB limit",
                        "code": "avatar_too_large",
                    },
                    status=413,
                )
    except (ValueError, AssertionError):
        # aiohttp raises plain ValueError for a bad/missing boundary or a
        # body truncated mid-part; that is caller junk, not a server error.
        return web.json_response(
            {"error": "malformed multipart body", "code": "invalid_multipart"}, status=400
        )
    ext = _sniff_image_ext(bytes(data[:16]))
    if not ext:
        return web.json_response(
            {
                "error": "avatar must be a PNG, JPEG, or WEBP image",
                "code": "avatar_bad_format",
            },
            status=400,
        )
    # Valid magic bytes on a truncated body must not stage: promotion would
    # reap the committed picture and serve an undecodable file in its place.
    if not _image_body_complete(ext, bytes(data)):
        return web.json_response(
            {
                "error": "avatar image is truncated or malformed — re-export and upload again",
                "code": "avatar_bad_format",
            },
            status=400,
        )

    def _stage() -> None:
        d = _avatars_dir()
        d.mkdir(parents=True, exist_ok=True)
        staged = d / f"{_avatar_stem(name)}.pending.{ext}"
        # Atomic even for the staging file: a crash mid-write must not leave
        # a truncated body a later promote would install. replace_with_retry
        # rides out the Windows sharing-violation window an AV scanner or
        # indexer opens on either path.
        tmp = staged.with_suffix(f".{ext}.tmp-{uuid.uuid4().hex[:8]}")
        try:
            tmp.write_bytes(bytes(data))
            replace_with_retry(tmp, staged)
        finally:
            tmp.unlink(missing_ok=True)
        # A re-pick with a different format supersedes the previous staging.
        # Best-effort: a scanner holding a stale sibling open must not fail
        # the upload that already staged its bytes.
        for other in _AVATAR_IMAGE_EXTS:
            if other != ext:
                try:
                    (d / f"{_avatar_stem(name)}.pending.{other}").unlink(missing_ok=True)
                except OSError:
                    logger.debug("could not remove stale staging for %s (.%s)", name, other)

    # Staging happens under the config lock, with the crew's existence
    # re-checked inside it: an upload racing a crew deletion must not write
    # an orphan file the deletion's cleanup already missed. The multipart
    # body was fully read above, so the lock is held only for the short
    # filesystem commit.
    async with _get_config_lock():
        cfg = await asyncio.to_thread(KiroCrewConfig.load)
        if name not in cfg.agents:
            return web.json_response(
                {"error": f"Agent '{name}' not found", "code": "agent_not_found"},
                status=404,
            )
        await _drained_to_thread(_stage)
    _sel().log_api_access(
        caller=request.get("user", "dashboard"),
        operation="agent.avatar_upload",
        outcome="success",
        source="dashboard",
        resources=name,
    )
    return web.json_response({"ok": True, "staged": True, "token": _staging_token(bytes(data))})


# ── Conductor skill regeneration ────────────────────────────────────


def _regen_conductor() -> None:
    """Regenerate conductor skill after metadata or agent roster changes."""
    try:
        cfg = KiroCrewConfig.load()
        if not cfg.agent.conductor_skill:
            return
        from kiro_crew.conductor_skill import generate_conductor_skill  # noqa: F811
        from kiro_crew.skills import SkillsLoader  # noqa: F811

        generate_conductor_skill(SkillsLoader())
    except Exception:
        logger.exception("Failed to regenerate conductor skill")


async def api_provider_test(request: web.Request) -> web.Response:
    """POST /api/provider/test — probe a provider base URL + key.

    Body: ``{url, api_key, format, use_stored}``. Fetches ``{url}/v1/models``
    with the format-appropriate auth header and returns the advertised model
    ids on success, or an error message. Used by the Provider settings "Test"
    button. When ``use_stored`` is true and no ``api_key`` is provided, the
    saved ``agent.provider_api_key`` is used.
    """
    import aiohttp

    # Owner gate BEFORE any body handling: this endpoint can attach the stored
    # provider API key, so a non-owner must be refused without learning whether
    # its request was even well-formed.
    denied = await _require_owner(request, "provider.test")
    if denied is not None:
        return denied

    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"ok": False, "error": "invalid JSON", "code": "invalid_json"}, status=400
        )
    url = str(body.get("url") or "").strip()
    if not url:
        return web.json_response(
            {"ok": False, "error": "url required", "code": "url_required"}, status=400
        )
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return web.json_response(
            {"ok": False, "error": "url must be http(s)", "code": "url_scheme"}, status=400
        )
    api_format = str(body.get("format") or "openai")
    api_key = str(body.get("api_key") or "")
    if not api_key and body.get("use_stored"):
        # The stored key is only ever sent to the host it was saved for —
        # otherwise any page that can reach the dashboard could exfiltrate it
        # by pointing `url` at an attacker server. Loopback targets are fine
        # (local routers are the normal case); foreign hosts are not.
        cfg = KiroCrewConfig.load()
        saved = urlparse(cfg.agent.provider_base_url or "")
        if not saved.hostname or (parsed.hostname, parsed.port) != (saved.hostname, saved.port):
            return web.json_response(
                {
                    "ok": False,
                    "error": "stored key may only be tested against the saved base URL",
                    "code": "stored_key_host_mismatch",
                },
                status=400,
            )
        api_key = (cfg.agent.provider_api_key or "").strip()
    headers: dict[str, str] = {}
    if api_key:
        if api_format == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {api_key}"
    fetch_url = f"{url.rstrip('/')}/v1/models"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            # no redirects: a redirect could re-point the credentialed request
            async with session.get(fetch_url, headers=headers, allow_redirects=False) as resp:
                if resp.status != 200:
                    return web.json_response({"ok": False, "error": f"HTTP {resp.status}"})
                data = await resp.json()
                models = [m.get("id") or "" for m in data.get("data", []) if m.get("id")]
                return web.json_response({"ok": True, "models": models})
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI verbatim
        return web.json_response({"ok": False, "error": str(exc)[:200]})


async def api_provider_status(request: web.Request) -> web.Response:
    """GET /api/provider/status — check which ACP backends have their
    required binary installed.  Returns ``{opencode: bool, claude_code: bool}``
    so the frontend can warn users who select a backend without the binary.
    """
    from kiro_crew.acp.client import _resolve_claude_acp_bin, _resolve_opencode_bin

    opencode_ok = _resolve_opencode_bin() is not None
    # claude-agent-acp resolution can be slow (npm glob); run off the loop.
    claude_ok = await asyncio.to_thread(lambda: _resolve_claude_acp_bin() is not None)
    return web.json_response({"opencode": opencode_ok, "claude_code": claude_ok})
=======
# Every function the owners define runs on this module's globals, so a patch of
# ``kiro_crew.dashboard.handlers.agents.<name>`` reaches it wherever it lives;
# see ``kiro_crew.dashboard.agent_admin``. Run once, after this body has bound every
# name.
_agent_admin.compose(
    globals(),
    (
        _owner_app_mcp_ownership,
        _owner_agent_config,
        _owner_default_agent,
        _owner_capabilities,
        _owner_template_lineage,
        _owner_fork_publish,
        _owner_agent_detail,
        _owner_roster,
        _owner_installed_agents,
        _owner_crew_records,
        _owner_crew_update,
        _owner_crew_removal,
        _owner_avatars,
    ),
)
>>>>>>> upstream/main
