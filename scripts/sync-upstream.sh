#!/usr/bin/env bash
# sync-upstream.sh — pull kirodotdev/KiroCrew main into this fork, safely.
#
# The fork exists for one reason: the claude_code / opencode ACP seam that lets
# RoyCrew run against a self-hosted router (9router, CLIProxyAPI) instead of
# Kiro's Bedrock catalog. Upstream keeps refactoring around that seam, so every
# sync ends by running the seam's own tests — a green run is the proof the merge
# did not quietly revert the fork.
#
# git rerere is enabled here: resolve a conflict once and git replays the same
# resolution automatically the next time upstream touches that hunk.
#
# usage:  scripts/sync-upstream.sh          # fetch + merge + verify
#         scripts/sync-upstream.sh verify   # just re-run the seam tests
set -euo pipefail
cd "$(dirname "$0")/.."

UPSTREAM_URL="https://github.com/kirodotdev/KiroCrew.git"

# ponytail: the seam's guard is the fork's existing tests, not a new suite.
SEAM_TESTS=(
  test/test_acp_provider.py        # claude/opencode are selectable ACP backends
  test/test_acp_opencode.py        # opencode wire format + no silent model swap
  test/test_acp_backend_kas.py     # 4-way backend invariants stay 4-way
  test/test_router_model_prefix.py # cmc/ oc/ cx/ ol/ ag/ prefix stripping
  test/test_provider_test_endpoint.py  # /api/provider/test + stored-key guard
  test/test_cc_models_endpoint.py  # router catalog reaches the model picker
  test/test_config_patch.py        # agent.acp_backend accepts claude/opencode
)

PYTEST=.venv/bin/pytest
[ -x "$PYTEST" ] || PYTEST=pytest

verify() {
  echo "==> verifying the claude_code/9router seam survived"
  "$PYTEST" "${SEAM_TESTS[@]}" -q
  echo "==> seam OK"
}

if [ "${1:-}" = "verify" ]; then verify; exit; fi

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "$UPSTREAM_URL"
git config rerere.enabled true
git config rerere.autoupdate true

if [ -n "$(git status --porcelain)" ]; then
  echo "working tree is dirty — commit or stash first" >&2
  exit 1
fi

git fetch upstream main
BEHIND="$(git rev-list --count HEAD..upstream/main)"
if [ "$BEHIND" -eq 0 ]; then echo "already up to date with upstream"; exit 0; fi
echo "==> $BEHIND new upstream commit(s)"

if ! git merge upstream/main --no-edit; then
  echo
  echo "CONFLICTS — resolve keeping BOTH sides:" >&2
  git diff --name-only --diff-filter=U | sed 's/^/  /' >&2
  cat >&2 <<'RULES'

  Rules (the fork dies if these are resolved upstream's way):
   - agent.acp_backend must keep "claude" and "opencode" in its enum;
     agent.provider stays locked to "acp" (upstream's harness-parity contract).
   - Keep upstream's new/renamed APIs, then re-apply the fork's claude/opencode
     branches on top of them. Never take a whole file with `--ours`.
   - Router prefix stripping (cmc/ oc/ cx/ ol/ ag/) and the /api/provider/*
     routes are fork-only: upstream deleting them is not a conflict to accept.
   - website/electron/auto-update.js is fork-OWNED, the one file to take whole
     with `--ours`: upstream's updater fetches Kiro's CDN feed
     (updates.crew.kiro.dev) across nightly/insider/stable channels, which would
     push the upstream app over RoyCrew. The fork reads its own GitHub releases
     instead, so upstream's updater/channel tests do not apply here.

  Then: git add -A && git commit && scripts/sync-upstream.sh verify
RULES
  exit 1
fi

verify
