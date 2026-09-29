/**
 * The dashboard's API client: the `api` singleton and the transport under it.
 *
 * This module owns the transport and its auth recovery: the `X-Session-Key`
 * default, the request helpers, the `j`/`jNullable` parsers that journal every
 * failure as an `ApiError`, the 403 `X-Auth-Required` silent refresh, the
 * embedded-pane hand-off, the re-auth banner and the stale-owner prompt. It
 * installs those helpers as the blessed `apiTransport` at load.
 *
 * The endpoints themselves live by domain under `./client/`, one module per
 * product area, each a `create*Endpoints` factory handed that transport. `api`
 * is assembled here from their segments, spread in the order the methods have
 * always had, so it stays one plain object: `vi.spyOn(api, name)` and the
 * `{ ...mod.api, name: vi.fn() }` mock factories keep working. The wire types
 * those modules own are re-exported below, so every import path is unchanged.
 */
import { installSessionExpiryHandler } from './sessionExpirySignal'
import { ApiError, friendlyErrText, toApiError } from './apiError'
import { refreshOnce, __resetRefreshOnceForTests } from './refreshOnce'
import {
  STALE_OWNER_SESSION_CODE,
  installStaleOwnerHandler,
  noteStaleOwnerResponse,
} from './staleOwnerSignal'
import { edgeChallengeMessage, noteEdgeAuthChallenge } from './edgeAuthChallenge'
import { beginArtifactWrite, endArtifactWrite } from '../lib/artifactWrites'
import { installApiTransport } from './apiTransport'
import { queryClient, invalidateAcrossQueryClients } from './queryClient'
import { recordError, parseErrorCode, requestPath } from '../utils/errorReport'
import { i18nT } from '../i18n/t'
import type { ClientTransport } from './client/transport'
import { createSystemEndpoints } from './client/system'
import { createTelemetryEndpoints } from './client/telemetry'
import { createChatEndpoints } from './client/chat'
import { createOnboardingEndpoints } from './client/onboarding'
import { createSecurityEndpoints } from './client/security'
import { createRemoteAccessEndpoints } from './client/remoteAccess'
import { createFeatureDiscoveryEndpoints } from './client/featureDiscovery'
import { createThemesEndpoints } from './client/themes'
import { createInstancesEndpoints } from './client/instances'
import { createCloudEndpoints } from './client/cloud'
import { createMemoryEndpoints } from './client/memory'
import { createSessionsEndpoints } from './client/sessions'
import { createMcpEndpoints } from './client/mcp'
import { createAgentsEndpoints } from './client/agents'
import { createChatSlotSettingsEndpoints } from './client/chatSlotSettings'
import { createFilesEndpoints } from './client/files'
import { createCronEndpoints } from './client/cron'
import { createHooksEndpoints } from './client/hooks'
import { createSkillsEndpoints } from './client/skills'
import { createSteeringEndpoints } from './client/steering'
import { createConnectionsEndpoints } from './client/connections'
import { createConfigEndpoints } from './client/config'
import { createCapabilityManagerEndpoints } from './client/capabilityManager'
import { createVoiceEndpoints } from './client/voice'
import { createSourceControlEndpoints } from './client/sourceControl'
import { createMonitorsEndpoints } from './client/monitors'
import { createChatOrganizationEndpoints } from './client/chatOrganization'
import { createNotificationsEndpoints } from './client/notifications'
import { createSubagentsEndpoints } from './client/subagents'
import { createApprovalsEndpoints } from './client/approvals'
import { createTaskRunnerEndpoints } from './client/taskRunner'
import { createWorkflowsEndpoints } from './client/workflows'
import { createUpdatesEndpoints } from './client/updates'
import { createAgentChannelsEndpoints } from './client/agentChannels'
import { createAppsEndpoints } from './client/apps'
import { createArtifactsEndpoints } from './client/artifacts'
import { createBrowserAndComputerUseEndpoints } from './client/browserAndComputerUse'
import { createDecisionsEndpoints } from './client/decisions'
import { createMessagingEndpoints } from './client/messaging'
import { createAutoResearchEndpoints } from './client/autoResearch'
import type { DecisionsConsentData } from './client/decisions'

export type { TunnelStatus } from './client/system'
export type { WakaTimeStatsEntry, WakaTimeStats } from './client/telemetry'
export type {
  KiroPrerequisiteStatus,
  KasLoginStatus,
  KasLoginDeviceSession,
  KasLoginPollResult,
  KasLoginLoopbackSession,
  AgentImportCategory,
  AgentImportSource,
  AgentImportSkipped,
  AgentImportScanResponse,
  AgentImportSelection,
  AgentImportConflictStrategy,
  AgentImportApplyRequest,
  AgentImportSummary,
  AgentImportApplyResponse,
} from './client/onboarding'
export type {
  DeniedCommandRule,
  DeniedUserRule,
  AwsConsentStatus,
  FileDeliveryGrant,
  FileDeliveryConsentStatus,
  CredentialRedactionState,
  ArmedFileDeliveryConsent,
  DeniedCommandsData,
  GovernanceScopeDetail,
  GovernanceScope,
  GovernanceDistributionData,
  GovernancePolicyData,
  PostureItem,
  PostureControl,
  SecurityPostureData,
  TrustedAppsData,
  TrustedAppsRevokeResult,
  ManagedSecret,
  SecretsListResponse,
} from './client/security'
export type {
  TailnetStatusData,
  TailnetMobileStep,
  TailnetMobileData,
  TailnetMobileMutation,
  MobileConnectMethodsData,
  TailnetMobileConfigure,
  TailnetMobileQr,
} from './client/remoteAccess'
export type {
  SuggestionKind,
  SuggestionItem,
  FeatureVideo,
  FeatureVideoNext,
  FeatureVideoProbe,
  FeatureVideoStatus,
} from './client/featureDiscovery'
export type {
  InstanceTunnelStatus,
  SsoStatus,
  InstanceView,
  AddInstanceBody,
} from './client/instances'
export { filenameFromDisposition } from './client/instances'
export type {
  CloudCoords,
  CloudPreflight,
  RemoteProvisioner,
  LaunchJobStatus,
  LaunchStepState,
  LaunchStep,
  CloudLaunchSignin,
  KiroLoginTarget,
  CloudIdentity,
  LaunchJob,
  LaunchTaskSighting,
  LaunchTaskReport,
} from './client/cloud'
export type { MemoryCarveQuery, MemoryCarveResult } from './client/memory'
export { SEARCH_MIN_CHARS } from './client/sessions'
export type {
  McpShareReason,
  McpShareRecommendation,
  McpMeasureProgress,
  McpManagedServer,
} from './client/mcp'
export type {
  MemberRosterRow,
  MemberActivityEntry,
  CrewTeam,
  CrewPanelData,
  CrewPanelMeta,
} from './client/agents'
export { SLASH_COMMANDS_TIMEOUT_MS } from './client/chatSlotSettings'
export type {
  WebhookFreshness,
  WebhookOutcome,
  WebhookTokenEntry,
  WebhookContextEntry,
  WebhookRunRecord,
  WebhooksView,
  WebhookTokenCreated,
  WebhookTestResult,
} from './client/hooks'
export type { SkillScriptValidation } from './client/skills'
export { SKILLS_TIMEOUT_MS } from './client/skills'
export type {
  ConnectionMintState,
  ConnectionStatus,
  ConnectionOAuthClientSource,
  ConnectionOAuthClient,
  ConnectionOAuthClientSave,
  ConnectionTestResult,
} from './client/connections'
export type { AcpBackendInstalled, AcpBackendProbe } from './client/config'
export type { MonitorWrite, MonitorResponse } from './client/monitors'
export type {
  ChannelFolderBackfillMoved,
  ChannelFolderBackfillReport,
} from './client/chatOrganization'
export type { PlanStepInput } from './client/taskRunner'
export type {
  WorkflowLineage,
  WorkflowDefinitionRevision,
  WorkflowDefinition,
  WorkflowDefinitionWrite,
} from './client/workflows'
export type {
  InstallStreamResult,
  ExternalRegistryRow,
  FileMenuSurface,
  FileMenuContext,
} from './client/apps'
export type { AppPublishProvider } from './client/artifacts'
export type {
  BrowserInstallData,
  BrowserViewData,
  BrowserOpenData,
  ComputerUsePermissions,
  ComputerUseConfigData,
  ComputerUseConfigSave,
} from './client/browserAndComputerUse'
export type {
  DecisionsConsentData,
  DecisionPointData,
  DecisionFeedbackSide,
  DecisionVerdictValue,
} from './client/decisions'
export type {
  SlackConfigData,
  SlackConfigSave,
  DiscordConfigData,
  TelegramConfigData,
  DiscordConfigSave,
  TelegramConfigSave,
  WeComConfigData,
  WeComConfigSave,
  FeishuConfigData,
  FeishuConfigSave,
  WebexConfigData,
  WebexConfigSave,
  IMessageConfigData,
  IMessageConfigSave,
  TeamsConfigData,
  WeixinConfigData,
  TeamsConfigSave,
  WeixinConfigSave,
  WhatsAppGroup,
  WhatsAppConfigData,
  WhatsAppConfigSave,
} from './client/messaging'

let _sessionExpiredShown = false

/**
 * True while the banner on screen is the stale-owner variant. A separate latch
 * because that session is still AUTHENTICATED: ordinary polls keep succeeding,
 * so the `j` wrapper's clear-banner-on-2xx self-dismissal would remove the one
 * instruction that recovers the owner-gated surfaces. It clears via the
 * banner's own X or a successful in-banner token exchange, never via a 2xx.
 */
let _staleOwnerBanner = false

/**
 * Synchronous getter so React components can read the auth-banner state on
 * mount (e.g. when the banner was already injected before the component
 * subscribed to the `mc-auth-required` / `mc-auth-cleared` events).
 */
export function isAuthBannerShown(): boolean {
  return _sessionExpiredShown
}

/**
 * Internal: fire a window-level CustomEvent so React components can react
 * to auth-banner state transitions. The banner itself is a vanilla DOM
 * element managed by this module; the events let consumers (e.g.
 * `ChatPage`) suppress redundant offline UI when auth is the real blocker.
 *
 * Two events, and the difference is load-bearing. `mc-auth-cleared` means
 * only THE BANNER IS GONE, which includes the reader dismissing it with its
 * X while the session is still broken. `mc-auth-recovered` means
 * AUTHENTICATION WORKS AGAIN, and is emitted from `removeAuthBanner` alone --
 * every one of whose callers is gated on a 2xx or on an accepted token
 * exchange. A consumer that acts on recovery (dropping a stale auth failure)
 * must read the second; a consumer that only mirrors banner presence reads
 * the first.
 */
function _emitAuthEvent(
  kind: 'mc-auth-required' | 'mc-auth-cleared' | 'mc-auth-recovered',
): void {
  if (typeof window === 'undefined') return
  try { window.dispatchEvent(new CustomEvent(kind)) } catch { /* ignore */ }
}

/**
 * Clear the session-expired banner if it is currently shown.
 * Called automatically from the `j` response wrapper on any 2xx response so
 * the banner self-dismisses once auth is restored (e.g. via a successful poll
 * after gateway restart wiped the session table). The in-banner token paste
 * calls it directly once its exchange succeeds, since that path deliberately
 * issues no request whose 2xx would reach `j`.
 *
 * Idempotent: safe to call on every response.
 */
export function removeAuthBanner(): void {
  // A 2xx means auth works again — clear the terminal-refresh latch so a later
  // lapse retries silently instead of going straight to the banner.
  _silentRefreshExhausted = false
  // The stale-owner banner is exempt from the 2xx self-dismissal: that session
  // still authenticates for everything the owner gate does not front, so a
  // success proves nothing about the stale-subject denial.
  if (_staleOwnerBanner) return
  // Auth works again, so a LATER lapse in this same document deserves its own
  // hand-off. Deliberately after the stale-owner return above: that denial is not
  // disproved by an unrelated success, and re-asking the hub for it loops forever.
  _embeddedHandoffPosted = false
  if (!_sessionExpiredShown) return
  _sessionExpiredShown = false
  const el = document.getElementById('mc-session-expired')
  if (el) el.remove()
  _emitAuthEvent('mc-auth-cleared')
  // Reaching here means a caller proved auth works: every call site is behind a
  // 2xx or an accepted token exchange. The banner's own X does NOT come through
  // here -- it tears the banner down inline -- so this event, unlike
  // `mc-auth-cleared`, is never fired by a reader simply dismissing the notice.
  _emitAuthEvent('mc-auth-recovered')
}

// Reactive warm-path recovery: background-poll 403s funnel here, through the
// shared single-flight refreshOnce(). True if the 30-day cookie rotated.
let _silentRefreshExhausted = false
// One hub hand-off per pane DOCUMENT. Without this every 403 from every
// background poll posts another `mc-auth-expired`, and the hub answers each one
// with an SSH token mint (rate-limited, never stopped) — a mint storm behind a
// loading spinner. A hub re-mint reloads this iframe, which resets this latch,
// so a pane that can recover still gets a fresh ask on every load.
let _embeddedHandoffPosted = false

/** Hand auth recovery to the hub, at most once per pane document.
 *
 * The wildcard target is deliberate and matches the two call sites' comments:
 * the hub's origin is not knowable from inside the pane (tunnel hosts vary), and
 * the message carries only a fixed type string — no secret — while the parent
 * validates `event.origin` before acting on it (see resolveTunnelOrigin).
 */
function postAuthExpiredToHub(): boolean {
  if (_embeddedHandoffPosted) return true
  try {
    // nosemgrep: javascript.browser.security.wildcard-postmessage-configuration.wildcard-postmessage-configuration
    window.parent.postMessage({ type: 'mc-auth-expired' }, '*')
  } catch {
    return false // cross-origin parent unreachable — caller falls back to the banner
  }
  _embeddedHandoffPosted = true
  return true
}

export function attemptSilentRefresh(): Promise<boolean> {
  return refreshOnce().then((res) => {
    if (res.ok) {
      // Keep the scheduler's ['auth-me'] cache from holding a stale
      // pre-rotation session_exp after a warm-path recovery.
      void queryClient.invalidateQueries({ queryKey: ['auth-me'] })
      return true
    }
    // 401 = terminal (chain revoked / no cookie) → latch to banner; 5xx is transient.
    if (res.status === 401) _silentRefreshExhausted = true
    return false
  })
}

/** Test-only: reset module auth-recovery state between cases. */
export function __resetAuthRecoveryStateForTests(): void {
  _silentRefreshExhausted = false
  _embeddedHandoffPosted = false
  _sessionExpiredShown = false
  _staleOwnerBanner = false
  __resetRefreshOnceForTests()
  if (typeof document !== 'undefined') {
    document.getElementById('mc-session-expired')?.remove()
  }
}

/**
 * Exchange a pasted token for a session cookie WITHOUT leaving the page.
 *
 * The auth middleware reads `?token=` AHEAD of the session cookie on every path,
 * and because such a token did not arrive from the cookie it writes the session
 * cookie onto that response once the handler returns (`dashboard/token_auth.py`,
 * the `if not from_cookie` branch). `GET /api/auth/me` is deliberately kept off
 * the bypass list so it runs the full auth path. One credentialed request on that
 * endpoint therefore establishes the session in place.
 *
 * This used to be `window.location.href = ...?token=...`, which authenticated by
 * exactly the same mechanism and threw away every piece of in-memory state on the
 * way. Whatever the user had typed into the panel that prompted the re-auth went
 * with it -- for Settings -> Secrets that was a credential they had already
 * pasted, which is the loss this replaces (#12240).
 *
 * Answers false for any non-2xx and for a transport failure, including the 404 an
 * older gateway gives for this endpoint. The caller keeps the banner up on false,
 * so a server that cannot exchange in place leaves the user exactly where they
 * were rather than half-signed-in.
 */
/**
 * What one in-banner exchange established.
 *
 * `reached` is false only when the request never got an answer -- an unreachable
 * gateway, a dropped connection. It is separate from `ok` because the two need
 * different words: a refused token asks the user to paste a better one, while an
 * unreachable gateway makes "not accepted" an assertion about a check that never
 * ran.
 *
 * `ok` means some credential is live: enough to drop a plain-expiry banner,
 * which was raised because nothing was. `tokenAccepted` is the gateway's answer
 * to the narrower question -- is the token in THIS request what authenticated it
 * -- and `ownerOk` to whether that caller also clears the owner gate. A token
 * minted before the owner was configured is valid, so it can be accepted and
 * still denied; resolving an owner denial needs both. A gateway that predates
 * either field leaves it false, which keeps the prompt up rather than dismissing
 * one it cannot vouch for.
 */
type PasteExchange = {
  reached: boolean
  ok: boolean
  tokenAccepted: boolean
  ownerOk: boolean
}

const EXCHANGE_UNREACHABLE: PasteExchange = {
  reached: false,
  ok: false,
  tokenAccepted: false,
  ownerOk: false,
}

async function exchangePastedToken(token: string): Promise<PasteExchange> {
  try {
    const r = await fetch('/api/auth/me?token=' + encodeURIComponent(token), {
      credentials: 'include',
    })
    if (!r.ok) return { reached: true, ok: false, tokenAccepted: false, ownerOk: false }
    try {
      const body = (await r.json()) as
        | { token_accepted?: unknown; owner_ok?: unknown }
        | null
      return {
        reached: true,
        ok: true,
        tokenAccepted: body?.token_accepted === true,
        ownerOk: body?.owner_ok === true,
      }
    } catch {
      // 2xx with an unreadable body: the session is live, but nothing vouches
      // for the pasted token, so it counts as the unproven case.
      return { reached: true, ok: true, tokenAccepted: false, ownerOk: false }
    }
  } catch {
    return EXCHANGE_UNREACHABLE
  }
}

