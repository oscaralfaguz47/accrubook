import { useQuery } from '@tanstack/react-query'

import { toErrorView } from '../../api/errorView'
import { currencyListQuery } from './queries'

export function CurrencyList() {
  // Hooks first, always, before any early return (rules of hooks).
  const { data, error, isPending, isError, isFetching, refetch } = useQuery(currencyListQuery())

  if (isPending) {
    return <output>Loading currencies…</output>
  }

  if (isError) {
    const { message, code } = toErrorView(error)
    return (
      <div role="alert">
        <p>Could not load currencies. {message}</p>
        {code ? (
          <p>
            Error code: <code>{code}</code>
          </p>
        ) : null}
        <button type="button" onClick={() => void refetch()} disabled={isFetching}>
          Try again
        </button>
      </div>
    )
  }

  // From here on TypeScript knows `data` is defined: the union was narrowed above.
  if (data.results.length === 0) {
    return <p>No currencies available yet.</p>
  }

  return (
    <table>
      <caption>Currencies</caption>
      <thead>
        <tr>
          <th scope="col">Code</th>
          <th scope="col">Name</th>
          <th scope="col">Decimal places</th>
          <th scope="col">Active</th>
        </tr>
      </thead>
      <tbody>
        {data.results.map((currency) => (
          <tr key={currency.code}>
            <td>{currency.code}</td>
            <td>{currency.name}</td>
            <td>{currency.decimal_places}</td>
            <td>{currency.is_active ? 'Yes' : 'No'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
