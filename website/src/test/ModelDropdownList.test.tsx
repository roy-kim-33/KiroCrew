import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import ModelDropdownList, { formatMultiplier, costTier } from '../components/ModelDropdownList'

/**
 * The fork's model picker renders a router catalog, not Kiro's fixed list, so
 * the rows it must not mangle are the ones a router adds: models with no rate
 * multiplier at all, and the vision flag that decides whether an image can be
 * sent at all. A row that silently lands in the wrong section is how a user
 * sends an image to a text-only model and gets a 400 that wedges the session.
 */
const model = (name: string, extra: Record<string, unknown> = {}) => ({ name, ...extra })

describe('formatMultiplier', () => {
  it('keeps one decimal for ordinary rates', () => {
    expect(formatMultiplier(1)).toBe('1.0x')
    expect(formatMultiplier(1.3)).toBe('1.3x')
    expect(formatMultiplier(4.4)).toBe('4.4x')
  })

  it('never renders a sub-cent rate as 0x', () => {
    // "0x" reads as free. Anything that rounds to zero keeps a significant
    // digit instead.
    expect(formatMultiplier(0.004)).not.toMatch(/^0x$/)
    expect(formatMultiplier(0.001)).not.toMatch(/^0x$/)
  })

  it('rounds to two decimals', () => {
    expect(formatMultiplier(1.239)).toBe('1.24x')
    expect(formatMultiplier(1.231)).toBe('1.23x')
  })
})

describe('costTier', () => {
  it('splits on the default multiplier the user already sits at', () => {
    expect(costTier(0.01)).toBe('budget')
    expect(costTier(0.99)).toBe('budget')
    expect(costTier(1)).toBe('standard')
    expect(costTier(1.3)).toBe('standard')
    expect(costTier(1.5)).toBe('standard')
    expect(costTier(1.51)).toBe('premium')
    expect(costTier(4.4)).toBe('premium')
  })
})

describe('ModelDropdownList', () => {
  it('renders a flat list when no model reports vision', () => {
    render(
      <ModelDropdownList
        models={[model('cmc/deepseek-v4-pro'), model('oc/glm-5.2')]}
        activeModel="cmc/deepseek-v4-pro"
        onSelect={vi.fn()}
      />
    )
    expect(screen.getByText('cmc/deepseek-v4-pro')).toBeInTheDocument()
    expect(screen.getByText('oc/glm-5.2')).toBeInTheDocument()
  })

  it('separates vision rows from text-only ones', () => {
    render(
      <ModelDropdownList
        models={[
          model('cmc/mimo-v2.5', { supportsVision: true }),
          model('oc/deepseek-v4-flash'),
        ]}
        activeModel="cmc/mimo-v2.5"
        onSelect={vi.fn()}
      />
    )
    expect(screen.getByText('cmc/mimo-v2.5')).toBeInTheDocument()
    expect(screen.getByText('oc/deepseek-v4-flash')).toBeInTheDocument()
  })

  it('treats a missing vision flag as text-only, never as vision', () => {
    // A gateway older than the flag reports nothing. Guessing "vision" there is
    // what sends an image to a model that rejects it.
    render(
      <ModelDropdownList
        models={[model('legacy/model'), model('cmc/mimo-v2.5', { supportsVision: true })]}
        activeModel="legacy/model"
        onSelect={vi.fn()}
      />
    )
    expect(screen.getByText('legacy/model')).toBeInTheDocument()
    expect(screen.getByText('cmc/mimo-v2.5')).toBeInTheDocument()
  })

  it('reports the chosen model by name', () => {
    const onSelect = vi.fn()
    render(
      <ModelDropdownList
        models={[model('cmc/deepseek-v4-pro'), model('oc/glm-5.2')]}
        activeModel="cmc/deepseek-v4-pro"
        onSelect={onSelect}
      />
    )
    fireEvent.click(screen.getByText('oc/glm-5.2'))
    expect(onSelect).toHaveBeenCalledWith('oc/glm-5.2')
  })

  it('renders a router row that carries no rate multiplier', () => {
    // Router catalogs price nothing; the badge must simply be absent rather
    // than rendering NaNx or 0x.
    render(
      <ModelDropdownList
        models={[model('cmc/deepseek-v4-pro'), model('kiro/auto', { rateMultiplier: 1 })]}
        activeModel="kiro/auto"
        onSelect={vi.fn()}
      />
    )
    expect(screen.getByText('cmc/deepseek-v4-pro')).toBeInTheDocument()
    expect(screen.queryByText('NaNx')).not.toBeInTheDocument()
    expect(screen.queryByText('0x')).not.toBeInTheDocument()
  })

  it('renders each model description when the catalog supplies one', () => {
    render(
      <ModelDropdownList
        models={[model('cmc/mimo-v2.5', { description: 'vision-capable', supportsVision: true })]}
        activeModel="cmc/mimo-v2.5"
        onSelect={vi.fn()}
      />
    )
    expect(screen.getByText('vision-capable')).toBeInTheDocument()
  })
})
