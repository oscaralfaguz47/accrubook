import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { apiUrl, currencies, currencyPage } from '../../test/handlers'
import { renderWithQueryClient } from '../../test/render'
import { server } from '../../test/server'
import { CurrencyList } from './CurrencyList'

const listUrl = apiUrl('/api/v1/currencies/')

const notFoundProblem = {
  type: 'about:blank',
  title: 'Not Found',
  status: 404,
  detail: 'Not found.',
  code: 'not_found',
  instance: '/api/v1/currencies/',
}

describe('CurrencyList', () => {
  it('shows a loading state, then one row per currency', async () => {
    renderWithQueryClient(<CurrencyList />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading currencies…')

    const table = await screen.findByRole('table', { name: 'Currencies' })
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(1 + currencies.length) // header + data rows
    expect(rows[1]).toHaveTextContent('CRCCosta Rican Colon2Yes')
    expect(rows[2]).toHaveTextContent('JPYJapanese Yen0No')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('shows an empty state when the API returns no currencies', async () => {
    server.use(http.get(listUrl, () => HttpResponse.json(currencyPage([]))))

    renderWithQueryClient(<CurrencyList />)

    expect(await screen.findByText('No currencies available yet.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows the Problem Details message and code for an API error', async () => {
    server.use(
      http.get(listUrl, () =>
        HttpResponse.json(notFoundProblem, {
          status: 404,
          headers: { 'Content-Type': 'application/problem+json' },
        }),
      ),
    )

    renderWithQueryClient(<CurrencyList />)

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Could not load currencies. Not found.')
    expect(within(alert).getByText('not_found')).toBeInTheDocument()
  })

  it('shows a connection message, without a code, when the network fails', async () => {
    server.use(http.get(listUrl, () => HttpResponse.error()))

    renderWithQueryClient(<CurrencyList />)

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Cannot reach the server')
    expect(alert).not.toHaveTextContent('Error code')
  })

  it('loads the currencies when the user clicks "Try again" after a failure', async () => {
    const user = userEvent.setup()
    // Only the first request fails; the next one falls back to the happy-path handler.
    server.use(http.get(listUrl, () => HttpResponse.error(), { once: true }))

    renderWithQueryClient(<CurrencyList />)
    await user.click(await screen.findByRole('button', { name: 'Try again' }))

    expect(await screen.findByRole('table', { name: 'Currencies' })).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
