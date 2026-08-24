import { describe, it, expect } from 'vitest'

import {
  BACKEND_OPTIONS,
  PROVIDER_PRESETS,
  backendNeedsProviderConfig,
  type AgentBackend,
} from './providerPresets'

/**
 * These presets only PREFILL the base-URL field, so a wrong entry is not a
 * crash — it silently points the fork at an endpoint that answers nothing, and
 * the user sees a failed connection test with no clue why. The invariants that
 * catch that are structural: every backend the picker offers has a preset list
 * (or is explicitly config-free), every URL is a usable absolute origin with no
 * trailing slash or version path, and `custom` stays the blank first choice.
 */
describe('provider presets', () => {
  it('offers exactly the three backends the settings picker renders', () => {
    expect(BACKEND_OPTIONS.map(o => o.value)).toEqual(['claude_code', 'opencode', 'acp'])
    for (const o of BACKEND_OPTIONS) {
      expect(o.label.trim()).not.toBe('')
      expect(o.sub.trim()).not.toBe('')
    }
  })

  it('gives every configurable backend a preset list, and kiro-native none', () => {
    expect(backendNeedsProviderConfig('claude_code')).toBe(true)
    expect(backendNeedsProviderConfig('opencode')).toBe(true)
    // kiro-native's router is managed by kiro-cli; a URL/key box would be a lie.
    expect(backendNeedsProviderConfig('acp')).toBe(false)
    expect(Object.keys(PROVIDER_PRESETS).sort()).toEqual(['claude_code', 'opencode'])
  })

  it.each(['claude_code', 'opencode'] as const)('%s: custom is the blank first choice', backend => {
    const [first] = PROVIDER_PRESETS[backend]
    expect(first.value).toBe('custom')
    expect(first.url).toBe('')
    expect(first.keyRequired).toBeUndefined()
  })

  it.each(['claude_code', 'opencode'] as const)('%s: preset values are unique', backend => {
    const values = PROVIDER_PRESETS[backend].map(p => p.value)
    expect(new Set(values).size).toBe(values.length)
  })

  it.each(['claude_code', 'opencode'] as const)('%s: every URL is a bare origin', backend => {
    for (const preset of PROVIDER_PRESETS[backend]) {
      if (!preset.url) continue // 'custom' and OmniRouter are user-supplied
      const url = new URL(preset.url) // throws on a malformed entry
      expect(['http:', 'https:']).toContain(url.protocol)
      // The backend appends /v1/... itself, so a version path or trailing
      // slash here produces //v1 or /v1/v1 and a 404 the user cannot explain.
      expect(preset.url.endsWith('/')).toBe(false)
      expect(preset.url).not.toMatch(/\/v\d+$/)
    }
  })

  it('labels every opencode preset with its wire format', () => {
    // claude_code speaks Anthropic only; opencode adapts, so the format decides
    // which endpoint shape the adapter builds and cannot be left to a default.
    for (const preset of PROVIDER_PRESETS.opencode) {
      if (preset.value === 'custom') continue
      expect(preset.format, `${preset.value} has no format`).toBeDefined()
      expect(['anthropic', 'openai']).toContain(preset.format)
    }
  })

  it('marks the hosted providers as key-required and the local routers as not', () => {
    const byValue = Object.fromEntries(PROVIDER_PRESETS.claude_code.map(p => [p.value, p]))
    // Local routers on loopback need no key; a spurious "key required" would
    // block the Save button on the fork's own primary setup path.
    expect(byValue['9router'].keyRequired).toBeUndefined()
    expect(byValue['cli-proxy-api'].keyRequired).toBeUndefined()
    expect(byValue['anthropic'].keyRequired).toBe(true)
    expect(byValue['commandcode'].keyRequired).toBe(true)
  })

  it('keeps the local router URLs on loopback', () => {
    for (const value of ['9router', 'cli-proxy-api']) {
      const preset = PROVIDER_PRESETS.claude_code.find(p => p.value === value)!
      expect(new URL(preset.url).hostname).toBe('localhost')
    }
  })

  it('accepts every declared backend value', () => {
    const backends: AgentBackend[] = ['acp', 'claude_code', 'opencode']
    for (const b of backends) expect(typeof backendNeedsProviderConfig(b)).toBe('boolean')
  })
})