/**
 * Render *sentence* into *el* with the command wrapped in a <code> element.
 *
 * The command comes from `api.client.reauth_command`, so the value split on is
 * the SAME value a translator sees, and no untranslated literal sits in this
 * module. Falls back to the plain sentence when the command is absent from it,
 * because a translation that moved or dropped it must still be readable --
 * losing the chip is a styling regression, whereas rendering nothing would be a
 * blank banner. `ApiClient.coverage.test.tsx` pins the relationship across every
 * catalog, so a translation that breaks it reddens CI rather than silently
 * costing the chip.
 */
function setInstructionWithCommandChip(el: HTMLElement, sentence: string): void {
  const command = i18nT('api.client.reauth_command')
  const at = command ? sentence.indexOf(command) : -1
  if (at < 0) {
    el.textContent = sentence
    return
  }
  el.append(document.createTextNode(sentence.slice(0, at)))
  const chip = document.createElement('code')
  chip.textContent = command
  el.append(chip, document.createTextNode(sentence.slice(at + command.length)))
}

function showSessionExpiredBanner(lead?: string): void {
  if (_sessionExpiredShown) return
  _sessionExpiredShown = true
  _emitAuthEvent('mc-auth-required')
  const el = document.createElement('div')
  el.id = 'mc-session-expired'
  el.style.cssText =
    'position:fixed;top:0;left:0;right:0;z-index:99999;background:#b91c1c;color:#fff;' +
    'padding:12px 20px;text-align:center;font:14px/1.5 system-ui;'
  const b = document.createElement('b')
  b.textContent = lead ?? i18nT('api.client.session_expired')
  const input = document.createElement('input')
  input.type = 'text'
  input.placeholder = i18nT('api.client.paste_token_url_or_raw_token')
  input.style.cssText =
    'margin-left:12px;padding:4px 8px;border-radius:4px;border:1px solid #fca5a5;' +
    'background:#7f1d1d;color:#fff;font-size:13px;width:280px;cursor:text;caret-color:#fff;' +
    'outline:2px solid transparent;outline-offset:2px;transition:border-color 0.2s,box-shadow 0.2s;'
  input.addEventListener('focus', () => { input.style.borderColor = '#fff'; input.style.boxShadow = '0 0 0 3px rgba(255,255,255,0.25),0 0 20px rgba(255,255,255,0.1)' })
  input.addEventListener('blur', () => { input.style.borderColor = '#fca5a5'; input.style.boxShadow = 'none' })
  // A refused paste has to say so. The exchange's only other cue is the field
  // re-enabling, which is indistinguishable from nothing having happened, so
  // without this the user presses Enter again and concludes the banner is
  // broken. `role="status"` announces the text when it appears, since a sighted
  // user sees it arrive and a screen-reader user otherwise would not.
  //
  // A `div`, and deliberately unstyled: block layout puts it on its own line
  // without an inline-spacing rule, and it inherits the banner's white-on-red
  // type, which clears contrast at this size where a lighter red would not.
  const failure = document.createElement('div')
  failure.setAttribute('role', 'status')
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const v = input.value.trim()
      if (!v) return
      let t: string | null = null
      try { t = new URL(v).searchParams.get('token') } catch { t = v }
      if (!t) return
      // Disabled for the round trip so a second Enter cannot start a second
      // exchange. The pasted text is left in the field: on a refusal the user
      // corrects it rather than re-pasting from scratch.
      input.disabled = true
      // Drop the previous attempt's refusal now, so the next one is visibly a
      // new answer rather than text that was already on screen.
      failure.textContent = ''
      void exchangePastedToken(t).then(({ reached, ok, tokenAccepted, ownerOk }) => {
        input.disabled = false
        if (!reached) {
          // The request never got an answer, so nothing judged the token. Saying
          // it was not accepted would assert a check that never ran and send the
          // user to re-run a command that cannot help.
          failure.textContent = i18nT('api.client.token_exchange_unreachable')
          input.focus()
          return
        }
        if (!ok) {
          failure.textContent = i18nT('api.client.token_not_accepted')
          input.focus()
          return
        }
        // An owner denial is resolved by ONE event: a credential that both
        // authenticates AND clears the owner gate. A 2xx here establishes
        // neither. `/api/auth/me` is not owner-gated, so this session -- still
        // authenticated, still owner-denied -- answers 200 on its cookie, and
        // the middleware quietly falls back to that cookie when the pasted token
        // is invalid. A token minted before the owner was configured is valid
        // too, so it is accepted and still denied everywhere the gate fronts.
        // Clearing the latch on the status alone, or on acceptance alone, would
        // hide the prompt while every owner-gated call kept failing, and the
        // user would learn that from their next refused save.
        //
        // So the latch drops only when the gateway reports both. Without them
        // the banner stays up and says the token was not accepted, which is the
        // accurate reading of a 200 that proves neither.
        if (_staleOwnerBanner && !(tokenAccepted && ownerOk)) {
          failure.textContent = i18nT('api.client.token_not_accepted')
          input.focus()
          return
        }
        // `removeAuthBanner` returns early while the latch is set --
        // deliberately, because that session keeps answering 2xx on everything
        // the owner gate does not front, so an unrelated success proves
        // nothing. Dropping it here is what lets the banner clear on its own
        // recovery, which the previous full-page reload hid by wiping the
        // document.
        _staleOwnerBanner = false
        // Auth works again. `removeAuthBanner` drops the banner and clears the
        // terminal-refresh latch, so a LATER lapse in this document retries the
        // silent path instead of going straight back to the banner.
        removeAuthBanner()
        // Only queries that failed AND are holding nothing get refetched.
        //
        // `status === 'error'` alone is not enough, and the earlier version of
        // this comment was wrong to say an error-state query has no data to sync
        // from. React Query KEEPS the last successful `data` when a later
        // refetch fails: measured against `@tanstack/query-core`, a query that
        // succeeds and then fails a refetch reports `status: 'error'` with its
        // `data` still defined and unchanged. Refetching one of those
        // re-delivers data to whatever watches it, and
        // `McpCustomServerModal`'s effect runs
        // `setText(JSON.stringify(specQuery.data.spec, ...))` on every change of
        // `specQuery.data` -- so an unsaved spec draft would be silently
        // overwritten by the server's copy. A no-argument
        // `invalidateQueries()` does that to every panel at once, which is the
        // wider version of the same bug.
        //
        // `data === undefined` narrows it to queries that never carried a
        // successful value: exactly the ones the lapse broke, and the only ones
        // with nothing to overwrite a draft with.
        invalidateAcrossQueryClients({
          predicate: (q) => q.state.status === 'error' && q.state.data === undefined,
        })
      })
    }
  })
  // The connective text around the command used to sit here as two bare English
  // It used to be two bare English fragments wrapped around a <code> element,
  // which left the banner untranslated everywhere while the panel's own error
  // card was translated. A key per fragment is not the fix: the i18n gate
  // rejects a value that ends mid-sentence, because the translator cannot
  // reorder around a sibling it never sees -- and several languages need the
  // command somewhere English does not put it. `api.client.
  // session_expired_sign_in_again` already carries this same command inline in a
  // whole sentence across every locale, so this follows that precedent. A `div`
  // so it needs no inline spacing rule.
  //
  // The command still gets its own <code> element, found by splitting the
  // rendered sentence on the command itself rather than by a placeholder: that
  // keeps one whole translatable sentence in one key AND keeps the command
  // visually separable, which is the whole reason a reader can tell where it
  // begins and ends.
  const instruction = document.createElement('div')
  setInstructionWithCommandChip(
    instruction,
    i18nT('api.client.run_kirocrew_token_then_paste_sign_in_url'),
  )
  el.append(b, instruction, input, failure)
  const dismiss = document.createElement('button')
  dismiss.textContent = '✕'
  dismiss.style.cssText =
    'margin-left:12px;background:none;border:none;color:#fca5a5;cursor:pointer;font-size:18px;vertical-align:middle;'
  dismiss.addEventListener('click', () => {
    el.remove()
    _sessionExpiredShown = false
    _staleOwnerBanner = false
    _emitAuthEvent('mc-auth-cleared')
  })
  el.append(dismiss)
  document.body.prepend(el)
  requestAnimationFrame(() => input.focus())
}

export function checkSessionExpired(r: Response): Response {
  if (r.status === 403 && r.headers.get('X-Auth-Required') === 'true' && !_sessionExpiredShown) {
    // When this dashboard is running embedded in the Instances pane stack
    // (an <iframe> inside the hub), don't show the paste-token banner here —
    // the user can't easily fetch the remote token from inside the pane, and
    // the hub owns recovery.
    //
    // But try OUR OWN recovery first. This pane holds the same 30-day
    // `mc_refresh_<port>` cookie the top-level path below uses, and the common
    // cause of a burst of 403s here is a lapsed access cookie (a laptop that
    // slept through the proactive refresh) — which one silent refresh fixes, with
    // no SSH mint, no iframe reload, and no lost pane state. Handing that to the
    // hub instead costs a remote mint and a full reload of this document.
    //
    // Only when the refresh cannot recover do we signal the parent, which
    // force-mints a fresh token and reloads this iframe. That hand-off is
    // latched to once per document (see postAuthExpiredToHub): the hub answers
    // every ask with a mint, so an unrepairable session used to produce one mint
    // per rate-limit window for as long as the window stayed open.
    if (window.parent && window.parent !== window) {
      if (!_silentRefreshExhausted) {
        void attemptSilentRefresh().then((ok) => {
          if (ok) removeAuthBanner()
          else postAuthExpiredToHub()
        })
        return r
      }
      if (postAuthExpiredToHub()) return r
      // Cross-origin parent unreachable — fall through to the banner below.
    }
    // Mid-session the access cookie can lapse (20h TTL, or laptop sleep
    // pausing the proactive refresh timer) while the tab stays open. The
    // background polls then 403 in a burst. Before showing the re-auth banner,
    // try a single-flight silent refresh with the still-valid 30-day cookie —
    // this recovers without ever showing the banner. Only banner if the
    // refresh can't recover (chain revoked / no refresh cookie).
    if (!_silentRefreshExhausted) {
      void attemptSilentRefresh().then((ok) => {
        if (ok) removeAuthBanner()
        else if (_silentRefreshExhausted) showSessionExpiredBanner()
      })
      return r
    }
    showSessionExpiredBanner()
  }
  return r
}

/**
 * Recovery prompt for the ONE denial the silent-refresh path can never clear:
 * a session whose token was minted before `KIROCREW_OWNER_ID` was configured.
 * `/api/auth/refresh` re-mints from the incoming subject, so a "successful"
 * refresh would rotate the cookie and keep the stale bootstrap subject — the
 * next owner-gated call is denied again, forever. Only a fresh sign-in (a new
 * token link, whose subject is derived from the now-configured owner) recovers,
 * so this goes straight to the banner instead of attempting a refresh.
 */
function handleStaleOwnerSession(): void {
  // Latch FIRST, even when a banner is already showing: a plain-expiry banner
  // raised moments earlier would otherwise keep its clear-on-2xx self-dismissal
  // and vanish on the next successful poll — this session still succeeds on
  // everything the owner gate does not front, so once the stale denial is seen
  // only the X or a successful in-banner token exchange may clear the prompt.
  _staleOwnerBanner = true
  if (_sessionExpiredShown) return
  // Embedded in the Instances pane stack: hand recovery to the hub, mirroring
  // checkSessionExpired — the hub force-mints a fresh token (whose subject is
  // derived from the current owner) and reloads this iframe.
  // No silent refresh attempt here, unlike checkSessionExpired: re-minting from
  // the incoming subject keeps the stale bootstrap subject, so a "successful"
  // refresh would rotate the cookie and be denied again. The hand-off is latched
  // to once per document, and `_staleOwnerBanner` above keeps a later 2xx from
  // re-opening it — a hub re-mint cannot fix this denial either, so asking twice
  // only buys another SSH mint.
  if (typeof window !== 'undefined' && window.parent && window.parent !== window) {
    if (postAuthExpiredToHub()) return
    // Cross-origin parent unreachable — fall through to the banner below.
  }
  showSessionExpiredBanner(i18nT('api.client.stale_owner_session'))
}

// The signal module is a leaf shared with the direct-fetch surfaces (app-sdk,
// the MCP-app relay, Mochi's approval bridge); this module owns the banner, so
// it supplies the prompt those detections raise. Re-exported so consumers of
// the blessed transport can reference the wire contract from one place.
installStaleOwnerHandler(handleStaleOwnerSession)
installSessionExpiryHandler(checkSessionExpired)
export { STALE_OWNER_SESSION_CODE }

/**
 * `ApiError` and `friendlyErrText` now live in the side-effect-free
 * `api/apiError` module so app API clients can import them without pulling this
 * file's graph (queryClient, transport install, the error journal) into their
 * bundles. Re-exported here because this has always been their import path —
 * every existing consumer, and every test that mocks `../api/client`, is
 * unchanged by the move.
 */
export { ApiError, friendlyErrText, toApiError }

/**
 * Whether *e* is a failure the user can only clear by signing back in.
 *
 * The gateway's auth denial names the cryptographic reason it rejected the
 * token (`invalid signature`, `session revoked`), which is accurate and
 * useless to a user: it neither says the session is what broke nor points at
 * the re-auth banner. Call sites use this to swap a futile retry for the one
 * action that recovers.
 *
 * An interposed proxy's challenge is deliberately NOT one of these, though it
 * also sets `authRequired`: the gateway never saw that request, so its sign-in
 * banner and token flow cannot clear it, and offering them names the wrong
 * system. Those failures carry their own remedy in the message instead. Call
 * sites that only want the retry withdrawal read `authRequired` directly.
 */
export const isAuthExpiredError = (e: unknown): boolean =>
  e instanceof ApiError && e.authRequired && !e.edgeChallenge

/**
 * Build the ApiError AND journal it.
 *
 * `j`/`jNullable` are the single chokepoint every dashboard API failure passes
 * through, which makes this the one place that can capture the full context
 * (status, path, backend `code`, raw body) before call sites collapse it to
 * `e.message`. `utils/errorReport` then lets a shared error banner recover that
 * context from the message alone — see AskAgentButton / ErrorNotice.
 */
const apiFailure = (r: Response, errText: string, benign?: BenignDenial): ApiError => {
  // An auth denial's own reason text ("invalid signature") describes HMAC
  // verification, not anything the user can act on, and every card that renders
  // it hides the fact that one re-auth clears all of them at once. Substitute
  // the recovery instruction for display; the raw reason still travels in
  // `body` and in the error report's `detail` for diagnostics.
  const authRequired = r.status === 403 && r.headers.get('X-Auth-Required') === 'true'
  // The stale-owner signal is matched on status AND the backend's code — a
  // generic 401 (or any 403) keeps its current handling untouched. Detection
  // lives HERE rather than in checkSessionExpired because the code travels in
  // the BODY, which checkSessionExpired (a pre-body Response hook) cannot read;
  // the prompt itself is idempotent, so the factory raising it cannot spam.
  const staleOwnerSession = noteStaleOwnerResponse(r.status, errText)
  // A third denial neither of the above can see: a proxy in front of the gateway
  // answered with its own sign-in page, so the signals are status + type + body.
  // Skipped when the gateway's own header is present: that header proves the request
  // reached the gateway, so nothing interposed answered it.
  const edgeOutcome = authRequired || staleOwnerSession
    ? null
    : noteEdgeAuthChallenge(r.status, r.headers.get('content-type'), errText)
  // Every one of these needs a person: the gateway never saw the request, so a silent
  // retry a second later reproduces it whether a session lapsed or a firewall refused.
  const edgeAuthExpired = edgeOutcome !== null
  const message = staleOwnerSession
    ? i18nT('api.client.stale_owner_session_sign_in_again')
    : authRequired
      ? i18nT('api.client.session_expired_sign_in_again')
      : edgeChallengeMessage(edgeOutcome)
        || friendlyErrText(r.status, errText)
        || `HTTP ${r.status}`
  const code = parseErrorCode(errText)
  // One specific denial on one endpoint is a DESIGNED, benign signal rather than a
  // failure worth showing the user — a disabled optional feature answering its own
  // probe (instances is deny-by-default; see listInstances). The caller opts that
  // one out via `benign`: the ApiError is still THROWN so the caller's catch runs,
  // but it is not journaled, so it cannot surface as a spurious error report on an
  // unrelated route (e.g. /chat/new-session mounting the sidebar).
  //
  // The match is on status AND the gateway's own `code`, never status alone. The
  // same endpoint answers 403 to a non-owner caller and to a Slack-origin request,
  // and both are real authorization failures a reader needs; keyed on status they
  // would be silently swallowed along with the routine one.
  //
  // The three auth-recovery denials above are additionally excluded, including the
  // edge challenge: a proxy answering with its own sign-in page carries no code of
  // ours, so it cannot match `benign`, but the term is kept explicit because each of
  // the three needs a person and none may ever be opted out by a call site.
  const expectedBenign = !!benign
    && r.status === benign.status
    && code === benign.code
    && !authRequired
    && !staleOwnerSession
    && !edgeAuthExpired
  if (!expectedBenign) {
    recordError({
      source: 'api',
      message,
      status: r.status,
      code,
      endpoint: requestPath(r.url),
      detail: errText,
    })
  }
  // no retry can succeed until the user signs in again.
  return new ApiError(
    r.status, message, errText,
    authRequired || staleOwnerSession || edgeAuthExpired,
    edgeAuthExpired,
  )
}

/**
 * The auth-recovery half of `j` for a response that is handed back RAW instead
 * of parsed (the chat-core transport's wire): the pre-body 403 `X-Auth-Required`
 * hook, and the body-borne stale-owner code a 401 carries -- read off a CLONE so
 * the caller's own `json()` still works. Fire-and-forget: the recovery prompts
 * are idempotent and the receipt read must not wait on them. A 2xx also clears
 * a stale session-expired banner, exactly as `j` does -- a send that succeeds
 * after auth was restored elsewhere must not leave the banner up.
 */
function sendResponseAuthRecovery(r: Response): Response {
  checkSessionExpired(r)
  if (r.ok) removeAuthBanner()
  if (r.status === 401) {
    // Best-effort: a wire may hand back a Response-like without `clone`.
    try {
      void r.clone().text().then((body) => noteStaleOwnerResponse(r.status, body)).catch(() => {})
    } catch { /* not a real Response; nothing to read */ }
  }
  return r
}

