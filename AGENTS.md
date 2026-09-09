# Rules for AI Assistants

**This file is a ROUTER, not a manual.** It carries only the rules whose violation
causes damage before a pointer could be read. Everything else is a link you MUST
open before touching that subsystem: see
[Read before you touch](#read-before-you-touch). The frontend has its own router,
[`website/AGENTS.md`](website/AGENTS.md).

## What this is

<<<<<<< HEAD
Kiro Crew is an open-source personal AI agent: chat from Slack, a web dashboard, or
the CLI; run multi-step tasks unattended; schedule cron jobs; keep memory across
sessions. It drives an LLM through the KiroACP provider (the ACP adapter running
`kiro-cli` over ACP JSON-RPC) plus MCP tools.
=======
Kiro Crew is an open-source personal AI agent: chat from the web dashboard, the
CLI, or a messaging channel like Slack and Discord; run multi-step tasks
unattended; schedule cron jobs; keep memory across sessions. It drives an LLM
through the KiroACP provider (the ACP adapter running `kiro-cli` over ACP
JSON-RPC) plus MCP tools.
>>>>>>> upstream/main

- **Backend:** Python package `kiro_crew` in `src/kiro_crew/`. **Frontend:** React
  + TS + Vite SPA in `website/`, built into `src/kiro_crew/static/dist/` and served
  by the backend.
- **Data home:** `~/.kiro/crew`, overridden with `KIROCREW_HOME`.
- **Distribution:** public GitHub, plain setuptools, public PyPI / public npm.

Full map: [overview](docs/architecture/overview.md). This repo is the de-Amazoned
public fork of an internal package; what must never come back is
[oss-fork-boundaries](docs/system-specs/oss-fork-boundaries.md), gated by
the `internal-content-scan` check (blocking on pull requests, forks included) and
the
`no-new-builtin-apps` rule in `AUTOSDE.yaml`.

## Read before you touch

Load the doc for the row you are working in **before** you change code. Update it
in the **same commit** when you change what it documents.

| If you are touching… | Read first |
|---|---|
| `platform/`, editions, CPP seam, governance | [platform-context](docs/system-specs/modules/platform-context.md) + [governance](docs/system-specs/modules/governance.md) |
| `security.py`, `hooks.py`, denied commands, sensitive paths | [security](docs/system-specs/modules/security.md) + [sel](docs/system-specs/modules/sel.md) |
| the security model as a whole, threat boundaries | [security-deep-dive](docs/architecture/security-deep-dive.md) |
| `computer_use/` | [computer-use](docs/system-specs/modules/computer-use.md) |
| `acp/`, kiro-cli transport, providers | [acp-client](docs/system-specs/modules/acp-client.md) + [providers](docs/system-specs/modules/providers.md) |
<<<<<<< HEAD
=======
| picking or defaulting a model anywhere | [model-selection](docs/system-specs/common/model-selection.md) + [model-fallback](docs/system-specs/modules/model-fallback.md) |
| adding or adapting an agent harness (BYO, KAS, claude) | [harness-parity](docs/system-specs/modules/harness-parity.md) (invariants) + [harness-parity-gate](docs/ci/harness-parity-gate.md) (CI) |
| the publicly selectable Claude backend | [claude-code-provider](docs/system-specs/modules/claude-code-provider.md) |
>>>>>>> upstream/main
| sessions, slots, session keys, PIDs | [session](docs/system-specs/modules/session.md) + [history](docs/system-specs/modules/history.md) |
| memory, embeddings, vectors, lessons, skills, hooks | [memory-skills-hooks](docs/system-specs/modules/memory-skills-hooks.md) |
| MCP servers or tools (adding, changing, statelessness) | [mcp](docs/architecture/mcp.md) |
| apps, App Kit, manifests, app agents | [app-kit-platform](docs/system-specs/modules/app-kit-platform.md) + [app-kit/](docs/app-kit/README.md) |
| artifacts, companion chat | [artifacts](docs/system-specs/modules/artifacts.md) |
| `stt/`, `transcribe.py`, `voice_reply.py`, the mic, dictation, TTS | [stt-streaming](docs/system-specs/modules/stt-streaming.md) + [voice-streaming](docs/system-specs/modules/voice-streaming.md) |
| cron, learn, dashboard handlers | [learn-cron-dashboard](docs/system-specs/modules/learn-cron-dashboard.md) |
| Slack, Discord, any channel, messaging, approvals | [messaging](docs/system-specs/modules/messaging.md) + [slack-gateway](docs/system-specs/modules/slack-gateway.md) |
| subagents, spawn, orphan recovery | [subagent](docs/system-specs/modules/subagent.md) |
| crews, `select_crew`, crew bindings, Crew Mode slots | [crew-mode](docs/system-specs/modules/crew-mode.md) |
| the pipeline conductor agent or its skill | [pipeline-conductor](docs/system-specs/modules/pipeline-conductor.md) |
| task runner | [task](docs/system-specs/modules/task.md) + [taskrunner](docs/system-specs/modules/taskrunner.md) |
| `workflows/` (the dynamic-workflow engine) | [workflows](docs/system-specs/modules/workflows.md) |
| themes | [themes](docs/system-specs/modules/themes.md) + [theming-contract](website/docs/theming-contract.md) |
| anything under `website/` | [`website/AGENTS.md`](website/AGENTS.md) |
| user-facing strings, dates, numbers, sort order | [i18n-catalog](website/docs/i18n-catalog.md) (authoring) + [i18n-gates](docs/ci/i18n-gates.md) (CI) |
| tests: flakes, hangs, speed, memory, fixtures, sharding, side effects, host state (`~/.kiro`, `Path.home()`, the systemd user manager), conftest isolation, `monkeypatch.undo()`, env-var leaks, host-dependent tests (Windows, Python 3.13, per-user tools), what `TMPDIR` must not be | [testing-conventions](docs/system-specs/common/testing-conventions.md) + the [writing-tests](src/kiro_crew/builtin_skills/kirocrew-dev/writing-tests/SKILL.md) skill; frontend and Electron tests: [website/docs/testing.md](website/docs/testing.md) |
| browser E2E | [e2e-gate](docs/ci/e2e-gate.md) |
| proving a worktree change against an isolated running gateway | [worktree-verification-recipes](docs/guides/worktree-verification-recipes.md) |
| CI, PR flow, review gates, commit messages | [ci-and-reviews](docs/ci/ci-and-reviews.md) + [CONTRIBUTING.md](CONTRIBUTING.md) |
| constants, comments, lint, code style, the brand name | [code-style](docs/system-specs/common/code-style.md) |
| connections, connectors, an external account link | [connections](docs/system-specs/modules/connections.md) |
| a POSIX call: locks, signals, PIDs, chmod, RSS | [platform-compat](docs/system-specs/common/platform-compat.md) + [windows-install](docs/guides/windows-install.md) |
| injected `[Cron notification]` / `[Subagent completion event]` | [injected-messages](docs/system-specs/common/injected-messages.md) |
| build, install, dev mode | [CONTRIBUTING.md](CONTRIBUTING.md) + [install](docs/guides/install.md) |
| cutting a release | [release](docs/build/release.md) |
| `CHANGELOG.md` | [changelog](docs/build/changelog.md) |
| errors, retries, user-facing failure text | [error-handling](docs/system-specs/common/error-handling.md) |
| what this public fork must never re-introduce | [oss-fork-boundaries](docs/system-specs/oss-fork-boundaries.md) |
| any doc: moving, renaming, indexing it | [docs/README.md](docs/README.md) |

The whole doc tree is indexed from [`docs/README.md`](docs/README.md). User-facing
docs that ship in the package live in `src/kiro_crew/docs/` and are indexed by
[its README](src/kiro_crew/docs/README.md).

## Security invariants (do NOT weaken)

Detail and rationale: [security](docs/system-specs/modules/security.md),
[governance](docs/system-specs/modules/governance.md),
[computer-use](docs/system-specs/modules/computer-use.md).

- **Keystone.** `security_policy.json`, `profiles/`, `admission_policy.json` and
  `computer_use.json` under the data home are the ceiling the agent is governed by.
  **The enforcement point is the OS layer in `sandbox.py`, not a text matcher.** Every
  crew-home leaf carries one of three dispositions, and which one it has IS the
  statement of what is guaranteed: `HIDDEN` (bind-masked in every mode — the credential
  homes, `.env`, `live_target.json`), `READONLY` (in-sandbox code reads it and a write
  would let the agent choose its own ceiling — the four leaves above), or `VISIBLE`
  (in-sandbox code needs read *and* write, so no OS rule applies and it rests on the
  tool gate alone). Precisely, then: the agent **cannot write** its own ceiling in any
  sandbox mode, and it **can read** it, deliberately — masking a policy file makes it
  resolve to the permissive standalone default, so hiding a ceiling REMOVES it instead
  of protecting it. Do not restore a read block by pattern-matching command text: a
  spawned shell reaches a file through an `open()` that never routes through the tool
  gate, so a path fenced only there is readable in any sandbox mode whatever the matcher
  recognises, and each spelling closed (`/./`, a glued redirect, a variable, `cd`,
  `pushd`) narrows an unbounded set by exactly one. `test_sandbox_governance_mask.py`
  pins the union of the three dispositions equal to the crew-home half of
  `security.sensitive_home_dirs()`, so a new leaf cannot land in none of them — that
  pin, not a regex, is what keeps the ceiling un-disableable. One residual worth
  carrying: `sel_hmac.key` is `VISIBLE`, so the SEL audit key has no OS fence; closing
  that means moving its in-sandbox reader behind the gateway, never another matcher.
- **Governance is `POLICY ∩ PROFILE`, tightest-wins**, enforced at Kiro Crew's OWN
  PreToolUse gate even when the kiro agent config granted the call. The evaluator
  is scope-name-agnostic, so adding a scope is a `SCOPE_CATALOG` data change, never
  an evaluator edit.
- **`CONTRACT_VERSION` stays pinned at 1 pre-launch.**
- **Never restate the denied-rule count in prose.**
  `test/test_denied_commands_security.py` pins it, and a restated count goes stale
  silently.
- **A cron script body is never a shell-gate subject.** `is_sensitive_bash_command`
  and `is_denied` read a SHELL COMMAND LINE; `mcp_cron._vet_script_contents` scans a
  Python source body with whole-body, source-aware detectors only (credential path,
  secret env name, exfil URL) and the sandbox is the runtime control. Handing the
  body to the shell gate was tried (#4243 → #8811) and every shell-grammar pass
  produced a permanent false denial on ordinary scripts (#7912, #8563, #8643,
  #8812), each patched with another AST layer that still could not stop
  `open(a + b)`. Do not add a `subject_is_*` flag, a `_traversal_subjects`
  re-pointing, or an `is_sensitive_source_body` back. A new script detector is a
  whole-body match in `_vet_script_contents`, or a sandbox mask. Pinned by
  `test_the_shell_gate_has_no_source_body_entry_point` and
  `test_script_body_is_never_a_shell_gate_subject`.
- **A regex spelling-chase is a review smell, not a fix.** When a security review
  finds "X also reaches the fence via spelling Y", ask first whether the SUBJECT is
  wrong (a document handed to a command-line matcher) or whether the sandbox
  already covers it. Add a table entry only when the subject is genuinely a shell
  command line and the OS sandbox does not hold the path (#7441 went four rounds
  of `command`/`exec -a`/`nice`/`env -i`/`timeout`/`busybox` before restructuring).
- **Computer use is deliberately NOT governed**: it is one operator opt-in on the
  keystone `computer_use.json`. Never add `computer_use.*` scopes, capability rows,
  approval ordinals or pointer permits. Its refusals run **in band** on
  `tools._dispatch`, never at the fail-OPEN `hooks` gate, because a pre-authorized
  tool can skip that gate. `click_method: "auto"` must NEVER resolve onto
  `"global"`: that is the only thing between an ordinary click and the operator's
  real cursor.

## Never hardcode a model id

`claude-*`, `opus*`, `sonnet*`, `haiku*`, `gpt-*` or `fable*` as a default or
fallback fails at runtime for anyone not entitled to it, silently until the first
prompt. The default is `"auto"`; resolve a substitute choice through
`acp.client.resolve_usable_model`; pin a cheaper model only via
`agent.role_models.<role>`. `code-review.yml` fails on a newly added hardcoded
literal. Rules and the one exception:
[model-selection](docs/system-specs/common/model-selection.md).

## Harness parity

Never express "this is the Kiro harness" as the ABSENCE of another one. A negative
test fails toward the permissive answer, so nothing goes red until an operator who
never opted into that harness pays for it — and every id in
`acp_backends.BASELINE_SELECTABLE_BACKENDS` is selectable on a plain public build,
so `not is_claude_backend` is already wrong on the non-Claude ones. Identity is
positive: `is_kiro_backend`, `== ACP_BACKEND_KIRO`, or membership in a named
`ACP_BACKENDS_*` set.

<<<<<<< HEAD
### Custom LLM router wiring (fork)

The fork can drive any Anthropic-compatible router through the `claude_code`
backend instead of (or alongside) kiro-cli's `acp` provider:

- **Config:** `agent.provider = "claude_code"`, `agent.provider_base_url` (e.g.
  `http://127.0.0.1:8317`), `agent.model` = a router-served model id. The model
  id is the router's OWN namespace — it must never pass through
  `model_registry` translation (the Bedrock-form `global.anthropic.*` id would
  be rejected). On this path the model rides in via `ANTHROPIC_MODEL` env
  (`AcpClient._model_via_env`), not `session/set_model`.
- **Key:** `agent.provider_api_key`, or the environment. The fork-specific
  `CLIPROXY_API_KEY` env var is mapped into `ANTHROPIC_API_KEY` at the provider
  factory, so a local proxy needs no credential in `config.json`
  (`config/loader.py` `create_provider_factory`; precedence: config key >
  `ANTHROPIC_API_KEY` env > `CLIPROXY_API_KEY` env).
- **GUI picker catalog:** the router path advertises `GET {base_url}/v1/models`
  entries under their PREFIXED picker ids (see the table below), filtered
  through `AcpClient._ROUTER_MODEL_WHITELIST`; extend locally via
  `model_whitelist.json` under the config dir, merged by
  `AcpClient.router_model_whitelist()`. The picker namespace drops
  commandcode's vendor part: the raw `deepseek/deepseek-v4-pro` is shown as
  `cmc/deepseek-v4-pro`.
- **Prefix stripping (the wire contract):** CLIProxyAPI serves RAW unprefixed
  `/v1/models` ids and REJECTS prefixed spellings ("unknown provider"), so
  `strip_router_model_prefix()` is applied before anything goes upstream (the
  `ANTHROPIC_MODEL` env, the `settings.local.json` model pin, and the
  `_meta.claudeCode.options.model` seed). A known prefix is stripped; unknown
  or absent prefixes pass through unchanged.
  `AcpClient._ROUTER_RAW_MODEL_IDS` is the single source for both the whitelist
  and the translation; `_capture_router_models` resolves each catalog entry to
  its prefix via `owned_by` (`openai` = the Codex OAuth group).
- **CLIProxyAPI (localhost:8317):** Anthropic Messages at
  `http://127.0.0.1:8317/v1/messages`, catalog at `/v1/models`. The two
  `gpt-image-*` entries are image-generation only and stay out of the picker
  whitelist.

## Harness parity: Kiro is first-class, the rest are adapted
=======
An added harness ADAPTS to the seams the Kiro path already runs through; it never
moves, widens or generalizes them, and it is selected at `agent.acp_backend` —
`agent.provider` stays `enum=["acp"]`. Invariant ids (cite them bare, `H7`),
capability sets and the CI half:
[harness-parity](docs/system-specs/modules/harness-parity.md). Run the added-line
gate locally with
`HARNESS_BASE_REF=origin/main python3 scripts/check_harness_parity.py`.
>>>>>>> upstream/main

## Specs and docs

<<<<<<< HEAD
- **An added harness ADAPTS, it does not widen.** It may only fit itself to the
  seams the Kiro harness already runs through: no new conditional, required
  argument, awaited step, or failure mode on the Kiro path, and no collapsing a
  per-harness literal (spawn argv, `PROTOCOL_VERSION`, client capabilities) into
  one form every harness accepts. A harness that cannot land without changing the
  Kiro path does not land yet.
- **Identity is positive.** `is_kiro_backend` / `== ACP_BACKEND_KIRO`, or
  membership in a named `ACP_BACKENDS_*` set in `acp/types.py`. Never a bare
  string literal, an inequality, or a negation.
- **Capabilities are opt-in membership sets** (`ACP_BACKENDS_SESSION_SHARING`,
  `ACP_BACKENDS_STEER`, `ACP_BACKENDS_INTERNAL_SANDBOX`), and every harness's
  membership is an explicit decision. `is_kiro_cli` is the one that fails OPEN:
  it makes `sandbox.wrap_argv` SKIP Kiro Crew's own seatbelt in favour of the
  harness's internal sandbox, so granting it to a harness without one leaves the
  agent process unconfined.
- **Kiro is the floor.** `agent.acp_backend` defaults to `ACP_BACKEND_KIRO` and it
  is in `acp_backends.selectable_backends()` unconditionally (its baseline is
  `BASELINE_SELECTABLE_BACKENDS`); an unusable persisted value degrades there with a
  logged reason instead of raising. There is exactly one gate —
  `resolve_selected_backend`, called from `_normalize_acp_backend` inside config
  load — and it reads `selectable_backends()` per call, so registering a backend is
  what makes a persisted value survive. The Kiro construction path gains no second
  check (harness-parity H13). A harness is selected at `acp_backend` —
  `agent.provider` stays `enum=["acp"]`.
- **Registration is additive at the seam** — `platform/interfaces.py`'s
  `ProviderRegistry`, a v1 addition with no `CONTRACT_VERSION` bump. A new
  provider capability lands on the `LLMProvider` ABC with a safe default, never
  as a `hasattr` probe on the Kiro path.
- Invariant ids, and the test pinning each, are in
  [harness-parity](docs/system-specs/modules/harness-parity.md). Cite them bare
  (`H7`) in code comments and review findings.

`scripts/check_harness_parity.py` fails on a newly added negative identity test
under `src/kiro_crew/` (run it locally with
`HARNESS_BASE_REF=origin/main python3 scripts/check_harness_parity.py`); the
judgment half is the `harness-parity` rule in `AUTOSDE.yaml`.

### Prefix model ids (CLIProxyAPI picker)

| Prefix | Provider | Raw `/v1/models` ids (what the proxy receives) |
|---|---|---|
| `cmc/` | commandcode (`https://api.commandcode.ai/provider/v1`) | `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash`, `moonshotai/Kimi-K3`, `moonshotai/Kimi-K2.7-Code`, `moonshotai/Kimi-K2.7-Code-Highspeed`, `moonshotai/Kimi-K2.6`, `moonshotai/Kimi-K2.5`, `zai-org/GLM-5.2`, `zai-org/GLM-5.2-Fast`, `zai-org/GLM-5.1`, `zai-org/GLM-5`, `MiniMaxAI/MiniMax-M3`, `MiniMaxAI/MiniMax-M2.7`, `MiniMaxAI/MiniMax-M2.5`, `xiaomi/mimo-v2.5-pro`, `xiaomi/mimo-v2.5`, `Qwen/Qwen3.8-Max`, `Qwen/Qwen3.7-Max`, `Qwen/Qwen3.7-Plus`, `Qwen/Qwen3.7-Flash`, `Qwen/Qwen3.6-Max-Preview`, `Qwen/Qwen3.6-Plus`, `stepfun/Step-3.7-Flash`, `stepfun/Step-3.5-Flash`, `tencent/hy3-paid`, `nvidia/nemotron-3-ultra-550b-a55b`, `thinkingmachines/inkling`, `thinkingmachines/inkling-small`, `poolside/laguna-s-2.1-free`, `meta/muse-spark-1.2`, `xai/grok-4.5`, `gpt-5.6-luna` |
| `oc/` | opencode-go (`https://opencode.ai/zen/go/v1`) | `deepseek-v4-flash`, `mimo-v2.5` |
| `ol/` | ollama-cloud (`https://ollama.com/v1`) | `deepseek-v4-flash:0731` only — the plain and kimi/glm entries are deliberately NOT exposed |
| `cx/` | codex (Codex OAuth; catalog `owned_by` `openai`) | `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.6-sol`, `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `codex-auto-review` — `gpt-5.3-codex-spark` is NOT listed (400 upstream) |
| `ag/` | antigravity (3 OAuth accounts, round-robin) | `gemini-3-flash`, `gemini-3-flash-agent`, `gemini-3.5-flash-extra-low`, `gemini-3.1-pro-low`, `gemini-3.6-flash-high`, `gemini-pro-agent`, `gemini-3.1-flash-lite`, `gemini-3.1-flash-image`, `gemini-3.5-flash-low`, `claude-opus-4-6-thinking`, `claude-sonnet-4-6`, `gpt-oss-120b-medium` |

## Specification management

- MUST read the relevant spec under `docs/system-specs/modules/` before changing
  the code it covers.
- MUST update the spec in the SAME commit when an API, schema, or documented
  behavior changes.
- MUST add the doc to its directory `README.md` when creating one, and MUST update
  every index that points at a doc you move, rename, or delete. `scripts/docs-lint.sh`
  enforces this; run it before you commit a docs change.
=======
- MUST read the owning spec under `docs/system-specs/` before changing the code it
  covers, and MUST update it in the SAME commit.
>>>>>>> upstream/main
- MUST NOT create additional markdown files unless explicitly instructed.
- Everything else about adding, moving, indexing and linting a doc — including
  `scripts/docs-lint.sh` — is [docs/README.md](docs/README.md). Treat
  `docs/task-specs/` as an archive, never as current context.

## Git

- Do NOT proactively `git commit`. Commit only when asked.
- Do NOT `git push` unless the user explicitly says to push. Being asked to commit
  is NOT permission to push.
- `main` is the default branch; changes land through a GitHub PR. The full flow:
  [CONTRIBUTING.md](CONTRIBUTING.md).

```
<type>: <summary — max 72 chars, imperative, lowercase, no period>

<body — what and why, not how; wrapped at 72>
```

Types the PR-title gate in `code-review.yml` accepts: `feat`, `fix`, `docs`,
`style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`. **One
logical change per commit**, and at most two commits per PR.

## CHANGELOG.md

- **Your feature PR does not touch `CHANGELOG.md`.** The release PR writes the
  section covering everything that shipped.
- **Never delete or edit a shipped section.** A release PR prepends one section and
  leaves every earlier one byte-identical. This has already cost 322 lines of
  released history once, which no test caught.
- **A stable release must never ship a version carrying a prerelease suffix.**

When, how, the heading shape and the format budget:
[changelog](docs/build/changelog.md). Cutting a release, and the one escape hatch
from the suffix rule: [release](docs/build/release.md).

## The gate before you commit

```bash
python3 scripts/check_black_formatting.py && python3 scripts/check_subprocess_encoding.py && isort src/kiro_crew test
flake8 src/kiro_crew test && mypy src/kiro_crew
python -m pytest
```

- **On macOS, run `mypy --platform linux src/kiro_crew`.** Without it a local run
  reports errors you did not cause and MISSES the Linux-only errors CI fails on, so
  a clean local run is a false green.
- **Never run bare `black src/kiro_crew test`.** It reformats every baselined file
  and buries your diff. Format only what you touched:
  `black --target-version py310 <the files you changed>`.
- Frontend: `cd website && npm run build && npm run test`.
- A multi-test `--override-ini` MUST keep `-n auto --dist loadgroup
  --max-worker-restart=2`; a bare override silently drops `--dist loadgroup` and
  scatters `@pytest.mark.xdist_group` tests into flaky races.

Gates, the six flake classes, the conftest isolation floor and the traps that are
invisible when reading a test: [code-style](docs/system-specs/common/code-style.md) +
[testing-conventions](docs/system-specs/common/testing-conventions.md). A test that
can block forever is a lost RUN, not a failed test: on Windows pytest-timeout kills
the xdist worker, and with `--max-worker-restart=0` one unbounded `await` aborts the
whole job (class 6). Frontend and Electron: [website/docs/testing.md](website/docs/testing.md).

## Cross-platform

<<<<<<< HEAD
Gates you will trip:

| Gate | Rule |
|---|---|
| flake8 F401 | no unused imports |
| flake8 N806 | function-local variables are lowercase (`mock_client`, not `MockClient`) |
| flake8 W504 | line break BEFORE a binary operator |
| mypy | annotate empty collections (`output: list[str] = []`) |
| pytest | `asyncio: mode=strict`, so every async test needs `@pytest.mark.asyncio` |

Never fix a flake with a rerun, a longer `sleep`, or a weakened assertion. Read
[testing-conventions](docs/system-specs/common/testing-conventions.md) § Determinism
for the five flake classes and the one correct fix for each. In particular, a timing
test that asserts algorithmic **complexity** must assert the shape, not a duration —
deterministically where the code has structure to observe (pin the linear path, require
an identical invocation trace when the input doubles), and by a generously-bounded
doubling ratio only where it does not: absolute ceilings split by Python version (CI
enables coverage on 3.12 only), and tight timed ratios false-red on shared runners.

**A test must not touch the operator's machine, and the floor you stand on is not the
same in every testpath.** `testpaths` collects two trees, and only `test/` gets
`test/conftest.py`; the ~108 test modules under `src/kiro_crew/apps/builtins/*/tests/`
see the **rootdir** `conftest.py`, plus that app's own `tests/conftest.py` where one
exists (three of the eight apps ship one). So the rootdir conftest carries the
host floor: `KIROCREW_HOME` pinned per test, the import-time `~/.kiro` bindings pinned
(that directory is kiro-cli's own home, shared with the real installed agent, and a
separate isolation axis from the data home), the SEL default dir pinned session-wide,
`tempfile`'s base redirected with residue reported, and the checkout failed on residue.
Before adding isolation, decide which floor it belongs to; before writing a test, read
the [writing-tests skill](src/kiro_crew/builtin_skills/kirocrew-dev/writing-tests/SKILL.md).
Two traps are worth naming here because neither is visible when reading the test:

- **A child process inherits pytest's CWD, the repo root**, so a spawn that may create a
  file needs `cwd=` under `tmp_path` — and the assertion must be scoped to where that
  child actually ran, not to where you hoped it wrote.
- **A singleton with a daemon thread beats every filesystem cleanup.** It captures the
  directory the first caller resolved and re-creates it after a test's own teardown
  deleted it, so the fix is a session-scoped directory owned by no test, never tidier
  cleanup.
- **A stub is not a stop: SPY on a `shutdown`/`close`/`stop` and delegate.** A stub that
  only records leaves the thing running for the whole worker. Replacing the metrics
  provider's `shutdown` left an OpenTelemetry exporter thread alive, and because that SDK
  reinstalls it in every fork child via `os.register_at_fork`, the sandbox probe's child
  became multithreaded — `unshare(CLONE_NEWUSER)` implies `CLONE_THREAD` and fails EINVAL
  there, which was cached as "this host has no sandbox backend" and failed every later
  sandboxed spawn closed. 19 red tests, none of them a metrics test.

## Code style

| Rule | Requirement |
|---|---|
| Line length | 100 chars (black configured) |
| Python version | ≥ 3.10 (`from __future__ import annotations` for type hints) |
| Imports | `import logging` + `logger = logging.getLogger(__name__)` |
| Async | `asyncio` throughout; `async def` for all I/O |
| Dataclasses | `@dataclass` for data containers |
| Constants | No hardcoded strings or values in business logic; every limit has an owning module. Index: [code-style](docs/system-specs/common/code-style.md) |
| Comments | Explain **behavior and rationale (the why)**: invariants, edge cases, units, non-obvious constraints. NOT a task log: no PR/CR numbers, review-round markers, incident dates, milestone tags, or commit SHAs. No "previously/used to/we now" narration, state current behavior in present tense. Don't restate what the code plainly does. `_vendor/` and pragmas are exempt. |
| Icons | **Never use emojis in the UI.** Use `lucide-react` with `className="lucide-inline"`. |
| Product name | The product is **Kiro Crew**: two words, a space, capital `K`. Identifiers keep the spelling their own system gave them (the `kirodotdev/KiroCrew` repo slug, `KiroCrew.dmg` artifacts, the `KiroCrew Nightly` OS identifier, the `kirocrew` CLI, `KIROCREW_*` env vars, `kiro_crew` imports). CI-gates the lines a change adds; run `BRAND_BASE_REF=origin/main python3 scripts/check_brand_name.py` before pushing. |
| User-facing strings | The dashboard is translated into 11 languages. **Never hardcode a user-facing English string, and never format a date, number, or sort order without naming a locale.** Both are CI-gated. Backend-owned strings have no catalog path yet, so a new non-2xx JSON body MUST carry a machine-readable `code` field. |

## Cross-platform: route POSIX calls through `platform_compat`

Kiro Crew runs on macOS, Linux (x86_64 and ARM), and Windows (native). `fcntl`,
`termios`, `resource`, and `pty` do not exist on Windows, and
**`os.kill(pid, 0)` TERMINATES the target there**: it is not a liveness probe.

| Need | Use (`platform_compat`) | NOT |
|------|--------------------------|-----|
| File lock | `file_lock(fd, exclusive=)` / `acquire_lock`+`release_lock` / `try_acquire_lock` | `fcntl.flock` |
| Liveness probe | `pid_exists(pid)` / `pid_liveness(pid)` | `os.kill(pid, 0)` (kills on Windows!) |
| Kill a process | `kill_pid(pid, sig)` | `os.kill(pid, sig)` |
| Kill a tree | `kill_process_tree(pid, sig)` | `os.killpg(os.getpgid(pid), sig)` |
| Parent PID | `get_ppid(pid)` | `/proc` read / libproc |
| Match process cmdline | `process_matches(pid, needles)` | `/proc/<pid>/cmdline` / `ps` |
| Process start time (PID-reuse guard) | `process_start_time(pid)` | `/proc/<pid>/stat` / `ps -o lstart=` (both answer `None` on Windows, so the guard silently never confirms) |
| Signals | `platform_compat.SIGKILL` / `SIGTERM` | `signal.SIGKILL` (undefined on Windows) |
| Spawn isolation | `start_new_session=IS_POSIX` + `creationflags=CREATE_NEW_PROCESS_GROUP` | bare `start_new_session=True` |
| Re-exec the current Python module | `reexec_python_module(module, args)` | `os.execv(sys.executable, [sys.executable, ...])` (breaks when the Windows interpreter path contains spaces) |
| Race-free Job object assignment | `creationflags \|= CREATE_SUSPENDED`, then `apply_job_limits`, then `resume_process_main_thread` | assigning a job to an already-running child (descendants it already spawned escape) |
| Fork-bomb / memory ceiling on a spawned tree | `sandbox.apply_windows_resource_ceiling(pid)` after the spawn, alongside `cgroup_scope_argv` | `cgroup_scope_argv` alone (a no-op on Windows, so no ceiling at all) |
| File mode | `chmod_safe(path, mode)` / `fchmod_safe(fd, mode)` | `os.chmod` / `os.fchmod` (no `os.fchmod` on Windows) |
| Owner-only secret (fail-loud) | `restrict_to_owner(path)` | `os.chmod(path, 0o600)` under `if IS_POSIX` (silent no-op leaves secrets world-readable) |
| Owner-only secret directory (fail-loud, inheritable) | `restrict_dir_to_owner(path)`; `make_owner_only_dir(path)` to also create it (its tighten step is best-effort) | `restrict_to_owner(path)` on a directory (its Windows grants carry no `(OI)(CI)`, so files created inside land on the default DACL, not owner-only; its `0o600` also drops the execute bit a directory needs) |
| Directory link | `symlink_or_junction(target, link)` | `os.symlink` (`WinError 1314` without elevation) |
| Detect/remove a dir link | `is_link_or_junction(path)` / `unlink_link_or_junction(path)` | `path.is_symlink()` (misses a Windows junction) |
| Process RSS (live) / peak RSS / CPU | `proc_rss_bytes()` / `proc_peak_rss_bytes()` / `proc_cpu_seconds()` | `resource.getrusage` (`ru_maxrss` is a high-water mark, never a live reading, and its unit is KiB on Linux but bytes on macOS) |
| Available host memory | `host_available_mib()` (0 = unknown, never 0 = no memory) | `/proc/meminfo` directly (Linux-only, so the bound built on it silently vanishes on macOS and Windows) |
| FD soft limit | `raise_nofile_soft_limit(n)` | `resource.setrlimit` |
| Port to PID | `find_listening_pids(port)` / `listening_pid_tool_available()`; `find_port_listeners(port)` when ownership must be scoped to the local address actually probed | `lsof` directly |
| Spawn a system tool (`ps`, `lsof`, `netstat`, `taskkill`) | `trusted_system_bin(name)`, treating `None` as "unavailable" | a bare argv name (resolved through a `PATH` that can lead with same-uid-writable dirs) |
| strftime no-pad | `strftime(dt, "%-I")` | bare `dt.strftime("%-I")` (`ValueError` on Windows) |

Verify process, signal, file-lock, and metrics changes on macOS + Linux. Frontend:
Chrome, Firefox, Safari, Edge, using standard Web APIs and guarding the rest.
Windows specifics: [windows-install](docs/guides/windows-install.md).
=======
Route POSIX calls through `platform_compat`: `fcntl`, `termios`, `resource` and
`pty` do not exist on Windows, and **`os.kill(pid, 0)` TERMINATES the target
there** — it is not a liveness probe. The full helper-per-call table:
[platform-compat](docs/system-specs/common/platform-compat.md). Verify process,
signal, file-lock and metrics changes on macOS + Linux.
>>>>>>> upstream/main

## LLM-facing capabilities

A new LLM-facing CLI command MUST also ship as an MCP tool, MCP tools MUST be
stateless (no module global holds per-caller data), and a skill any shipped
feature, tool or doc references MUST live in `src/kiro_crew/builtin_skills/` — the
only tree bundled into the package. Why, plus the session-key gate:
[mcp](docs/architecture/mcp.md) +
[memory-skills-hooks](docs/system-specs/modules/memory-skills-hooks.md).

## Injected messages are not the user

`[Cron notification from "job"]`, `[Subagent completion event]` and
`[auto-nudge cycle N]` arrive from automation. Process them; do NOT answer them as
if a human typed them — the user may not be present. Envelopes:
[injected-messages](docs/system-specs/common/injected-messages.md).

## Harness safety

`kirocrew gateway --approval yolo` auto-approves ALL tools and refuses to start
unless `KIROCREW_HOME` is explicitly set to a non-default path. Never point it at
`~/.kiro/crew`. All harness flags: [cli](docs/system-specs/modules/cli.md).
