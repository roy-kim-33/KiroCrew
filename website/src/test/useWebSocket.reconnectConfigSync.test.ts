/**
 * Reconnect must re-sync `kirocrewConfig` and `available-models`, not just
 * session summaries.
 *
 * Both queries use `staleTime: Infinity` — freshness is push-driven
 * (`sessions_restarting` -> invalidateRefreshQueries; session-spawn
 * `activity_event` -> `available-models`), never poll-driven. A provider
 * switch made by this tab before a drop, by another tab, or by the desktop
 * app pushes exactly one of those frames while this socket is down, and
 * nothing else will ever correct the cache: the settings panel and every
 * model picker in the app keep serving the pre-switch backend's data
 * forever, surviving even a remount, until the page is hard-reloaded. A
 * gateway restart (e.g. `dev-fullstack.sh`) guarantees that exact window.
 */
import { renderHook, act } from '@testing-library/react'
import { createElement } from 'react'
import { Provider } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createTestStore } from './helpers'
import { useWebSocket } from '../hooks/useWebSocket'

vi.mock('../api/client', () => ({
  api: {
    chatSlots: vi.fn().mockResolvedValue([]),
    voiceConfig: vi.fn().mockResolvedValue({ autoSpeak: false }),
    approvals: vi.fn().mockResolvedValue([]),
    notifications: vi.fn().mockResolvedValue({ notifications: [], unread: 0 }),
    chatSlotDetail: vi.fn().mockResolvedValue({ messages: [], running: false, has_more: false, total: 0, queue: [] }),
  },
}))

const WS_INSTANCES: MockWebSocket[] = []

class MockWebSocket {
  static OPEN = 1
  static CONNECTING = 0
  readyState = MockWebSocket.CONNECTING
  onopen: ((ev: Event) => void) | null = null
  onmessage: ((ev: MessageEvent) => void) | null = null
  onclose: ((ev: CloseEvent) => void) | null = null
  onerror: ((ev: Event) => void) | null = null
  send = vi.fn()
  close = vi.fn()

  constructor() { WS_INSTANCES.push(this) }

  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.(new Event('open'))
  }
}

describe('useWebSocket reconnect config/model-list catch-up', () => {
  let testStore: ReturnType<typeof createTestStore>
  let qc: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    WS_INSTANCES.length = 0
    testStore = createTestStore()
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    vi.stubGlobal('WebSocket', MockWebSocket)
  })

  afterEach(() => { vi.unstubAllGlobals() })

  function wrapper({ children }: { children: React.ReactNode }) {
    return createElement(Provider, { store: testStore },
      createElement(QueryClientProvider, { client: qc }, children),
    )
  }

  const keysOf = (spy: { mock: { calls: unknown[][] } }) =>
    spy.mock.calls.map(c => JSON.stringify((c[0] as { queryKey?: unknown })?.queryKey))

  it('does NOT invalidate config/models on the first-ever connect', () => {
    // Nothing could have been missed yet — there is no prior connection to
    // have dropped a push during.
    const spy = vi.spyOn(qc, 'invalidateQueries')
    renderHook(() => useWebSocket(), { wrapper })
    act(() => { WS_INSTANCES[0].simulateOpen() })

    const keys = keysOf(spy)
    expect(keys).not.toContain(JSON.stringify(['kirocrewConfig']))
    expect(keys).not.toContain(JSON.stringify(['available-models']))
  })

  it('invalidates both on reconnect after a drop', () => {
    renderHook(() => useWebSocket(), { wrapper })
    act(() => { WS_INSTANCES[0].simulateOpen() })

    const spy = vi.spyOn(qc, 'invalidateQueries')
    act(() => { WS_INSTANCES[0].onclose?.(new CloseEvent('close')) })
    const reconnected = WS_INSTANCES[WS_INSTANCES.length - 1]
    act(() => { reconnected.simulateOpen() })

    const keys = keysOf(spy)
    expect(keys).toContain(JSON.stringify(['kirocrewConfig']))
    expect(keys).toContain(JSON.stringify(['available-models']))
  })
})