/**
 * A non-2xx this endpoint's caller handles itself, identified by the denial it
 * IS rather than by the status it arrives with.
 *
 * Status alone is not enough to identify a denial, and on the motivating
 * endpoint it is actively wrong: `/api/instances` answers 403 for a disabled
 * feature, for a non-owner caller, and for a Slack-origin request, and only the
 * first is routine. `code` is the machine-readable discriminator the gateway
 * emits for exactly that case, so both must match before anything is opted out.
 */
type BenignDenial = { readonly status: number; readonly code: string }

/**
 * The one parser body behind `j`, `jNullable` and `jInstancesDisabled`.
 *
 * `benign` and `nullOn204` are the ONLY differences between the three, so they
 * share this rather than holding copies that drift as the auth-recovery steps
 * above change.
 */
const parseJson = async (r: Response, benign?: BenignDenial, nullOn204 = false) => {
  checkSessionExpired(r)
  if (r.ok) removeAuthBanner()
  // Before the !r.ok branch, because 204 IS ok: the banner clear above still runs,
  // exactly as it did when this was its own copy of the body.
  if (nullOn204 && r.status === 204) return null
  if (!r.ok) {
    const errText = await r.text()
    throw apiFailure(r, errText, benign)
  }
  return r.json()
}

const j = (r: Response) => parseJson(r)

/**
 * Nullable variant of j(): preserves auth recovery + ApiError semantics but
 * returns null on 204 (No Content). Used by tips endpoints.
 */
const jNullable = (r: Response) => parseJson(r, undefined, true)

/**
 * The one denial in the dashboard that is a DESIGNED, benign signal rather than
 * a failure worth journaling: `/api/instances` answering its own list probe on
 * an install where the control plane is simply off.
 *
 * Deliberately NOT a `(status, code)` parameter pair. A parser taking those
 * would hand every domain module a general "ignore this status everywhere"
 * opt-out, and there is exactly one denial that has earned it. A second one
 * would be a second constant here, reviewed on its own merits — which is the
 * point: each addition is a visible decision at the facade rather than a call
 * site quietly passing different arguments.
 */
const INSTANCES_DISABLED: BenignDenial = { status: 403, code: 'instances_disabled' }

/**
 * `j` for the one benign denial above — nothing else.
 *
 * `j`'s exact semantics (auth recovery, `ApiError` on non-2xx) EXCEPT that a 403
 * carrying `instances_disabled` is thrown but NOT recorded in the error journal.
 * Any other denial on that same endpoint, INCLUDING another 403, journals
 * normally: `/api/instances` also answers 403 to a non-owner caller and to a
 * Slack-origin request, and both are real authorization failures a reader needs.
 *
 * Why it exists: the instances control plane is deny-by-default
 * (`instances.enabled` off), so a 403 to its own list probe is expected on most
 * installs. Journaling it made the sidebar's routine `['instances']` query
 * publish a spurious "/api/instances -> 403" error report on whatever route
 * mounted the sidebar (e.g. /chat/new-session).
 *
 * Handed to the domain modules through `ClientTransport` rather than imported by
 * them, for the reason that interface's own docstring gives: a module must reach
 * the SAME parser objects the facade installs, or an edition's calls and core's
 * calls diverge.
 */
const jInstancesDisabled = (r: Response) => parseJson(r, INSTANCES_DISABLED)
// X-Session-Key ensures the server-side ephemeral gate always runs.
// Without it, browser requests would skip the `if sk:` check — a fail-open
// path that an MCP subprocess could exploit by omitting its own header.
const _sk = { 'X-Session-Key': 'dashboard:ui' }

/**
 * Count a mutating request against the artifact it targets, so the leave-time
 * cleanup can tell an unacknowledged write from a document nobody touched.
 *
 * Hooked HERE, at the transport, rather than in each caller: the previous design
 * asked every write path to announce itself and repeatedly shipped one that did
 * not, letting a document be deleted with its own PATCH still in the air. A
 * request cannot be issued without passing through these five helpers, so this
 * cannot be forgotten by a new call site. `settle` itself is excluded — it is the
 * cleanup, not a user write, and counting it would have it guard against itself.
 */
const ARTIFACT_WRITE_RE = /\/api\/artifacts\/([^/?#]+)/
function trackArtifactWrite(url: string, res: Promise<Response>): Promise<Response> {
  const m = ARTIFACT_WRITE_RE.exec(url)
  if (!m || url.includes('/settle')) return res
  let slug: string
  try {
    slug = decodeURIComponent(m[1])
  } catch {
    slug = m[1]
  }
  beginArtifactWrite(slug)
  // `finally` on both paths: a FAILED write clears too, which is correct — the
  // server never applied it, so the record it re-reads is authoritative anyway.
  return res.finally(() => endArtifactWrite(slug))
}

const get = (url: string, sessionKey?: string, signal?: AbortSignal) =>
  fetch(url, { headers: { ...(sessionKey ? { 'X-Session-Key': sessionKey } : _sk) }, ...(signal ? { signal } : {}) })
const post = (
  url: string,
  body?: object,
  sessionKey?: string,
  extra?: HeadersInit,
  redirect?: RequestRedirect,
) =>
  trackArtifactWrite(url, fetch(url, {
    method: 'POST',
    // sessionKey overrides the shared `dashboard:ui` placeholder with the REAL
    // slot. The placeholder satisfies the server's `if sk:` gate but names no
    // actual session, so a restricted (incognito) slot was never recognised as
    // restricted and its writes were allowed through. Callers acting on behalf
    // of a specific chat slot must pass it.
    // `extra` carries a per-call precondition header (a view the server must
    // still agree with) without every caller re-implementing the header merge.
    // `redirect` is for a caller whose URL is not core's to choose: a validated
    // target that answers 3xx would otherwise be followed automatically, and the
    // check that approved the FIRST url never sees the second. Defaulted so no
    // existing caller changes behaviour.
    ...(redirect ? { redirect } : {}),
    headers: { 'Content-Type': 'application/json', ...(sessionKey ? { 'X-Session-Key': sessionKey } : _sk), ...extra },
    body: body ? JSON.stringify(body) : undefined,
  }))
const put = (url: string, body: object, sessionKey?: string, extra?: HeadersInit) =>
  trackArtifactWrite(url, fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json', ...(sessionKey ? { 'X-Session-Key': sessionKey } : _sk), ...extra }, body: JSON.stringify(body) }))
const del = (url: string, body?: object, sessionKey?: string, extra?: HeadersInit) =>
  trackArtifactWrite(url, fetch(url, { method: 'DELETE', headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(sessionKey ? { 'X-Session-Key': sessionKey } : _sk), ...extra }, body: body ? JSON.stringify(body) : undefined }))
const patch = (url: string, body: object, sessionKey?: string, signal?: AbortSignal) =>
  trackArtifactWrite(url, fetch(url, {
    method: 'PATCH',
    // Same override as post(): replace the shared `dashboard:ui` placeholder with
    // the REAL slot when the write belongs to a chat session, so the server's
    // restricted-session gate applies to it.
    headers: { 'Content-Type': 'application/json', ...(sessionKey ? { 'X-Session-Key': sessionKey } : _sk) },
    body: JSON.stringify(body),
    signal,
  }))

// Publish the blessed transport so a downstream edition can build its OWN typed
// API module on the SAME session-key-authenticated helpers as core methods
// (inheriting X-Session-Key + auth-recovery + ApiError), instead of forking this
// file or writing methods on raw fetch. See api/apiTransport.ts.
installApiTransport({ get, post, put, del, patch, j, jNullable })

// The Kiro credit-usage wire payload and the view model normalized from it stay
// defined here, side by side: `KiroAccountModal` and `api/kiroUsage.ts` read
// them from this module, and `./client/telemetry` imports them as types.
export interface KiroBonusCreditGrantPayload {
  name: string
  used: number
  total: number
  days_left?: number
}

export interface KiroUsagePayload {
  available?: boolean
  /**
   * Why usage is unavailable when `available` is false (`api_key_auth` or
   * `signin_required`); absent when the gateway simply holds no reading.
   */
  reason?: string
  credits_used?: number
  credits_covered?: number
  credits_overage?: number
  credits_plan?: number
  resets?: string
  plan?: string
  cost_usd?: number
  overage_rate?: number | string
  bonus_credits?: KiroBonusCreditGrantPayload[]
  stale?: boolean
  account?: string
  email?: string
  account_type?: string
  start_url?: string
}

/** `POST /api/sessions/usage/refresh` — the GET envelope plus the declined-scrape marker. */
export interface KiroUsageRefreshResponse {
  usage?: KiroUsagePayload
  skipped?: 'scrape_parked'
  retry_after?: number
}

export interface KiroBonusCreditGrant {
  name: string
  used: number
  total: number
  daysLeft?: number
}

export interface KiroCreditUsage {
  used: number
  limit: number
  overage: number
  resets?: string
  plan?: string
  costUsd?: number
  overageRate?: number
  bonusCredits: KiroBonusCreditGrant[]
  stale: boolean
  account?: string
  email?: string
  accountType?: string
  startUrl?: string
}

// Every endpoint owner under `./client/` is built on this one transport: the
// helper objects just installed as the blessed `apiTransport`, plus the recovery
// hooks the methods that read their own response call directly.
const transport: ClientTransport = {
  get,
  post,
  put,
  del,
  patch,
  j,
  jNullable,
  jInstancesDisabled,
  sessionKeyHeader: _sk,
  checkSessionExpired,
  removeAuthBanner,
  sendResponseAuthRecovery,
}

const system = createSystemEndpoints(transport)
const telemetry = createTelemetryEndpoints(transport)
const chat = createChatEndpoints(transport)
const onboarding = createOnboardingEndpoints(transport)
const security = createSecurityEndpoints(transport)
const remoteAccess = createRemoteAccessEndpoints(transport)
const featureDiscovery = createFeatureDiscoveryEndpoints(transport)
const themes = createThemesEndpoints(transport)
const instances = createInstancesEndpoints(transport)
const cloud = createCloudEndpoints(transport)
const memory = createMemoryEndpoints(transport)
const sessions = createSessionsEndpoints(transport)
const mcp = createMcpEndpoints(transport)
const agents = createAgentsEndpoints(transport)
const chatSlotSettings = createChatSlotSettingsEndpoints(transport)
const files = createFilesEndpoints(transport)
const cron = createCronEndpoints(transport)
const hooks = createHooksEndpoints(transport)
const skills = createSkillsEndpoints(transport)
const steering = createSteeringEndpoints(transport)
const connections = createConnectionsEndpoints(transport)
const config = createConfigEndpoints(transport)
const capabilityManager = createCapabilityManagerEndpoints(transport)
const voice = createVoiceEndpoints(transport)
const sourceControl = createSourceControlEndpoints(transport)
const monitors = createMonitorsEndpoints(transport)
const chatOrganization = createChatOrganizationEndpoints(transport)
const notifications = createNotificationsEndpoints(transport)
const subagents = createSubagentsEndpoints(transport)
const approvals = createApprovalsEndpoints(transport)
const taskRunner = createTaskRunnerEndpoints(transport)
const workflows = createWorkflowsEndpoints(transport)
const updates = createUpdatesEndpoints(transport)
const agentChannels = createAgentChannelsEndpoints(transport)
const apps = createAppsEndpoints(transport)
const artifacts = createArtifactsEndpoints(transport)
const browserAndComputerUse = createBrowserAndComputerUseEndpoints(transport)
const decisions = createDecisionsEndpoints(transport)
const messaging = createMessagingEndpoints(transport)
const autoResearch = createAutoResearchEndpoints(transport)

// Spread in the order the methods have always had, so the key order is
// unchanged. A key two segments both defined would silently take the later
// one; `ApiClient.refactor.facade.test.ts` holds every key to one owner.
export const api = {
<<<<<<< HEAD
  status: () => fetch('/api/status').then(j),
  tunnelStatus: () => fetch('/api/tunnel/status').then(j) as Promise<TunnelStatus>,
  system: () => fetch('/api/system').then(j),
  sessionStorage: () => get('/api/system/session-storage').then(j) as Promise<SessionStorageReport>,
  sessionStorageCleanup: (olderThanDays: number, dryRun = false) =>
    post('/api/system/session-storage/cleanup', { older_than_days: olderThanDays, dry_run: dryRun })
      .then(j) as Promise<SessionStorageCleanup>,
  sessionStorageRestore: (batchId: string, uids?: string[]) =>
    post('/api/system/session-storage/restore', uids ? { batch_id: batchId, uids } : { batch_id: batchId })
      .then(j) as Promise<{ restored: number }>,
  /** Starts an empty and returns the job; the delete outlives this request. */
  sessionStorageEmpty: (batchIds: string[]) =>
    post('/api/system/session-storage/empty', { batch_ids: batchIds }).then(j) as Promise<SessionStorageEmptyJob>,
  /** The running or last-finished empty. Cheap — no store is walked, so it polls. */
  sessionStorageEmptyStatus: () =>
    get('/api/system/session-storage/empty').then(j) as Promise<{ job: SessionStorageEmptyJob | null }>,
  /** Session inventory — the flat list contract (§1). */
  sessionInventory: () =>
    get('/api/system/session-storage/sessions').then(j) as Promise<SessionInventoryList>,
  /** Session detail — lazy per-row fetch (§2). */
  sessionInventoryDetail: (uid: string) =>
    get(`/api/system/session-storage/sessions/${encodeURIComponent(uid)}`).then(j) as Promise<SessionInventoryDetail>,
  /** Move explicit selection to trash (§3). */
  sessionInventoryTrash: (uids: string[]) =>
    post('/api/system/session-storage/trash', { uids }).then(j) as Promise<SessionTrashResult>,
  telemetryStartup: () => fetch('/api/telemetry/startup').then(j),
  // Per-turn context injection breakdown for one session. Independent of the
  // telemetry main switch: the usage rows it reads are always written.
  telemetryContextTrace: (slot: string) =>
    fetch('/api/telemetry/context-trace?slot=' + encodeURIComponent(slot)).then(j),
  /** Per-turn usage rows for one session — the Spend table's drill-down.
   *  Same always-written row store as the context trace; the dashboard reads
   *  every row (the endpoint's app-ownership filter applies to app callers). */
  usageTurns: (slot: string) =>
    fetch('/api/usage/turns?slot=' + encodeURIComponent(slot)).then(j),
  /** Intent summary for the chat summary panel.
   *
   *  Read-only: it never triggers generation. Summaries are produced at turn end
   *  by a background pass, so opening the panel cannot spend tokens and repeated
   *  opening cannot become a refresh loop. Returns `enabled: false` (not an
   *  error) when the feature is off, so the panel can explain itself. */
  sessionSummary: (slot: string) =>
    fetch('/api/chat/slots/' + encodeURIComponent(slot) + '/summary').then(j) as Promise<SessionSummary>,
  /** Summarize this session NOW, on the person's explicit request.
   *
   *  Same path as the GET, different verb: reading a summary must stay free of
   *  side effects, so spending tokens is a separate verb rather than a flag on
   *  the read. Rejects with the body's `code` (`summary_in_flight`,
   *  `too_few_turns`, `summary_unavailable`, `summary_disabled`) so the panel can
   *  say which rather than showing one generic failure. */
  generateSessionSummary: (slot: string) =>
    fetch('/api/chat/slots/' + encodeURIComponent(slot) + '/summary', {
      method: 'POST',
    }).then(j) as Promise<SessionSummary>,
  beaconStatus: () => fetch('/api/telemetry/beacon').then(j),
  /** Local metric-collection posture for the Privacy panel's recording switch.
   *  Separate from telemetryStartup(), which parses every shard in the window. */
  collectionStatus: () => fetch('/api/telemetry/collection').then(j),
  // Background polls read the gateway's latched state (no kiro-cli subprocess).
  // `refresh` is the explicit user action (Refresh / Check again) that forces a
  // real host probe.
  /**
   * `refresh` picks the probe mode, and the two are deliberately different:
   * `'explicit'` is the human Check again and always probes the host, `'auto'` is
   * the blocking gate's poll and is coalesced server-side behind a short floor so
   * several open tabs cannot multiply the `kiro-cli` spawns. `false` reads the
   * gateway's latched state and spawns nothing.
   */
  kiroPrerequisite: (refresh: false | 'auto' | 'explicit' = false) => {
    // Built with URLSearchParams like every other query here (see artifacts
    // below): the mode is its own wire value, so there is no query-string
    // literal for the i18n gate to mistake for user-visible copy.
    const params = new URLSearchParams()
    if (refresh) params.set('refresh', refresh)
    const s = params.toString()
    return get(`/api/kiro-prerequisite${s ? `?${s}` : ''}`).then(
      j,
    ) as Promise<KiroPrerequisiteStatus>
  },
  // A POST, not a flag on the status GET: the gateway's CSRF check and its SEL
  // audit are both method-scoped, so a spec rewrite reached from a GET would be
  // cross-site triggerable and would leave no audit record.
  repairKiroPrerequisiteSpecs: () =>
    post('/api/kiro-prerequisite/repair-specs').then(j) as Promise<KiroPrerequisiteStatus>,
  // A POST for the same CSRF/audit reasons as the spec repair above. Runs the
  // CLI's own in-place self-update on the gateway host and returns the
  // post-update snapshot; `cli_update_error` is empty on success.
  updateKiroPrerequisiteCli: () =>
    post('/api/kiro-prerequisite/update-cli').then(j) as Promise<KiroPrerequisiteStatus>,
  // KAS-mode in-product sign-in (no kiro-cli, no terminal). Status is a cheap
  // read; every step that changes sign-in state is a POST for the same
  // CSRF/audit reasons as the spec repair above. Error responses carry a
  // machine-readable `code` field alongside the human message.
  kasLoginStatus: () => get('/api/kas-login').then(j) as Promise<KasLoginStatus>,
  kasLoginBeginDevice: (provider: string, extra?: { start_url?: string; region?: string }) =>
    post('/api/kas-login/device', { provider, ...(extra ?? {}) }).then(
      j,
    ) as Promise<KasLoginDeviceSession>,
  kasLoginPoll: (login_id: string) =>
    post('/api/kas-login/poll', { login_id }).then(j) as Promise<KasLoginPollResult>,
  // Loopback begin answers 409 `loopback_unavailable` when this install shape
  // cannot receive the callback (or every allowlisted port is busy); the gate
  // treats that as "start the device flow instead", not as a failure.
  kasLoginBeginLoopback: (provider: string) =>
    post('/api/kas-login/loopback', { provider }).then(j) as Promise<KasLoginLoopbackSession>,
  // Idempotent: releases a loopback listener's port early on every start-over path.
  kasLoginCancel: (login_id: string) =>
    post('/api/kas-login/cancel', { login_id }).then(j) as Promise<{ ok: boolean }>,
  kasLoginLogout: (identity: string) =>
    post('/api/kas-login/logout', { identity }).then(j) as Promise<KasLoginStatus>,
  onboardingImportScan: () =>
    get('/api/onboarding/import/scan').then(j) as Promise<AgentImportScanResponse>,
  onboardingImportApply: (body: AgentImportApplyRequest) =>
    post('/api/onboarding/import/apply', body).then(j) as Promise<AgentImportApplyResponse>,
  onboardingImportState: (body: { completed: true }) =>
    put('/api/onboarding/import/state', body).then(jNullable) as Promise<{ ok?: boolean } | null>,
  // Counts are derived server-side from the controls they describe, so a null
  // means "temporarily unresolvable", never "zero".
  securityStats: () => get('/api/security/stats').then(j) as Promise<{ denied_commands: number | null; suspicious_patterns: number | null; tool_schemas: number | null; redaction_paths: number | null }>,
  securityPosture: () => get('/api/security/posture').then(j) as Promise<SecurityPostureData>,
  // `sessionKey` MUST carry the active slot's key (`dashboard:<slot>`) when one
  // is active: the server's restricted-session guard reads X-Session-Key, and
  // the shared `dashboard:ui` default answers "not restricted" — which would
  // let an incognito/temporary slot mint a durable any-device credential. Same
  // cooperative-honesty contract as the tailnet mobile surface.
  mobileLoginLink: (sessionKey?: string) =>
    post('/api/auth/mobile-link', undefined, sessionKey).then(j) as Promise<{
    url: string
    expires_in: number
  }>,
  // Phone-connection methods available on this deployment under the current
  // governance ceiling (CPP mobile_connect seam). Descriptor-only: minting the
  // credential stays on each method's own endpoint above/below. An empty list
  // hides the sidebar "Connect your phone" entry entirely.
  mobileConnectMethods: () =>
    get('/api/mobile-connect/methods').then(j) as Promise<MobileConnectMethodsData>,
  // Tailnet origin (Settings → Security). READ ONLY here: the toggle writes
  // `dashboard.tailscale.enabled` through the generic config PATCH, because the
  // setting IS a config value and the status endpoint reports what the running
  // server resolved from it at startup.
  tailnetStatus: () => get('/api/tailnet/status').then(j) as Promise<TailnetStatusData>,
  // Mobile access. `tailnetMobile` is a LIVE probe (two daemon round trips
  // server-side), so poll it gently; the mutations below are user-driven.
  tailnetMobile: () => get('/api/tailnet/mobile').then(j) as Promise<TailnetMobileData>,
  tailnetMobileConfigure: () =>
    post('/api/tailnet/mobile/configure', {}).then(j) as Promise<TailnetMobileConfigure>,
  tailnetMobilePublish: () =>
    post('/api/tailnet/mobile/publish', {}).then(j) as Promise<TailnetMobileMutation>,
  tailnetMobileUnpublish: () =>
    post('/api/tailnet/mobile/unpublish', {}).then(j) as Promise<TailnetMobileMutation>,
  // Mints a session token. Called ONLY from an explicit user action — never on
  // render — because the response is a live credential. `sessionKey` carries
  // the caller's REAL slot key so the server's restricted-session guard sees
  // it instead of the shared `dashboard:ui` placeholder.
  tailnetMobileQr: (ttl?: string, sessionKey?: string) =>
    post('/api/tailnet/mobile/qr', ttl ? { ttl } : {}, sessionKey).then(j) as Promise<TailnetMobileQr>,
  // Denied commands (Settings → Security). Every endpoint returns the full
  // refreshed snapshot so callers can seed their query cache from the response.
  deniedCommands: () => get('/api/security/denied-commands').then(j) as Promise<DeniedCommandsData>,
  toggleBuiltinDeniedCommand: (id: string, enabled: boolean) =>
    patch('/api/security/denied-commands/builtins/' + encodeURIComponent(id), { enabled }).then(j) as Promise<DeniedCommandsData>,
  setDeniedCommandsDisableAll: (value: boolean) =>
    patch('/api/security/denied-commands/disable-all', { value }).then(j) as Promise<DeniedCommandsData>,
  addUserDeniedCommand: (pattern: string, note = '') =>
    post('/api/security/denied-commands/user', { pattern, note }).then(j) as Promise<DeniedCommandsData>,
  toggleUserDeniedCommand: (id: string, enabled: boolean) =>
    patch('/api/security/denied-commands/user/' + encodeURIComponent(id), { enabled }).then(j) as Promise<DeniedCommandsData>,
  deleteUserDeniedCommand: (id: string) =>
    del('/api/security/denied-commands/user/' + encodeURIComponent(id)).then(j) as Promise<DeniedCommandsData>,
  // Third-party app trust (Settings → Security). Like denied-commands, every
  // endpoint returns the full refreshed snapshot so callers can seed the query
  // cache from the mutation response instead of re-fetching.
  listTrustedApps: () => get('/api/security/trusted-apps').then(j) as Promise<TrustedAppsData>,
  trustApp: (name: string, repository?: string) =>
    post(
      '/api/security/trusted-apps/' + encodeURIComponent(name),
      repository ? { repository } : undefined,
    ).then(j) as Promise<TrustedAppsData>,
  // Returns the snapshot PLUS `disabled` — revoking trust also disables an app
  // that is currently enabled, so its code stops running immediately.
  untrustApp: (name: string) =>
    del('/api/security/trusted-apps/' + encodeURIComponent(name)).then(j) as Promise<TrustedAppsRevokeResult>,
  setTrustAllApps: (value: boolean) =>
    put('/api/security/trusted-apps/allow-all', { value }).then(j) as Promise<TrustedAppsData>,
  // Read-only governance policy viewer (Settings → Security). No write path —
  // the enterprise ceiling is file-authored and un-editable via the UI.
  governancePolicy: () => get('/api/governance/policy').then(j) as Promise<GovernancePolicyData>,
  suggestions: (force?: boolean) => fetch(`/api/suggestions${force ? '?force=1' : ''}`).then(j) as Promise<{ suggestions: string[]; generated_at: number; stale: boolean }>,
  branding: () => fetch('/api/dashboard/branding').then(j) as Promise<{ bot_name: string; avatar: string; direct_local?: boolean }>,
  // Instances (multi-instance management) — owner-only, gated by instances.enabled.
  // listInstances throws ApiError(403) when the feature is disabled; callers
  // should catch and render the enable toggle rather than an error. `active`
  // is true only when the SSH manager is actually running (the flag was on at
  // gateway startup) — enabled-but-not-active means a restart is required.
  listInstances: () => get('/api/instances').then(j) as Promise<{ active: boolean; instances: InstanceView[]; warm_set_cap: number; sso: SsoStatus }>,
  addInstance: (body: AddInstanceBody) => post('/api/instances', body).then(j) as Promise<InstanceView>,
  updateInstance: (id: string, body: Partial<AddInstanceBody>) =>
    patch('/api/instances/' + encodeURIComponent(id), body).then(j) as Promise<InstanceView>,
  removeInstance: (id: string) => del('/api/instances/' + encodeURIComponent(id)).then(j),
  instanceStatus: (id: string, diagnose = false) =>
    get('/api/instances/' + encodeURIComponent(id) + '/status' + (diagnose ? '?diagnose=1' : '')).then(j) as Promise<InstanceTunnelStatus>,
  connectInstance: (id: string) =>
    post('/api/instances/' + encodeURIComponent(id) + '/connect').then(j) as Promise<
      InstanceTunnelStatus & { token?: string }
    >,
  refreshInstanceToken: (id: string) =>
    post('/api/instances/' + encodeURIComponent(id) + '/refresh-token').then(j) as Promise<
      InstanceTunnelStatus & { token?: string }
    >,
  disconnectInstance: (id: string) =>
    post('/api/instances/' + encodeURIComponent(id) + '/disconnect').then(j) as Promise<{
      disconnected: string
      was_connected: boolean
    }>,
  restartInstance: (id: string) =>
    post('/api/instances/' + encodeURIComponent(id) + '/restart').then(j) as Promise<{
      ok: boolean
      message: string
    }>,
  // Copies a session to another instance. The local session is left untouched:
  // the peer allocates its own key, so this is a copy and never a move.
  sendSessionToInstance: (id: string, slot: string) =>
    post('/api/instances/' + encodeURIComponent(id) + '/send-session', { slot }).then(j) as Promise<{
      ok: boolean
      instance: string
      remote_key: string
      messages: number
      // '' when the peer is too old to report it — treated as unknown.
      resume_mode?: 'session_load' | 'prefix' | ''
    }>,
  // Cloud provisioning (owner-only) — launch a cloud-hosted remote crew on the
  // user's OWN AWS account, then register it as an SSM instance on connect. The
  // launch is a DURABLE gateway job (see cloud/launch_job.py): it survives
  // dashboard navigation and restart, so the UI polls its state rather than
  // holding it in memory. `tag` (kc-xxxx) is the cloud lifecycle handle used by
  // stop/start/destroy; `instance_id` (i-...) is the EC2 id it registers under.
  cloudPreflight: (profile?: string, region?: string) => {
    const p = new URLSearchParams()
    if (profile) p.set('profile', profile)
    if (region) p.set('region', region)
    const s = p.toString()
    return get('/api/cloud/preflight' + (s ? '?' + s : '')).then(j) as Promise<CloudPreflight>
  },
  cloudIamPolicy: () => get('/api/cloud/iam-policy').then(j) as Promise<{ policy: string }>,
  cloudLaunches: () => get('/api/cloud/launch').then(j) as Promise<{ jobs: LaunchJob[] }>,
  cloudLaunch: (body: { profile: string; region: string; size_key: string }) =>
    post('/api/cloud/launch', body).then(j) as Promise<LaunchJob>,
  cloudLaunchStatus: (id: string) =>
    get('/api/cloud/launch/' + encodeURIComponent(id)).then(j) as Promise<LaunchJob>,
  cloudLaunchCancel: (id: string) =>
    post('/api/cloud/launch/' + encodeURIComponent(id) + '/cancel').then(j) as Promise<LaunchJob>,
  // Fetches the device-code prompt while the job is awaiting sign-in; 409 when
  // there is no pending prompt (surfaced as ApiError(409) to the caller).
  cloudLaunchSignin: (id: string) =>
    post('/api/cloud/launch/' + encodeURIComponent(id) + '/signin').then(j) as Promise<{ signin: CloudLaunchSignin }>,
  // The gateway resolves the stack from the tag but needs the launch's AWS
  // coordinates: a crew created under a non-default profile/region is invisible
  // to the default ones, so omitting them makes stop/start/destroy fail. destroy
  // also needs instance_id to drop the local Instances registration, otherwise
  // the crew keeps appearing in the list after its box is gone.
  cloudStop: (tag: string, coords?: CloudCoords) =>
    post('/api/cloud/' + encodeURIComponent(tag) + '/stop' + cloudQuery(coords)).then(j) as Promise<{ ok?: boolean }>,
  cloudStart: (tag: string, coords?: CloudCoords) =>
    post('/api/cloud/' + encodeURIComponent(tag) + '/start' + cloudQuery(coords)).then(j) as Promise<{ ok?: boolean }>,
  cloudDestroy: (tag: string, coords?: CloudCoords) =>
    del('/api/cloud/' + encodeURIComponent(tag) + cloudQuery(coords)).then(j) as Promise<{ ok?: boolean; unregistered?: boolean; source_removed?: boolean }>,
  // Memory
  memoryPreferences: () => fetch('/api/memory/preferences').then(j),
  saveMemoryPreferences: (content: string) => put('/api/memory/preferences', { content }),
  memoryProjects: () => fetch('/api/memory/projects').then(j),
  saveMemoryProjects: (content: string) => put('/api/memory/projects', { content }),
  memoryHistory: () => fetch('/api/memory/history').then(j),
  saveMemoryHistory: (content: string) => put('/api/memory/history', { content }),
  memorySettings: () => fetch('/api/memory/settings').then(j),
  saveMemorySettings: (s: {history_idle_hours?: number; history_max_days?: number}) => put('/api/memory/settings', s),
  // Vector memory
  vectorSemantic: () => fetch('/api/memory/semantic').then(j),
  vectorSemanticWrite: (key: string, value: string) => put('/api/memory/semantic', { key, value, source: 'user_explicit' }).then(j),
  vectorSemanticDelete: (key: string) => del('/api/memory/semantic/' + encodeURIComponent(key)),
  vectorEpisodic: (limit = 50, offset = 0, tags?: string) => fetch('/api/memory/episodic?limit=' + limit + '&offset=' + offset + (tags ? '&tags=' + encodeURIComponent(tags) : '')).then(j),
  vectorEpisodicSearch: (q: string, tags?: string) => fetch('/api/memory/episodic/search?q=' + encodeURIComponent(q) + (tags ? '&tags=' + encodeURIComponent(tags) : '')).then(j),
  vectorEpisodicDelete: (id: string) => del('/api/memory/episodic/' + encodeURIComponent(id)),
  vectorStats: () => fetch('/api/memory/stats').then(j),
  vectorEvents: (limit = 50, offset = 0) => fetch('/api/memory/events?limit=' + limit + '&offset=' + offset).then(j),
  vectorEmbeddingStatus: () => fetch('/api/memory/embedding-status').then(j),
  vectorEnableEmbeddings: () => post('/api/memory/enable-embeddings').then(j),
  vectorValidateEmbedModel: (path: string) =>
    post('/api/memory/embedding-model', { path, validate_only: true }).then(j),
  vectorApplyEmbedModel: (path: string) =>
    post('/api/memory/embedding-model', { path }).then(j),
  vectorDisableEmbeddings: () => post('/api/memory/disable-embeddings').then(j),
  vectorImport: (data: object) => post('/api/memory/import', data).then(j),
  vectorContextPreview: (query?: string) => fetch('/api/memory/context-preview' + (query ? '?q=' + encodeURIComponent(query) : '')).then(j),
  memoryGraph: () => fetch('/api/memory/graph').then(j),
  consolidateMemory: (key: string, includeHistory: boolean) => post('/api/memory/consolidate', { key, include_history: includeHistory }).then(j),
  restartSessions: () =>
    post('/api/sessions/restart').then(j) as Promise<{
      ok: boolean
      sessions_reset: number
      mcp_synced: number
      /** false when the MCP reconcile FAILED before the restart: sessions did
       *  restart, but against a config that may not match the sources. */
      mcp_sync_ok: boolean
    }>,
  sessionsContext: () => fetch('/api/sessions/context').then(j),
  sessionsMemory: () => fetch('/api/sessions/memory').then(j) as Promise<{
    sessions: {
      key: string; title: string; slot_key: string; untitled: boolean
      agent: string; pid: number | null; owns_runtime: boolean; prompts: number
      channel: string
      rss_mb: number | null; procs: number | null; mcp: number | null
      cpu_cores: number | null; uptime_s: number | null
      credits: number | null; turns: number | null
    }[]
    tasks: {
      id: string; task: string; agent: string; parent: string
      rss_mb: number; peak_rss_mb: number; cpu_cores: number
      procs: number | null; mcp: number | null
      started_at: number; shared: boolean; pid: number | null; sampled: boolean
    }[]
    totals: {
      rss_mb: number; runtimes: number; host_mb: number | null
      host_pct: number | null; rss_is_upper_bound: boolean
    }
    history: { t: number; mb: number }[]
  }>,
  sessionsUsage: () => fetch('/api/sessions/usage').then(j) as Promise<{ usage?: KiroUsagePayload }>,
  providerUsage: () => fetch('/api/usage').then(j),
  mcpProbeCache: () => fetch('/api/mcp/probe').then(j),
  // Agents
  agentsInstalled: () => fetch('/api/agents/installed').then(j),
  agentDetail: (name: string) => fetch('/api/agents/detail/' + encodeURIComponent(name)).then(j),
  agentPatch: (name: string, body: object) => fetch('/api/agents/detail/' + encodeURIComponent(name), { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(j),
  agentDelete: (name: string) => fetch('/api/agents/detail/' + encodeURIComponent(name), { method: 'DELETE' }).then(j),
  // KiroCrew agents
  // sessionKey identifies the CHAT SLOT whose project scope applies. The
  // server resolves project-local agents through
  // active_project_dir(state, session_key); with no key it falls back to
  // "the single project shared by every slot" and fails closed when two
  // slots sit on different projects, so project-scoped agents silently
  // vanish from the picker. Surfaces with no slot context (Channels,
  // Schedule) pass nothing and keep the global-only view.
  kirocrewAgents: (sessionKey?: string) =>
    fetch('/api/agents', {
      headers: sessionKey ? { 'X-Session-Key': sessionKey } : { ..._sk },
    }).then(j),
  /** The model a new session on this KiroCrew agent would run on. Empty
   *  `agent` resolves the configured default agent. */
  agentResolvedModel: (agent: string) =>
    fetch('/api/agents/resolved-model?agent=' + encodeURIComponent(agent)).then(j),
  syncKirocrewAgents: () => post('/api/agents/sync', {}).then(j),
  createKirocrewAgent: (body: object) => post('/api/agents', body).then(j),
  // Crew Members page — roster of GLOBAL crews with DM-thread binding and the
  // cheap live-status fields the backend can answer without IO (richer live
  // detail rides the already-subscribed WS `slots` frames).
  members: () => fetch('/api/members').then(j) as Promise<{ members: MemberRosterRow[] }>,
  // Idempotent get-or-create of a member's pinned DM thread. Member slots are
  // born ONLY through this route (the generic slot-create endpoint refuses
  // mode="member"), so this is also the only place a member slot key comes from.
  memberThread: (slug: string) =>
    post('/api/members/' + encodeURIComponent(slug) + '/thread').then(j) as Promise<{ slot_key: string; slug: string; member: string }>,
  // A member's recent activity pointers (real recorded signal only: session
  // participations and routing decisions). `member` is the exact crew name —
  // slugs are lossy, so the backend filters the shared log by exact name.
  // Fetched on drawer open, never polled.
  memberActivity: (slug: string, member: string) =>
    fetch(
      '/api/members/' + encodeURIComponent(slug) + '/activity?member=' + encodeURIComponent(member),
    ).then(j) as Promise<{
      slug: string
      member: string
      /** True when the display window is saturated — derived counters are floors. */
      capped: boolean
      entries: MemberActivityEntry[]
    }>,
  updateKirocrewAgent: (name: string, body: object) =>
    put('/api/agents/' + encodeURIComponent(name), body).then(j),
  deleteKirocrewAgent: (name: string) =>
    del('/api/agents/' + encodeURIComponent(name)).then(j),
  /** Stage a crew's picture on the server (a `.pending` file only — the
   *  config PUT with `avatar: {kind:'image'}` is what promotes it live,
   *  keeping the editor's Apply→Save two-step a real commit point). */
  uploadCrewAvatar: (name: string, file: Blob) => {
    const form = new FormData()
    form.append('file', file, 'avatar.png')
    return fetch('/api/agents/' + encodeURIComponent(name) + '/avatar', {
      method: 'POST',
      body: form,
    }).then(j) as Promise<{ ok?: boolean; staged?: boolean; token?: string; error?: string }>
  },
  models: () => fetch('/api/models').then(j),
  effortLevels: (slot?: string) =>
    fetch('/api/effort-levels' + (slot ? '?slot=' + encodeURIComponent(slot) : '')).then(j) as Promise<string[]>,
  // Bounded HERE, not per initiator: react-query dedupes on the key, so the
  // weakest initiator would otherwise decide whether the promise is bounded.
  slashCommands: (signal?: AbortSignal) =>
    withDeadline(SLASH_COMMANDS_TIMEOUT_MS, signal, s =>
      fetch('/api/slash-commands', { signal: s }).then(j)),
  chatSlotAgent: (slot: string, agent: string) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/agent', { agent }).then(j) as Promise<{ ok?: boolean; agent?: string; workspace?: string }>,
  chatSlotModel: (slot: string, model: string) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/model', { model }).then(j) as Promise<{ ok?: boolean; model?: string }>,
  /** This slot's auto-compact threshold override (null = follows the global). */
  chatSlotAutocompact: (slot: string) =>
    fetch('/api/chat/slots/' + encodeURIComponent(slot) + '/autocompact').then(j) as Promise<{ pct: number | null; global_pct: number; min: number; max: number }>,
  /** Set (number) or clear (null) this slot's auto-compact threshold override. */
  setChatSlotAutocompact: (slot: string, pct: number | null) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/autocompact', { pct }).then(j) as Promise<{ ok?: boolean; pct: number | null; global_pct: number }>,
  chatSlotsModel: (model: string, skip_running: boolean) =>
    post('/api/chat/slots/model', { model, skip_running }).then(j) as Promise<{ ok: boolean; model: string; switched: string[]; skipped_running: string[]; unchanged: string[]; failed: string[] }>,
  chatSlotReasoningEffort: (slot: string, reasoning_effort: string) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/reasoning-effort', { reasoning_effort }).then(j) as Promise<{ ok?: boolean; reasoning_effort?: string; deferred?: boolean }>,
  chatSlotWorkspace: (slot: string, workspace: string) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/workspace', { workspace }).then(j),
  // Relaunch the slot's agent process in place (fresh agent spec, env, and MCP
  // servers; conversation preserved). 409 while a turn is in flight.
  chatSlotReload: (slot: string) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/reload', {}).then(j) as Promise<{ ok?: boolean; error?: string }>,
  chatSlotProject: (slot: string, project: string) =>
    post('/api/chat/slots/' + encodeURIComponent(slot) + '/project', { project }).then(j) as Promise<{ ok?: boolean; project?: string }>,
  // Follow-up card: create a sibling git worktree of `repo` on a new `branch`.
  // Resolves with the created path, or rejects with the server's message
  // (branch/dir already exists, not a git repo, git unavailable).
  createWorktree: (repo: string, branch: string) =>
    post('/api/worktree/create', { repo, branch }).then(j) as Promise<{
      ok?: boolean
      path?: string
      branch?: string
      base?: string
      error?: string
    }>,
  recentProjects: () => fetch('/api/recent-projects').then(j) as Promise<{ dirs: string[] }>,
  browseDirs: (path?: string) => fetch('/api/browse-dirs' + (path ? '?path=' + encodeURIComponent(path) : '')).then(j) as Promise<{ path: string; parent: string; dirs: { name: string; path: string }[] }>,
  browseFiles: (path?: string) => fetch('/api/browse-files' + (path ? '?path=' + encodeURIComponent(path) : '')).then(j) as Promise<{ path: string; parent: string; dirs: { name: string; path: string; mtime: number }[]; files: { name: string; path: string; mtime: number }[] }>,
  projectGit: (path: string) => fetch('/api/project/git?path=' + encodeURIComponent(path)).then(j) as Promise<{ path: string; repo: boolean; repoRoot?: string; branch?: string; detached?: boolean; head?: string }>,
  projectGitStatus: (path: string) => fetch('/api/project/git/status?path=' + encodeURIComponent(path)).then(j) as Promise<{ repo: boolean; repoRoot?: string; branch?: string; ahead?: number; behind?: number; files: { path: string; status: string; staged: boolean; additions?: number; deletions?: number }[] }>,
  projectGitLog: (path: string, limit = 20) => fetch('/api/project/git/log?path=' + encodeURIComponent(path) + '&limit=' + limit).then(j) as Promise<{ repo: boolean; commits: { sha: string; message: string; author: string; date: string; isHead: boolean }[] }>,
  projectTree: (path: string) => fetch('/api/project/tree?path=' + encodeURIComponent(path)).then(j) as Promise<{ root: string; paths: string[]; repo: boolean; truncated?: boolean }>,
  workspaces: () => fetch('/api/workspaces').then(j),
  createWorkspace: (body: object) => post('/api/workspaces', body).then(j),
  updateWorkspace: (name: string, body: object) =>
    put('/api/workspaces/' + encodeURIComponent(name), body).then(j),
  deleteWorkspace: (name: string) =>
    del('/api/workspaces/' + encodeURIComponent(name)).then(j),
  // Crons
  crons: () => fetch('/api/crons').then(j),
  createCron: (body: object) => post('/api/crons', body).then(j),
  deleteCron: (id: string) => del('/api/crons/' + id).then(j),
  batchDeleteCron: (ids: string[]) => del('/api/crons', { ids }).then(j),
  updateCron: (id: string, body: object) =>
    fetch('/api/crons/' + id, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(j),
  runCron: (id: string) => post('/api/crons/' + id + '/run').then(j),
  /** Grant/revoke vault secrets, or act on an agent-requested pending grant.
   * Body: {secret_env: {...}} grants (empty object revokes), or
   * {approve_pending: true, expected_secret_env, expected_ts} /
   * {deny_pending: true}. Approval restates the displayed request; the server
   * refuses with 409 stale_request if it was replaced. Operator-only server-side. */
  cronSecretsGrant: (id: string, body: { secret_env?: Record<string, string>; approve_pending?: boolean; deny_pending?: boolean; expected_secret_env?: Record<string, string> | null; expected_ts?: number; expected_source_sha256?: string }) =>
    put('/api/crons/' + id + '/secrets', body).then(j),
  cancelCron: (id: string) => post('/api/crons/' + id + '/cancel').then(j),
  cronToChat: (id: string) => post('/api/crons/' + id + '/to-chat').then(j),
  toggleCron: (id: string, enabled: boolean) => post('/api/crons/' + id + '/enable', { enabled }).then(j),
  cronHistory: (jobId: string, offset?: number, limit?: number) => {
    const p = new URLSearchParams()
    if (offset != null) p.set('offset', String(offset))
    if (limit != null) p.set('limit', String(limit))
    const qs = p.toString()
    return fetch('/api/crons/' + jobId + '/history' + (qs ? '?' + qs : ''), { headers: { ..._sk } }).then(j)
  },
  cronRunDetail: (jobId: string, runId: string) => fetch('/api/crons/' + jobId + '/history/' + encodeURIComponent(runId), { headers: { ..._sk } }).then(j),
  cronScript: (jobId: string) => fetch('/api/crons/' + jobId + '/script', { headers: { ..._sk } }).then(j),
  /** Vault secret NAMES (values are never exposed). Same endpoint the Settings
   * Secrets panel reads. */
  secretsList: () => fetch('/api/secrets').then(j),
  ackCron: (id: string, summary: string, ts?: string) => post('/api/crons/' + id + '/ack', { summary, ts }).then(j),
  cronHistoryAll: (opts?: { offset?: number; limit?: number; jobId?: string }) => {
    const p = new URLSearchParams()
    if (opts?.offset != null) p.set('offset', String(opts.offset))
    if (opts?.limit != null) p.set('limit', String(opts.limit))
    if (opts?.jobId) p.set('job_id', opts.jobId)
    return fetch('/api/crons/history' + (p.toString() ? '?' + p : ''), { headers: { ..._sk } }).then(j)
  },

  // Cron Folders
  cronFolders: () => fetch('/api/cron-folders').then(j),
  createCronFolder: (name: string) => post('/api/cron-folders', { name }).then(j),
  updateCronFolder: (id: string, body: { name?: string }) =>
    fetch('/api/cron-folders/' + id, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(j),
  deleteCronFolder: (id: string) => del('/api/cron-folders/' + id).then(j),

  // Lessons
  lessons: () => fetch('/api/lessons').then(j),
  createLesson: (rule: string, category: string) =>
    post('/api/lessons', { rule, category }).then(j) as Promise<{
      ok: boolean
      outcome: 'inserted' | 'enriched' | 'unchanged' | 'deduped' | 'refused'
      reason: string
    }>,
  deleteLesson: (rule: string) => del('/api/lessons', { rule }).then(j),
  // Hooks
  hooks: () => fetch('/api/hooks').then(j),
  kiroHooks: () => fetch('/api/kiro-hooks').then(j),
  createHook: (body: object) => post('/api/hooks', body).then(j),
  updateHook: (id: string, body: object) => put('/api/hooks/' + id, body).then(j),
  deleteHook: (id: string) => del('/api/hooks/' + id).then(j),
  toggleHook: (id: string) => post('/api/hooks/' + id + '/toggle', {}).then(j),
  testHook: (id: string, context?: string) => post('/api/hooks/' + id + '/test', { context: context || 'test' }).then(j),
  // Inbound webhooks (POST /api/hooks/agent) — token store, registered
  // contexts, run history. All dashboard-authed; the webhook bearer token is
  // never used from the browser.
  webhooks: () => fetch('/api/webhooks').then(j),
  // `require_signature` defaults to true server-side; a destination is required
  // for every newly created first-class source.
  createWebhookToken: (label: string, requireSignature = true, agent = '') =>
    post('/api/webhooks/tokens', {
      label,
      require_signature: requireSignature,
      agent,
    }).then(j),
  updateWebhookToken: (
    id: string,
    patch: { agent?: string; enabled?: boolean; label?: string },
  ) => fetch('/api/webhooks/tokens/' + encodeURIComponent(id), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  }).then(j),
  deleteWebhookToken: (id: string) => del('/api/webhooks/tokens/' + encodeURIComponent(id)).then(j),
  deleteWebhookContext: (hookId: string) => del('/api/webhooks/contexts/' + encodeURIComponent(hookId)).then(j),
  testWebhook: (message?: string, agent?: string) => post('/api/webhooks/test', { message, agent }).then(j),
  setWebhooksEnabled: (enabled: boolean) => post('/api/webhooks/switch', { enabled }).then(j),
  // Prompts (Agent SOPs)
  prompts: () => fetch('/api/prompts').then(j),
  promptDetail: (name: string, scope?: 'global' | 'local') =>
    fetch('/api/prompts/' + name.split('/').map(encodeURIComponent).join('/')
      + (scope ? '?scope=' + scope : '')).then(j),
  createPrompt: (name: string, content: string, scope: 'global' | 'local') =>
    post('/api/prompts', { name, content, scope }).then(j),
  updatePrompt: (name: string, scope: 'global' | 'local', content: string, baseHash: string) =>
    put('/api/prompts/' + encodeURIComponent(name) + '?scope=' + scope, { content, base_hash: baseHash }).then(j),
  deletePrompt: (name: string, scope: 'global' | 'local') =>
    del('/api/prompts/' + encodeURIComponent(name) + '?scope=' + scope).then(j),
  // Skills
  // sessionKey names the REAL chat slot so the server can resolve THIS chat's
  // project and include its `<project>/.kiro/skills`. Without it the shared
  // `dashboard:ui` placeholder makes the server fall back to "the one project
  // every slot shares", so workspace skills leak between chats on different
  // projects and vanish entirely when two chats disagree (#2457, #3551).
  // agent, when given, scopes the listing to that agent's own skill:// mapping;
  // an agent with no explicit mapping keeps the unfiltered listing. When the
  // mapping IS applied the server answers with the envelope
  // {skills, agent_scoped: true, agent} instead of the bare array, so the
  // picker can cue the scope (and tell "nothing mapped" from "nothing exists").
  // Consume through lib/skillsPayload.ts unwrapSkills() rather than assuming an array.
  // Bounded HERE, not per initiator: react-query dedupes on the key, so the
  // weakest initiator would otherwise decide whether the promise is bounded.
  skills: (sessionKey?: string, agent?: string, signal?: AbortSignal) =>
    withDeadline(SKILLS_TIMEOUT_MS, signal, s =>
      get('/api/skills' + (agent ? '?agent=' + encodeURIComponent(agent) : ''),
          sessionKey, s).then(j)),
  /** Project-skills trust: this chat's grant state plus every stored grant. */
  skillTrust: (sessionKey?: string) => get('/api/skills/-/trust', sessionKey).then(j),
  /** Grant trust to THIS chat's project. The server takes the directory from
   *  the slot, not from us — a caller-supplied path would let any caller
   *  consent for a directory the operator never opened. */
  // expectedKey is the canonical identity returned by the consent snapshot. It
  // is a confirmation, not a selector: the server still derives the directory
  // from the requesting slot and refuses when the current key differs.
  grantSkillTrust: (sessionKey: string | undefined, expectedKey: string) =>
    post('/api/skills/-/trust', { expected_key: expectedKey }, sessionKey).then(j),
  /** Revoke a grant. `path` is optional — omitted revokes this chat's project. */
  revokeSkillTrust: (path?: string, sessionKey?: string) =>
    del('/api/skills/-/trust' + (path ? '?path=' + encodeURIComponent(path) : ''),
        undefined, sessionKey).then(j),
  skill: (name: string) => fetch('/api/skills/' + name.split('/').map(encodeURIComponent).join('/')).then(j),
  /** List the file tree under a skill's directory.  The ``/-/`` separator
   *  disambiguates from a nested skill whose last segment is ``tree``. */
  skillTree: (name: string) => fetch('/api/skills/' + name.split('/').map(encodeURIComponent).join('/') + '/-/tree').then(j),
  /** Read a single file inside a skill's directory by relative path. */
  skillFile: (name: string, relPath: string) =>
    fetch('/api/skills/' + name.split('/').map(encodeURIComponent).join('/') +
          '/-/file?path=' + encodeURIComponent(relPath)).then(j),
  createSkill: (name: string, content: string) => post('/api/skills', { name, content }).then(j),
  updateSkill: (name: string, content: string) => put('/api/skills/' + name.split('/').map(encodeURIComponent).join('/'), { content }).then(j),
  deleteSkill: (name: string) => del('/api/skills/' + name.split('/').map(encodeURIComponent).join('/')).then(j),

  // Steering (Kiro steering files — ~/.kiro/steering + <project>/.kiro/steering)
  // sessionKey names the CHAT SLOT whose project `workspace/` keys resolve
  // against, exactly as it does for kirocrewAgents. Without it the server can
  // only fall back to "the single project every slot shares" and fails closed
  // with two chats on different projects, so project steering silently
  // disappears from a tab that has no way to say why. All five verbs take it:
  // a key created under one project must stay readable, editable and deletable
  // from the same page load.
  steeringFiles: (sessionKey?: string) =>
    fetch('/api/steering', { headers: sessionKey ? { 'X-Session-Key': sessionKey } : { ..._sk } }).then(j),
  steeringFile: (key: string, sessionKey?: string) =>
    fetch('/api/steering/' + key.split('/').map(encodeURIComponent).join('/'), {
      headers: sessionKey ? { 'X-Session-Key': sessionKey } : { ..._sk },
    }).then(j),
  // projectKey is the `project_key` the listing returned: a workspace write
  // echoes it so the server can refuse (409) when the chat slot has since been
  // re-pointed at a different project. The session key names the slot, and the
  // slot is precisely what can move, so it cannot close this on its own.
  createSteering: (name: string, content: string, source?: string, sessionKey?: string, projectKey?: string) =>
    post('/api/steering', { name, content, source }, sessionKey, projectHeader(projectKey)).then(j),
  /** Save a steering file. `declaration` optionally rewrites its front matter
   *  (mode and pattern) SERVER-side — an empty string on a field removes that
   *  key. The editor never splices YAML into its own
   *  textarea: the body is the user's document, and the server's writer
   *  preserves it byte for byte. */
  updateSteering: (
    key: string,
    content: string,
    sessionKey?: string,
    projectKey?: string,
    declaration?: { inclusion?: string; file_match_pattern?: string },
  ) =>
    put('/api/steering/' + key.split('/').map(encodeURIComponent).join('/'), { content, ...(declaration ?? {}) }, sessionKey, projectHeader(projectKey)).then(j),
  deleteSteering: (key: string, sessionKey?: string, projectKey?: string) =>
    del('/api/steering/' + key.split('/').map(encodeURIComponent).join('/'), undefined, sessionKey, projectHeader(projectKey)).then(j),

  // Auto-skill pending queue + lifecycle pin
  skillsPending: () => fetch('/api/skills/-/pending').then(j),
  skillPendingDetail: (slug: string) => fetch('/api/skills/-/pending/' + encodeURIComponent(slug)).then(j),
  approvePendingSkill: (slug: string) => post('/api/skills/-/pending/' + encodeURIComponent(slug) + '/approve', {}).then(j),
  dismissPendingSkill: (slug: string) => post('/api/skills/-/pending/' + encodeURIComponent(slug) + '/dismiss', {}).then(j),
  dismissAllPendingSkills: (slugs: string[]) => post('/api/skills/-/pending/-/dismiss-all', { slugs }).then(j),
  pinSkill: (name: string, pinned: boolean) => post('/api/skills/-/pin', { name, pinned }).then(j),
  /** Opt a skill in/out of full-body injection when its triggers match.
   *  `inject: false` reduces the skill to a one-line pointer on a match. */
  setSkillInjectOnTrigger: (name: string, inject: boolean) =>
    post('/api/skills/-/inject-on-trigger', { name, inject }).then(j),
  /** Context budget: cost data for the skill control plane. */
  skillsBudget: () => get('/api/skills/-/budget').then(j) as Promise<import('../types').SkillBudgetResponse>,
  /** Multi-provider skill discovery (skills.sh, etc.) */
  discoverSkills: (query: string, opts?: { provider?: string; limit?: number }) =>
    get(`/api/skills/-/discover?q=${encodeURIComponent(query)}${opts?.provider ? `&provider=${opts.provider}` : ''}${opts?.limit ? `&limit=${opts.limit}` : ''}`).then(j) as Promise<import('../types').DiscoverSkillsResponse>,
  /** Preview a skill's description, full SKILL.md, and bundle manifest before installing */
  previewDiscoveredSkill: (provider: string, id: string) =>
    get(`/api/skills/-/discover/preview?provider=${encodeURIComponent(provider)}&id=${encodeURIComponent(id)}`).then(j) as Promise<import('../types').DiscoverSkillPreview>,
  /** Install a skill from a provider by ID. Throws ApiError(409) when already installed and overwrite is not set. */
  installDiscoveredSkill: (provider: string, skillId: string, opts?: { name?: string; overwrite?: boolean }) =>
    post('/api/skills/-/discover/install', { provider, skill_id: skillId, name: opts?.name, overwrite: opts?.overwrite }).then(j) as Promise<import('../types').DiscoverInstallResult>,
  // MCP
  mcpServers: () => fetch('/api/mcp').then(j),
  mcpGlobalScopes: () => fetch('/api/mcp/scopes').then(j),
  /** Multi-provider MCP server discovery (official registry, plus the
   *  edition capability provider when one is installed). A query
   *  shorter than 2 chars returns {results: [], providers: [...]} without
   *  hitting any provider — a cheap availability probe. */
  mcpDiscover: (query: string, opts?: { provider?: string; limit?: number }) =>
    get(`/api/mcp/discover?q=${encodeURIComponent(query)}${opts?.provider ? `&provider=${opts.provider}` : ''}${opts?.limit ? `&limit=${opts.limit}` : ''}`).then(j) as Promise<import('../types').McpDiscoverResponse>,
  /** Full description + install-plan preview for one discovered server. */
  mcpDiscoverDetail: (provider: string, id: string) =>
    get(`/api/mcp/discover/detail?provider=${encodeURIComponent(provider)}&id=${encodeURIComponent(id)}`).then(j) as Promise<import('../types').McpDiscoverDetail>,
  /** Install a discovered MCP server. Throws ApiError(409) on name collision. */
  mcpDiscoverInstall: (provider: string, id: string) =>
    post('/api/mcp/discover/install', { provider, id }).then(j) as Promise<import('../types').McpDiscoverInstallResult>,

  mcpCustomAdd: (servers: Record<string, import('../types').McpCustomSpec>, enable: boolean) =>
    post('/api/mcp/custom', { servers, enable }).then(j) as Promise<{ ok: boolean; added: string[]; enabled: boolean }>,

  mcpCustomGet: (name: string) =>
    get(`/api/mcp/custom/${encodeURIComponent(name)}`).then(j) as Promise<import('../types').McpCustomSpecResponse>,

  mcpCustomUpdate: (name: string, spec: import('../types').McpCustomSpec) =>
    put(`/api/mcp/custom/${encodeURIComponent(name)}`, { spec }).then(j) as Promise<{ ok: boolean; name: string }>,
  mcpActive: (agent?: string) => fetch('/api/mcp/active' + (agent ? `?agent=${encodeURIComponent(agent)}` : '')).then(j),
  mcpProbe: () => post('/api/mcp/probe').then(j),
  mcpResetProbeFailures: (name: string) =>
    post('/api/mcp/quarantine/clear', { name }).then(j) as Promise<{ ok: boolean; name: string; released: boolean }>,
  mcpSync: () => post('/api/mcp/sync').then(j),
  mcpApply: (changes: McpApplyChange[]) =>
    post('/api/mcp/apply', { changes }).then(j),
  mcpToggle: (name: string, enabled: boolean) => post('/api/mcp/toggle', { name, enabled }).then(j),
  mcpToggleTool: (server: string, tool: string, enabled: boolean) => post('/api/mcp/toggle-tool', { server, tool, enabled }).then(j),
  mcpToggleAll: (enabled: boolean) => post('/api/mcp/toggle-all', { enabled }).then(j),
  mcpRemove: (name: string) => post('/api/mcp/remove', { name }).then(j),
  mcpOAuthRelay: (server: string, redirectUrl: string) =>
    post('/api/mcp/oauth/relay', { server, redirect_url: redirectUrl }).then(j) as Promise<{ ok: boolean }>,
  // Connections approval-URL mint. POST starts one; GET is the card's feed for it.
  connectionsMint: (slug: string) =>
    post('/api/connections/mint', { slug }).then(j) as Promise<{ ok: boolean; slug: string; state: string; token: string }>,
  connectionsMintState: (slug: string) =>
    fetch(`/api/connections/mint?slug=${encodeURIComponent(slug)}`).then(j) as Promise<ConnectionMintState>,
  // Warm every mintable provider's URL in one activation, so a later Connect
  // serves a URL the warm table already holds instead of paying a cold spawn.
  // Deliberately BODYLESS: what is mintable is a fact about the user's registry
  // and grant state, never a caller's choice, and the bound on what may be
  // spawned stays on the server's side of the wire. `preminting` names the
  // providers warming was STARTED for, which is why it can answer before any of
  // them holds a URL — a card's verdict remains its mint state, never this.
  // Owner-gated, so a non-owner session rejects (403); the caller is expected to
  // treat that as "no warm table", not as an error worth showing.
  connectionsPremint: () =>
    post('/api/connections/premint').then(j) as Promise<{ ok: boolean; preminting: string[] }>,
  // Authorization verdict + first-connect time per visible provider. Additive to
  // the mint feed above; never mints.
  connectionsStatus: () =>
    fetch('/api/connections/status').then(j) as Promise<{ schema_version: number; connections: ConnectionStatus[] }>,
  // Promptless authenticated enumeration through kiro-cli. The runtime owns
  // bearer injection and provider tools/list; this receives only a verdict and count.
  connectionsTest: (slug: string) =>
    post('/api/connections/test', { slug }).then(j) as Promise<ConnectionTestResult>,
  // Dispose an in-flight mint (process, listener, spec). Does NOT touch the MCP
  // config entry — the card owns that. `token` fences a sibling tab's row.
  connectionsCancel: (slug: string, token?: string) =>
    post('/api/connections/cancel', token ? { slug, token } : { slug }).then(j) as Promise<{ ok: boolean; slug: string; dropped: boolean }>,
  // Undo a connection on THIS machine: disposes any in-flight mint, deletes the
  // runtime's stored grant artifacts when they are ours alone, and removes the MCP
  // entry. `grantRemoved` and `grantSurviving` are separate answers because the
  // artifacts are a pair and either half can fail alone; `entryRemoved` is false
  // when the entry configured under this slug points at a different endpoint (so it
  // is not ours to delete); `grantSharedWith` names the other entries using the same
  // endpoint, which is why the grant was deliberately kept. `grantCensusUnreadable`
  // names the sources the census could not read, so the card can say WHICH file to
  // repair -- optional because the other half of `grantCensusIncomplete` (an entry
  // whose URL could not be compared) names no file, and a gateway predating the
  // field sends none.
  connectionsDisconnect: (slug: string) =>
    post('/api/connections/disconnect', { slug }).then(j) as Promise<{ ok: boolean; grantRemoved: boolean; grantSurviving: string[]; entryRemoved: boolean; grantSharedWith: string[]; grantCensusIncomplete: boolean; grantCensusUnreadable?: string[] }>,
  // MCP Gateway (shared pool)
  mcpGatewayStatus: () => fetch('/api/mcp-gateway/status').then(j) as Promise<{ enabled: boolean; stub: string[]; stub_count: number; running: boolean; ping_ok: boolean; supported: boolean }>,
  mcpGatewayEnable: (enabled: boolean) => post('/api/mcp-gateway/enable', { enabled }).then(j) as Promise<{ ok: boolean; enabled: boolean; running: boolean; ping_ok: boolean }>,
  mcpGatewayMetrics: () => fetch('/api/mcp-gateway/metrics').then(j) as Promise<{ running: boolean; size?: number; max_backends?: number; backends: { server: string; agent: string; pid: number | null; sessions: number; idle_s: number; rss_kb: number }[]; warm_pool_hits?: number; warm_pool_misses?: number; warm_pool_hit_rate_pct?: number }>,
  mcpGatewayServers: () => fetch('/api/mcp-gateway/servers').then(j) as Promise<{ servers: McpManagedServer[] }>,
  mcpGatewaySetStub: (name: string, stub: boolean) => post('/api/mcp-gateway/servers/stub', { name, stub }).then(j) as Promise<{ ok: boolean; name: string; stub: boolean; enabled?: boolean; applied?: boolean; restart_required?: boolean; stub_servers?: string[] }>,
  mcpResolveRefresh: () => post('/api/mcp-gateway/resolve-refresh', {}).then(j) as Promise<{ ok: boolean; reason?: string; resolved: Record<string, 'ready' | 'unresolved' | 'error'>; ready?: string[] }>,
  // Starting a measurement pass returns immediately: it spawns two processes per
  // unmeasured server, so the answer arrives through the progress read, not here.
  mcpMeasureStart: () => post('/api/mcp/measure', {}).then(j) as Promise<McpMeasureProgress>,
  mcpMeasureProgress: () => fetch('/api/mcp/measure').then(j) as Promise<McpMeasureProgress>,
  // Batch form of the above -- one config write for the whole set, so "toggle
  // all" can't land the allowlist half-flipped. Like the single form it records
  // rather than applies, and answers `restart_required`.
  //
  // `resolveEligibility` hands the decision to the server: it re-reads the sharing
  // switch and each server's verdict inside the same lock hold that writes them, so
  // the policy and the write cannot disagree. The response then reports `stubbed`
  // and `skipped` rather than echoing the request, because the two differ by design.
  mcpGatewaySetStubMany: (names: string[], stub: boolean, resolveEligibility?: boolean) => post('/api/mcp-gateway/servers/stub', resolveEligibility ? { names, stub, resolve_eligibility: true } : { names, stub }).then(j) as Promise<{ ok: boolean; names: string[]; stub: boolean; stubbed?: string[]; skipped?: Array<{ name: string; reason: string }>; sharing_on?: boolean; applied?: boolean; restart_required?: boolean; stub_servers?: string[] }>,
  // Agent config
  agentConfig: () => fetch('/api/agent/config').then(j),
  saveAgentConfig: (config: object) => put('/api/agent/config', { config }).then(j),
  defaultAgent: () => fetch('/api/config/default-agent').then(j),
  setDefaultAgent: (agent: string) => put('/api/config/default-agent', { agent }).then(j),
  kirocrewConfig: () => fetch('/api/config/kirocrew').then(j),
  saveKirocrewConfig: (agent: object) => put('/api/config/kirocrew', { agent }).then(j) as Promise<{ ok?: boolean; restart_required?: boolean; error?: string }>,
  patchConfig: (path: string, value: unknown) => fetch('/api/config/kirocrew', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, value }) }).then(j),
  providerTest: (body: { url: string; api_key?: string; format?: string; use_stored?: boolean }) => post('/api/provider/test', body).then(j),
  providerStatus: () => fetch('/api/provider/status').then(j),
  // Owner-only, and absent (404) on an older gateway. Both of those reach the
  // caller as a rejection, which is the intended signal: "no probe information",
  // to be treated as fail-open rather than as a verdict.
  acpBackends: () => fetch('/api/acp-backends').then(j) as Promise<{ backends: AcpBackendProbe[] }>,
  // Optional integrations — backend endpoints are graceful no-ops on a public
  // install (AIM / kiro usage are stubbed). Kept so the UI compiles and
  // degrades gracefully (panels render empty when the feature is absent).
  kiroUsage: () => fetch('/api/usage/kiro').then(j),
  capabilityMcpList: () => fetch('/api/capability/mcp').then(j),
  capabilityMcpInstall: (serverId: string) => post('/api/capability/mcp/install', { server_id: serverId }).then(j),
  capabilityMcpUninstall: (serverId: string) => post('/api/capability/mcp/uninstall', { server_id: serverId }).then(j),
  capabilitySkillsList: () => fetch('/api/capability/skills').then(j),
  capabilitySkillsInstall: (pkg: string) => post('/api/capability/skills/install', { package: pkg }).then(j),
  capabilitySkillsUninstall: (pkg: string) => post('/api/capability/skills/uninstall', { package: pkg }).then(j),
  capabilityAgentsList: () => fetch('/api/capability/agents').then(j),
  capabilityAgentsInstall: (pkg: string) => post('/api/capability/agents/install', { package: pkg }).then(j),
  capabilityAgentsUninstall: (pkg: string) => post('/api/capability/agents/uninstall', { package: pkg }).then(j),
  // Plugin packages (agent-client integrations). The response pairs the installed
  // rows with `out_of_sync` — packages installed as agents but missing their
  // plugin counterpart — so the UI can offer a one-click reconcile.
  capabilityPluginsList: () => fetch('/api/capability/plugins').then(j),
  capabilityPluginsSync: () => post('/api/capability/plugins/sync', {}).then(j),
  capabilityMcpRegistry: () => fetch('/api/capability/mcp/registry').then(j),
  // STT
  sttConfig: () => fetch('/api/config/stt').then(j),
  saveSttConfig: (body: {
    enabled?: boolean
    provider?: string
    model?: string
    streaming?: boolean
    silence_ms?: number
    partial_interval_ms?: number
    endpointing?: boolean
    dictation_panel?: boolean
    transcribe_region?: string
    transcribe_profile?: string
    language_code?: string
  }) => put('/api/config/stt', body).then(j),
  // Recogniser availability plus the model catalog and the progress of any
  // download in flight. Separate from `sttConfig` because it is POLLED while a
  // model is being fetched, and polling the config endpoint would re-read and
  // re-probe configuration several times a second.
  sttStatus: () => fetch('/api/stt/status').then(j),
  // Fetch a model now, so the cost is paid at a moment the user chose rather
  // than in the middle of their first dictation. Returns as soon as the transfer
  // is under way; progress is read from `sttStatus`.
  sttPrepare: (model: string) => post('/api/stt/prepare', { model }).then(j),
  // Fetch the audio decoder (ffmpeg) into the gateway's digest-verified store,
  // for a source install whose OS ships no ffmpeg package. Same 202-then-poll
  // shape as `sttPrepare`; progress arrives on `sttStatus().ffmpeg.download`.
  sttFfmpegDownload: () => post('/api/stt/ffmpeg/download', {}).then(j),
  // Load the model and run one throwaway decode so the first real utterance does
  // not pay for the graph allocation. Fire-and-forget at every call site: a
  // failure only costs the latency it was meant to hide.
  sttPrewarm: () => post('/api/stt/prewarm', {}).then(j),
  sttTranscribe: (blob: Blob, ext = 'webm') => {
    const fd = new FormData()
    fd.append('audio', blob, `recording.${ext}`)
    return fetch('/api/stt/transcribe', { method: 'POST', body: fd }).then(j)
  },
  // Chat
  pullRequestSource: (url: string, refresh = false) => post('/api/source/pull-request', { url, refresh }).then(j) as Promise<PullRequestSource>,
  pullRequestChecks: (url: string) => post('/api/source/pull-request/checks', { url }).then(j) as Promise<{ checks: PullRequestCheck[] }>,
  pullRequestStatuses: (urls: string[]) => post('/api/source/pull-request/status', { urls }).then(j) as Promise<PullRequestStatusBatch>,
  resolvePullRequestThread: (url: string, threadId: string) => post('/api/source/pull-request/resolve', { url, threadId }).then(j) as Promise<{ resolved: boolean }>,
  unresolvePullRequestThread: (url: string, threadId: string) => post('/api/source/pull-request/unresolve', { url, threadId }).then(j) as Promise<{ resolved: boolean }>,
  /** Reply into an existing review thread. Owner-only on the gateway. */
  replyToPullRequestThread: (url: string, threadId: string, body: string) => post('/api/source/pull-request/reply', { url, threadId, body }).then(j) as Promise<{ posted: boolean }>,
  /** Top-level comment on the pull request conversation. */
  commentOnPullRequest: (url: string, body: string) => post('/api/source/pull-request/comment', { url, body }).then(j) as Promise<{ posted: boolean }>,
  enablePullRequestAutoMerge: (url: string, confirmImmediateMerge = false) => post('/api/source/pull-request/auto-merge', { url, confirmImmediateMerge }).then(j) as Promise<{ autoMerge: boolean; mergeMethod: string }>,
  markPullRequestReady: (url: string) => post('/api/source/pull-request/ready', { url }).then(j) as Promise<{ ready: boolean }>,
  pullRequestPendingReview: (url: string) => post('/api/source/pull-request/pending-review', { url }).then(j) as Promise<{ reviewId: string; body: string; comments?: { path: string; line: number | null; body: string }[]; commitId: string; headSha: string; stale: boolean; contentRedacted: boolean; autoMergeArmed: boolean; contentDigest: string; staleDismissalEnabled: boolean }>,
  submitPullRequestReview: (url: string, reviewId: string, event: 'APPROVE' | 'REQUEST_CHANGES' | 'COMMENT', contentDigest: string) =>
    post('/api/source/pull-request/submit-review', { url, reviewId, event, contentDigest }).then(j) as Promise<{ submitted: boolean; event: string }>,
  // Issue sources. `refresh` bypasses the server's cached payload; the panel
  // never polls, so a refresh is always an explicit user action.
  fetchIssueSource: (url: string, refresh = false) => post('/api/source/issue', { url, refresh }).then(j) as Promise<IssueSource>,
  /** Top contributors to an app's source repo (GitHub only). Owner-gated. */
  appContributors: (url: string, refresh = false) => post('/api/source/contributors', { url, refresh }).then(j) as Promise<{ contributors: AppContributor[] }>,
  chatSlots: () => fetch('/api/chat/slots').then(j),
  /** All goal loops across sessions. Returns `{enabled:false, loops:[]}` when
   *  the auto-nudge feature flag is off, so callers need no flag check. */
  autonudgeList: (): Promise<{ enabled: boolean; loops: { slot_key: string; active?: boolean; cycle_count?: number; max_cycles?: number }[] }> =>
    fetch('/api/autonudge').then(j),
  /** Every pull request / issue link a session carries — the unbudgeted read
   *  behind the sidebar's expandable "+N" overflow chip. The slots payload caps
   *  chips per kind, so the links behind that chip are not on the client until
   *  this is called. */
  chatSlotSourceLinks: (slot: string): Promise<{ links: NonNullable<ChatSlot['source_links']>; total: number }> =>
    fetch('/api/chat/slots/' + encodeURIComponent(slot) + '/source-links').then(j),
  chatSlotDetail: (slot: string, limit?: number, before?: number, signal?: AbortSignal) => {
    const p = new URLSearchParams()
    if (limit) p.set('limit', String(limit))
    if (before !== undefined) p.set('before', String(before))
    return fetch('/api/chat/slots/' + encodeURIComponent(slot) + '?' + p, { signal }).then(j)
  },
  /** Create a chat slot. `instance_id` binds the new session to a connected crew
   *  for EXECUTION: it lives in this machine's list and history, and its turns run
   *  over there. The backend opens the peer's slot first, so a peer that is
   *  disconnected or on a different version fails the create rather than yielding
   *  a session that cannot send. */
  createChatSlot: (name?: string, agent?: string, model?: string, mode?: string, memory_mode?: string, title?: string, clean_mode?: boolean, artifact?: string, folder_id?: string, instance_id?: string) => post('/api/chat/slots', { ...(name ? { name } : {}), ...(agent ? { agent } : {}), ...(model ? { model } : {}), ...(mode ? { mode } : {}), ...(memory_mode ? { memory_mode } : {}), ...(title ? { title } : {}), ...(clean_mode !== undefined ? { clean_mode } : {}), ...(artifact ? { artifact } : {}), ...(folder_id ? { folder_id } : {}), ...(instance_id ? { instance_id } : {}) }).then(j) as Promise<ChatSlot>,
  /** Inject silent background context into a slot — consumed on the next user
   * message. Used by the artifact companion chat to name the bound artifact so
   * the user's first message needs no slug boilerplate. */
  chatSlotContext: (slot: string, content: string, opts?: { source?: string; ephemeral?: boolean; maxAge?: number }) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/context', { content, ...(opts?.source ? { source: opts.source } : {}), ...(opts?.ephemeral !== undefined ? { ephemeral: opts.ephemeral } : {}), ...(opts?.maxAge !== undefined ? { maxAge: opts.maxAge } : {}) }).then(j),
  deleteChatSlot: (slot: string) => del('/api/chat/slots/' + encodeURIComponent(slot)).then(j),
  cleanupSessions: (maxInactiveDays: number, activeSlot?: string, dryRun?: boolean) => post('/api/chat/slots/cleanup', { max_inactive_days: maxInactiveDays, active_slot: activeSlot || '', dry_run: !!dryRun }).then(j) as Promise<{ ok: boolean; archived: number; keys: string[]; failed: string[]; dry_run?: boolean; count?: number; active_is_stale?: boolean }>,
  stopChatSlot: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/stop').then(j),
  stopChatSlotForce: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/stop?force=true').then(j),
  cancelQueuedMessage: (slot: string, queueId: string) => del('/api/chat/slots/' + encodeURIComponent(slot) + '/queue/' + encodeURIComponent(queueId)).then(j),
  editQueuedMessage: (slot: string, queueId: string, content: string) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/queue/' + encodeURIComponent(queueId), { content }).then(j),
  reorderQueuedMessages: (slot: string, order: string[]) => put('/api/chat/slots/' + encodeURIComponent(slot) + '/queue/order', { order }).then(j),
  interruptSlot: (slot: string, queueId?: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/interrupt', queueId ? { queue_id: queueId } : {}).then(j),
  /** Ask the sleeping `wait` tool to return early. Cooperative, not a stop:
   *  the turn continues with a normal tool result. `waitId` must name the sleep
   *  currently in flight — the backend answers 409 for a stale one, which is how
   *  a click on a leftover countdown is rejected rather than ending a later wait. */
  endWait: (slot: string, waitId: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/end-wait', { wait_id: waitId }).then(j),
  approveChatSlot: (slot: string, action: string, extra?: Record<string, string>) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/approve', { action, ...extra }).then(j),
  planAction: (slot: string, action: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/plan-action', { action }).then(j),
  resumeChatSlot: (key: string, title?: string) => post('/api/chat/slots/' + encodeURIComponent(key) + '/resume', { name: key, key, title: title || key }).then(j),
  forkChatSlot: (slot: string, atIndex?: number, prompt?: string, mode?: string, direction?: string, messageId?: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/fork', { ...(atIndex !== undefined ? { at_message_index: atIndex } : {}), ...(messageId ? { at_message_id: messageId } : {}), ...(prompt ? { prompt } : {}), ...(mode ? { mode } : {}), ...(direction ? { direction } : {}) }).then(j),
  sideOpen: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/side/open', {}).then(j) as Promise<{ ok: boolean; open: boolean; messages: number; last_run_id: string; created_at: string }>,
  sideTurn: (slot: string, question: string, opts?: { steer?: boolean }) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/side/turn', { question, ...(opts?.steer ? { steer: true } : {}) }).then(j) as Promise<{ ok: boolean; run_id?: string; messages?: number; steered?: boolean; pending?: boolean; queued?: boolean; demoted?: boolean; queue_id?: string; still_queued?: boolean; depth?: number; steer_id?: string }>,
  sideQueueCancel: (slot: string, queueId: string) => del('/api/chat/slots/' + encodeURIComponent(slot) + '/side/queue/' + encodeURIComponent(queueId), { client: TAB_ID }).then(j) as Promise<{ ok: boolean; content: string; depth: number }>,
  sideQueueEdit: (slot: string, queueId: string, content: string) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/side/queue/' + encodeURIComponent(queueId), { content }).then(j) as Promise<{ ok: boolean; depth: number }>,
  sideClose: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/side/close', {}).then(j) as Promise<{ ok: boolean; was_open: boolean }>,
  chatMode: (mode: string, slot?: string) => post('/api/chat/mode', { mode, slot: slot || '' }).then(j),
  generateTitle: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/generate-title').then(j),
  resolveNavLinks: (links: { url: string; context: string }[]) => post('/api/chat/nav/resolve-links', { links }).then(j) as Promise<{ summaries: string[] }>,
  renameSlot: (slot: string, title: string) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/title', { title }).then(j),
  regenerateSlot: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/regenerate').then(j),
  /** Pick an interrupted turn back up. NOT `/resume` — that path opens a history session into a tab. */
  continueSlot: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/continue').then(j),
  switchVariant: (slot: string, index: number) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/switch-variant', { index }).then(j),
  editResend: (slot: string, ts: string, content: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/edit-resend', { ts, content }).then(j),
  rewind: (slot: string, ts: string, content: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/rewind', { ts, content }).then(j),
  slackLink: (slot: string, channel?: string, threadTs?: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/slack-link', (channel || threadTs) ? { ...(channel ? { channel } : {}), ...(threadTs ? { thread_ts: threadTs } : {}) } : undefined).then(j),
  unlinkSlack: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/slack-unlink').then(j),
  // Sets whether turns reach the linked Slack thread. One call for both
  // directions: a session born in its thread has no binding to re-establish, so
  // reconnecting cannot go through slack-link.
  pauseSlack: (slot: string, paused: boolean) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/slack-pause', { paused }).then(j),
  /** `origin` names WHICH non-Slack delivery to act on: the conversation the
   *  session was born in, or its explicit mirror binding. A session can hold
   *  both, and they mute independently, so the row has to say which it is. */
  pauseMirror: (slot: string, paused: boolean, origin = false) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/mirror-pause', { paused, origin }).then(j),
  channelTargets: () => fetch('/api/chat/channel-targets').then(j),
  linkMirror: (slot: string, channelType: string, targetId: string) => post(
    '/api/chat/slots/' + encodeURIComponent(slot) + '/mirror-link',
    { channel_type: channelType, target_id: targetId },
  ).then(j),
  remindMirror: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/mirror-link').then(j),
  unlinkMirror: (slot: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/mirror-unlink').then(j),
  slackChannels: () => fetch('/api/slack/channels').then(j),
  // Folders
  chatFolders: () => fetch('/api/chat/folders', { headers: { ..._sk } }).then(j),
  /** `config` carries the folder settings the create modal collects. Each is
   *  omitted when empty so the backend applies its own default. */
  createChatFolder: (name: string, parentId?: string, config?: { project_dir?: string; default_agent?: string; color?: string; tags?: string[] }) =>
    post('/api/chat/folders', { name, parent_id: parentId || '', ...(config ?? {}) }).then(j),
  updateChatFolder: (id: string, body: object) => patch('/api/chat/folders/' + encodeURIComponent(id), body).then(j),
  deleteChatFolder: (id: string) => del('/api/chat/folders/' + encodeURIComponent(id)).then(j),
  setSlotFolder: (slot: string, folderId: string | null) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/folder', { folder_id: folderId || '' }).then(j),
  setSlotColor: (slot: string, colorIndex: number | null) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/color', { color_index: colorIndex }).then(j),
  /** Set a custom per-session color (#rrggbb). The backend clears color_index
   *  when a hex is set and vice versa (mutual exclusion), so callers send one
   *  or the other, never both. */
  setSlotColorHex: (slot: string, colorHex: string | null) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/color', { color_hex: colorHex }).then(j),
  /** Clear BOTH color fields in one PATCH. The endpoint is in-body-gated, so
   *  an index-only null would leave a custom hex behind. */
  clearSlotColor: (slot: string) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/color', { color_index: null, color_hex: null }).then(j),
  setSlotPin: (slot: string, pinned: boolean) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/pin', { pinned }).then(j),
  setSlotMode: (slot: string, mode: string) => patch('/api/chat/slots/' + encodeURIComponent(slot) + '/mode', { mode }).then(j),
  // Tags
  chatTags: () => fetch('/api/chat/tags', { headers: { ..._sk } }).then(j),
  createChatTag: (name: string, color?: string, status?: boolean) => post('/api/chat/tags', { name, color: color || '', status: !!status }).then(j),
  updateChatTag: (id: string, body: { name?: string; color?: string; order?: number; status?: boolean }) => patch('/api/chat/tags/' + encodeURIComponent(id), body).then(j),
  deleteChatTag: (id: string) => del('/api/chat/tags/' + encodeURIComponent(id)).then(j),
  setSlotTags: (slot: string, tags: string[]) => fetch('/api/chat/slots/' + encodeURIComponent(slot) + '/tags', { method: 'PUT', headers: { 'Content-Type': 'application/json', ..._sk }, body: JSON.stringify({ tags }) }).then(j),
  dropSlotToColumn: (slot: string, columnId: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/drop', { column_id: columnId }).then(j),
  tagColumns: () => fetch('/api/chat/tag-columns', { headers: { ..._sk } }).then(j),
  createTagColumn: (body: { name?: string; tag_ids?: string[]; mode?: 'any' | 'all' | 'none'; include_untagged?: boolean; source?: 'tags' | 'state'; state_key?: SessionLaneKey }) => post('/api/chat/tag-columns', body).then(j),
  updateTagColumn: (id: string, body: { name?: string; tag_ids?: string[]; mode?: 'any' | 'all' | 'none'; order?: number; include_untagged?: boolean }) => patch('/api/chat/tag-columns/' + encodeURIComponent(id), body).then(j),
  deleteTagColumn: (id: string) => del('/api/chat/tag-columns/' + encodeURIComponent(id)).then(j),
  reorderTagColumns: (ids: string[]) => fetch('/api/chat/tag-columns/order', { method: 'PUT', headers: { 'Content-Type': 'application/json', ..._sk }, body: JSON.stringify({ ids }) }).then(j),
  sendChat: (message: string, slot?: string, colorTheme?: string, signal?: AbortSignal, meta?: Record<string, unknown>, steer?: boolean) => {
    // theme_consent_sha is the WIRE TOKEN (two-tier consent). The client just
    // TRANSMITS the raw stored grant (see themeConsentSha) — the server verifies
    // content-binding, injecting the persona only when this token equals sha256
    // of the persona.md it reads. Omitted for a built-in theme, no grant, or a
    // legacy '1'/'' token (must re-prompt). The legacy `theme_consent` boolean
    // is intentionally NOT sent: gating is content-bound server-side.
    //
    // Browse mode is no longer sent per message: it is default-on server-side
    // whenever Browser Mode is enabled in Settings (a durable capability),
    // gated there rather than per turn.
    //
    // `steer` carries the user's "act on this now" intent into a send that
    // starts its OWN turn. The slot is idle, so there is no running turn to
    // inject into; the flag's only effect server-side is to skip the hold that
    // parks a user message behind still-running sub-agents. Sent through this
    // endpoint rather than steerChat because a new turn needs `ws=1` to stream.
    const themeConsent = themeConsentSha(colorTheme)
    return fetch('/api/chat?ws=1', { method: 'POST', headers: { 'Content-Type': 'application/json', ..._sk }, body: JSON.stringify({ message, slot, ...(colorTheme ? { color_theme: colorTheme } : {}), ...(themeConsent ? { theme_consent_sha: themeConsent } : {}), ...(meta ? { meta } : {}), ...(steer ? { steer: true } : {}) }), signal })
  },
  // Mid-turn steer: inject into the RUNNING turn instead of queueing. Fire-and-forget
  // JSON response ({ok, steered}); the backend falls back to queue if steer is
  // unavailable so the text is never dropped.
  // `ws=1` because a steer that races `chat_done` falls through to the plain send
  // path, whose JSON receipt is gated on it — without it that arm streams SSE.
  // `sendId` is the client-minted correlation id stamped on the optimistic steer
  // bubble (same convention as the plain send path). It rides in `meta`, which
  // BOTH backend paths persist — the accepted-steer row and the new-turn row a
  // steer that races chat_done falls onto — so the bubble is reconcilable, and
  // its accepted-vs-new-turn ambiguity resolvable, by id identity (#6075).
  steerChat: (message: string, slot?: string, sendId?: string) =>
    fetch('/api/chat?ws=1', { method: 'POST', headers: { 'Content-Type': 'application/json', ..._sk }, body: JSON.stringify({ message, slot, steer: true, ...(sendId ? { meta: { sendId } } : {}) }) }).then(j),
  sessionsHealth: () => fetch('/api/sessions/health').then(j),
  // Knowledge
  knowledgeSearch: (q: string) => get(`/api/knowledge/search-for-context?q=${encodeURIComponent(q)}`).then(j),
  // Notifications
  notifications: () => fetch('/api/notifications').then(j),
  deleteNotification: (ts: string) => del('/api/notifications', { ts }).then(j),
  clearNotifications: () => post('/api/notifications/clear').then(j),
  ackNotification: (ts: string) => post('/api/notifications/ack', { ts }).then(j),
  unackNotification: (ts: string) => post('/api/notifications/unack', { ts }).then(j),
  ackAllNotifications: () => post('/api/notifications/ack-all').then(j),
  notificationChannels: () => fetch('/api/notifications/channels').then(j),
  updateNotificationChannelSettings: (channel: string, settings: { muted?: boolean; priority?: string | null }) =>
    put('/api/notifications/channels/settings', { channel, ...settings }).then(j),
  // Handoff
  handoffChannels: () => fetch('/api/handoff-channels').then(j) as Promise<Record<string, string> | null>,
  handoffSlot: (slot: string, channel?: string) => post('/api/chat/slots/' + encodeURIComponent(slot) + '/handoff', channel ? { channel } : undefined).then(j),
  // Sessions (history)
  // `excludeOpen` drops sessions already open as a tab — for the sidebar's
  // Older-sessions pane, which is the complement of the tab list above it.
  // Off by default: every other caller wants the full inventory.
  sessions: (limit = 30, offset = 0, preview = false, excludeOpen = false) => fetch('/api/sessions?limit=' + limit + '&offset=' + offset + (preview ? '&preview=1' : '') + (excludeOpen ? '&exclude_open=1' : '')).then(j),
  sessionsSearch: (q: string, limit = 50) => fetch('/api/sessions/search?q=' + encodeURIComponent(q) + '&limit=' + limit).then(j),
  // Federated session search across the local gateway + every CONNECTED remote
  // instance (backend rank-interleaves; remote rows carry instance_id/_name).
  // 403 = instances feature disabled — callers fall back to sessionsSearch.
  instancesSearchSessions: (q: string, limit = 50) => fetch('/api/instances/search-sessions?q=' + encodeURIComponent(q) + '&limit=' + limit).then(j),
  /** What a connected crew can do: its version, agent roster, model list, effort
   *  levels and workspaces. The per-instance counterpart to `/api/agents`,
   *  `/api/models`, `/api/effort-levels` and `/api/workspaces`, which are all
   *  same-origin reads of THIS machine — a session bound to a peer for execution
   *  must offer the peer's options, since picking a crew or model that only exists
   *  here would fail on the first send.
   *
   *  `version_match` is the gate the backend enforces on every dispatch, surfaced
   *  so the UI can explain a refusal before the user types rather than after.
   *  `unavailable` names the reads that failed, per field, so one unreachable
   *  roster disables exactly its own control instead of blanking the shelf. */
  instancesCapabilities: (instanceId: string) =>
    fetch('/api/instances/' + encodeURIComponent(instanceId) + '/capabilities').then(j) as Promise<RemoteCrewCapabilities>,
  sessionDetail: (key: string) => fetch('/api/sessions/' + encodeURIComponent(key)).then(j),
  deleteSession: (key: string) => del('/api/sessions/' + encodeURIComponent(key)).then(j),
  clearSessions: () => del('/api/sessions').then(j),
  // Autocomplete
  autocomplete: (q: string): Promise<{suggestions: string[]}> => fetch('/api/autocomplete?q=' + encodeURIComponent(q)).then(j),
  // Spawn
  spawnList: () => fetch('/api/spawn').then(j),
  spawn: (task: string) => post('/api/spawn', { task }).then(j),
  spawnStatus: (id: string, opts?: { signal?: AbortSignal }) => fetch('/api/spawn/' + encodeURIComponent(id), opts).then(j),
  spawnDelete: (id: string) => del('/api/spawn/' + encodeURIComponent(id)).then(j),
  spawnStopAll: (slot: string) => post('/api/spawn/stop-all', { slot }).then(j),
  spawnRetry: (id: string) => post('/api/spawn/' + encodeURIComponent(id) + '/retry', {}).then(j),
  spawnClear: () => del('/api/spawn').then(j),
  approvals: (): Promise<{ id: string; source?: string; tool?: string; tool_input?: string; tool_call_id?: string; slot?: string; ts?: number }[]> => fetch('/api/approvals').then(j),
  resolveApproval: (id: string, action: 'approve' | 'reject' | 'reject_once') => post('/api/approvals/' + encodeURIComponent(id) + '/' + action, {}).then(j),
  /** Question cards still awaiting an answer, for rehydration after a reload or
   *  websocket reconnect (`question_card` is a one-shot broadcast). A blocking
   *  ask carries `ask_id`; a stateless card carries `card_id` instead. */
  pendingQuestions: (): Promise<{ ask_id?: string; card_id?: string; slot: string; questions: { question: string; header?: string; multiSelect?: boolean; options: { label: string; description?: string }[] }[]; ts?: number }[]> =>
    fetch('/api/ask-question/pending').then(j),
  /** Resolve a pending agent question that carries an `ask_id` — a server-side
   *  wait opened by `POST /api/ask-question`, not the MCP ask_question tool,
   *  which posts a stateless `card_id` card instead. Pass no answers to
   *  dismiss, which unblocks the waiting caller with a timeout-equivalent
   *  result. */
  answerQuestion: (askId: string, answers?: Record<string, string>) =>
    post('/api/ask-question/' + encodeURIComponent(askId) + '/answer',
      answers ? { answers } : { dismissed: true }).then(j),
  /** Retire the slot's needs-input status for a STATELESS card (no `ask_id`),
   *  which blocks nothing and is otherwise removed client-side only — leaving
   *  the sidebar and sessions board claiming the agent is still waiting.
   *  `cardId` is the server-minted identity from the `question_card` payload:
   *  the dismissal is a round-trip, so a newer card can replace this one before
   *  it lands, and the server refuses rather than retiring the wrong ask. */
  dismissQuestionCard: (slot: string, cardId: string) =>
    post('/api/ask-question/dismiss', { slot, card_id: cardId }).then(j),
  // Logs
  logLevel: () => fetch('/api/logs/level').then(j),
  setLogLevel: (level: string) => post('/api/logs/level', { level }).then(j),
  // Task runner
  taskRunnerStatus: () => fetch('/api/taskrunner').then(j),
  startTaskRunner: (spec: string, agent?: string, workspaceDir?: string) => post('/api/taskrunner', { spec, agent: agent || '', workspace_dir: workspaceDir || '' }).then(j),
  cancelTaskRunner: (taskId?: string) => post('/api/taskrunner/cancel', taskId ? { task_id: taskId } : undefined).then(j),
  pauseTaskRun: (taskId: string) => post('/api/taskrunner/' + encodeURIComponent(taskId) + '/pause').then(j),
  deleteTaskRun: (taskId: string) => del('/api/taskrunner/' + encodeURIComponent(taskId)).then(j),
  retryTaskRun: (taskId: string, fromStep: number) => post('/api/taskrunner/' + encodeURIComponent(taskId) + '/retry', { from_step: fromStep }).then(j),
  renameTaskRun: (taskId: string, name: string) => fetch('/api/taskrunner/' + encodeURIComponent(taskId) + '/name', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }).then(j),
  updateTask: (taskId: string, index: number, updates: { title?: string; description?: string; depends_on?: number[]; requires_approval?: boolean; force_approval?: boolean }) => fetch('/api/taskrunner/' + encodeURIComponent(taskId) + '/tasks/' + index, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(updates) }).then(j),
  taskRunToChat: (taskId: string) => post('/api/taskrunner/' + encodeURIComponent(taskId) + '/to-chat').then(j),
  // `action` mirrors the backend's own two modes: 'reveal' selects the path in
  // the OS file manager (the default every existing caller relies on), 'open'
  // hands a regular file to its default application. Headless hosts have
  // neither, so the backend answers with `copy` and the path goes to the
  // clipboard instead of the call silently doing nothing.
  // This is a SIDE-EFFECT-FREE transport call: it neither writes the clipboard
  // nor shows a dialog. The single caller `revealOrOpen` owns the clipboard copy,
  // so the degrade is presented in exactly one place instead of in the transport
  // layer where a dialog is a surprise.
  revealPath: (path: string, action: 'open' | 'reveal' = 'reveal') =>
    post('/api/reveal', { path, action }).then(j) as Promise<RevealResult>,
  collectDiagnostics: (body: { note: string; include_logs: boolean }) =>
    post('/api/diagnostics/collect', body).then(j) as Promise<{
      zip_path: string
      filename: string
      included: string[]
      skipped: string[]
      redaction_summary: Record<string, number>
      total_redactions: number
      github_issue_url: string
      download_url: string
    }>,
  /** Compact list of dynamic-workflow runs, newest first — the AUTHORITY for a
   *  run's status.
   *
   *  Live status reaches the chat only as one-shot `workflow_run_event` frames,
   *  so a client that was closed, asleep, or disconnected when a run ended holds
   *  a row that never leaves `running`. This is the read that corrects it (see
   *  `reconcileWorkflowRuns`). Rejects (503) when the workflows service is
   *  unavailable, which callers must treat as "no evidence" — never as "no runs".
   */
  workflowRuns: () =>
    get('/api/workflows/runs').then(j) as Promise<{ runs?: WorkflowRunSummary[] }>,
  workflowDefinitions: (search = '') =>
    get('/api/workflows/definitions' + (search ? `?q=${encodeURIComponent(search)}` : '')).then(j) as Promise<{ definitions: WorkflowDefinition[] }>,
  authorWorkflow: (intent: string) =>
    post('/api/workflows/author', { intent }).then(j) as Promise<{
      ok: boolean
      source: string
      meta?: { name?: string; description?: string }
      derived_from?: WorkflowLineage | null
      errors?: string[]
    }>,
  saveWorkflowDefinition: (body: WorkflowDefinitionWrite) =>
    post('/api/workflows/definitions', body).then(j) as Promise<{ ok: boolean; definition: WorkflowDefinition }>,
  promoteWorkflowRun: (
    runId: string,
    body: Omit<WorkflowDefinitionWrite, 'source' | 'derived_from'>,
  ) =>
    post(`/api/workflows/runs/${encodeURIComponent(runId)}/promote`, body).then(j) as Promise<{
      ok: boolean
      definition: WorkflowDefinition
    }>,
  updateWorkflowDefinition: (
    workflowRef: string,
    body: Omit<WorkflowDefinitionWrite, 'derived_from'> & { expected_revision: number },
  ) => patch(`/api/workflows/definitions/${encodeURIComponent(workflowRef)}`, body).then(j) as Promise<{ ok: boolean; definition: WorkflowDefinition }>,
  runWorkflowDefinition: (workflowRef: string, input: string, args: Record<string, unknown> = {}) =>
    post(`/api/workflows/definitions/${encodeURIComponent(workflowRef)}/run`, { input, args }).then(j) as Promise<{ run_id: string; workflow_id: string; revision: number; slug: string }>,
  refineTaskInput: (input: string) => post('/api/taskrunner/refine', { input }).then(j),
  refineStatus: () => fetch('/api/taskrunner/refine').then(j),
  refineCancel: () => post('/api/taskrunner/refine/cancel').then(j),
  planTask: (input: string, source: string, spec?: string, agent?: string, workspaceDir?: string) =>
    post('/api/taskrunner/plan', { input, source, spec: spec || '', agent: agent || '', workspace_dir: workspaceDir || '' }).then(j),
  cancelPlan: () => post('/api/taskrunner/plan/cancel').then(j),
  updatePlan: (taskId: string, steps: PlanStepInput[]) =>
    put('/api/taskrunner/' + encodeURIComponent(taskId) + '/plan', { steps }).then(j),
  executePlan: (taskId: string, agent?: string, autoApprove?: boolean) =>
    post('/api/taskrunner/' + encodeURIComponent(taskId) + '/execute', { agent: agent || '', auto_approve: !!autoApprove }).then(j),
  planFromChat: (steps: PlanStepInput[], taskId?: string, originalInput?: string) =>
    post('/api/taskrunner/from-chat', { steps, task_id: taskId || '', original_input: originalInput || '' }).then(j),
  planContext: (taskId: string) =>
    fetch('/api/taskrunner/' + encodeURIComponent(taskId) + '/plan-context').then(j),
  /** Download the run's plan as a YAML workflow (re-importable via the "From YAML" tab).
   *  Fetches with the auth header, then triggers a browser download honoring the
   *  server's sanitized Content-Disposition filename. */
  exportPlanYaml: async (taskId: string) => {
    const r = await get('/api/taskrunner/' + encodeURIComponent(taskId) + '/plan.yaml')
=======
  ...system.statusAndStorage,
  ...telemetry.usageReadouts,
  ...sessions.crewBoard,
  // Defined here rather than in ./client/telemetry: it reads
  // `api.wakatimeExportUrl` at call time, so replacing that member reroutes the
  // download.
  /** Download the export as a file. Fetches rather than navigating, so an
   *  upstream 502 raises here (surfaced through ErrorNotice) instead of
   *  replacing the dashboard with the raw error body. The saved filename comes
   *  from the endpoint's own sanitized Content-Disposition. */
  wakatimeExportDownload: async (start: string, end: string, format: 'csv' | 'json') => {
    const r = await get(api.wakatimeExportUrl(start, end, format))
>>>>>>> upstream/main
    if (!r.ok) {
      throw await toApiError(r)
    }
    const blob = await r.blob()
    const cd = r.headers.get('Content-Disposition') || ''
    const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/.exec(cd)
    const filename = (m && decodeURIComponent(m[1])) || `wakatime-hours-${start}-to-${end}.${format}`
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  },
  ...chat.summaries,
  ...telemetry.privacyPosture,
  ...onboarding.readiness,
  ...security.posture,
  ...remoteAccess.mobileAccess,
  ...security.policies,
  ...featureDiscovery.suggestions,
  ...themes.branding,
  ...instances.registryAndTransfer,
  ...cloud.launcher,
  ...memory.memoryAndVectors,
  ...sessions.runtimes,
  ...telemetry.creditUsage,
  ...mcp.probeCache,
  ...agents.crew,
  ...chatSlotSettings.selection,
  ...files.projects,
  ...cron.jobs,
  ...security.secrets,
  ...cron.historyAndFolders,
  ...memory.lessons,
  // Defined here rather than in ./client/memory: learn-cron-dashboard.md names
  // this module as the home of `deleteLesson`.
  // The selector is sent only when it is a string: `""` names the global row
  // and a fragment names that scope's row, while an absent key deletes every
  // scope's same-rule row -- which is the only delete that can reach a row the
  // list reports as `null` (stored scope present but unusable). Passing `null`
  // through would be refused (400 repo_scope_not_string) rather than widened.
  // `selectors` are the row's own from the list: `scope` / `workspace` pick the
  // JSONL file (the route defaults to the global one, so a workspace row's delete
  // has to carry them back), and `exact` narrows the rule match to the whole
  // rule -- the route matches by SUBSTRING by default, which is right for a CLI
  // fragment and wrong for a table row that holds the full text ("use tabs"
  // would also take "always use tabs").
  deleteLesson: (
    rule: string,
    repoScope?: string | null,
    selectors?: { scope?: 'global' | 'workspace'; workspace?: string; exact?: boolean },
  ) =>
    del('/api/lessons', {
      rule,
      ...(typeof repoScope === 'string' ? { repo_scope: repoScope } : {}),
      ...(selectors?.scope ? { scope: selectors.scope } : {}),
      ...(selectors?.workspace ? { workspace: selectors.workspace } : {}),
      ...(selectors?.exact ? { exact: true } : {}),
    }).then(j) as Promise<{ ok: boolean }>,
  ...hooks.triggers,
  ...skills.library,
  ...steering.files,
  ...skills.curation,
  ...mcp.servers,
  ...connections.accounts,
  ...mcp.gateway,
  ...config.settings,
  ...telemetry.kiroUsage,
  ...capabilityManager.catalog,
  ...voice.speechToText,
  ...sourceControl.providers,
  ...chat.slotList,
  ...monitors.loops,
  ...chat.slots,
  ...chatOrganization.sidebar,
  ...chat.send,
  ...system.taskQueue,
  ...memory.knowledge,
  ...notifications.inbox,
  ...sessions.history,
  ...instances.peerReads,
  ...sessions.historyDetail,
  ...chat.composerAutocomplete,
  ...subagents.spawned,
  ...approvals.requests,
  ...system.logs,
  ...taskRunner.runs,
  ...files.reveal,
  ...system.diagnostics,
  ...workflows.engine,
  ...taskRunner.plans,
  ...updates.lifecycle,
  ...files.fileOps,
  ...themes.themeList,
  ...config.dashboardRead,
  ...featureDiscovery.featureVideos,
  ...config.dashboardWrite,
  ...themes.themeEditing,
  ...voice.voiceSettings,
  ...security.consents,
  ...voice.synthesis,
  ...agentChannels.channels,
  ...apps.platform,
  ...artifacts.library,
  // Defined here rather than in ./client/artifacts: the i18n gate reads the
  // query-string template below as copy, and a moved line counts as written.
  browseRemoteArtifacts: (provider: string, opts?: { scope?: string; q?: string; pageToken?: string }) =>
    get(
      `/api/remote-artifacts/${encodeURIComponent(provider)}/browse` +
        `?scope=${encodeURIComponent(opts?.scope ?? 'mine')}` +
        (opts?.q ? `&q=${encodeURIComponent(opts.q)}` : '') +
        (opts?.pageToken ? `&pageToken=${encodeURIComponent(opts.pageToken)}` : ''),
    ).then(j),
  ...artifacts.remoteAndComments,
  ...browserAndComputerUse.hostAutomation,
  ...decisions.consentRead,
  // Defined here rather than in ./client/decisions: decisions.md names this
  // module as the home of the optional-`enabled` consent write.
  // Enabling echoes the endpoint the card showed: the gateway binds consent to
  // that address and answers 409 if config.json moved it since the read.
  // `toolArgs` and `compaction` are each OMITTED when the caller does not pass one,
  // and that omission is meaningful: the gateway preserves the recorded scope for an
  // absent field, so an ordinary switch flip can neither grant nor erase it. Pass a
  // boolean only for the switch the owner actually acted on — including `false`,
  // because on this route a revoke has to be written and cannot be left out.
  // `enabled` is OPTIONAL, and leaving it out is what makes a scope write safe rather
  // than careful: a body that carries the switch can only carry what this client last
  // read, so a view read before a revoke turns egress back on. Omitted, the route reads
  // the switch and the endpoint off the keystone under its own lock, and the write moves
  // only the scopes named. A body with neither the switch nor a scope is a 400.
  saveDecisionsConsent: (
    enabled?: boolean,
    endpoint?: string,
    toolArgs?: boolean,
    compaction?: boolean,
    memoryText?: boolean,
  ) =>
    put('/api/decisions/consent', enabled === undefined
      ? {
        endpoint,
        ...(toolArgs === undefined ? {} : { tool_args: toolArgs }),
        ...(compaction === undefined ? {} : { compaction }),
        ...(memoryText === undefined ? {} : { memory_text: memoryText }),
      }
      : enabled
        ? {
          enabled,
          endpoint,
          ...(toolArgs === undefined ? {} : { tool_args: toolArgs }),
          ...(compaction === undefined ? {} : { compaction }),
          ...(memoryText === undefined ? {} : { memory_text: memoryText }),
        }
        : { enabled }).then(j) as Promise<DecisionsConsentData>,
  ...decisions.scopesAndFeedback,
  ...messaging.channelConfigs,
  ...autoResearch.drafts,
  ...apps.sessionStatus,
  ...autoResearch.campaigns,
  ...apps.fileMenu,
  ...artifacts.publishing,
  ...featureDiscovery.tips,
}
