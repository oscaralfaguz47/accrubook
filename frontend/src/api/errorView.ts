import { ApiError } from './errors'

/** What the UI shows for a failed request. */
export interface ErrorView {
  message: string
  /** Machine-readable code from Problem Details, useful when reporting the issue. */
  code?: string
}

export function toErrorView(error: unknown): ErrorView {
  if (error instanceof ApiError) {
    return { message: error.message, code: error.problem.code }
  }
  if (error instanceof TypeError) {
    return { message: 'Cannot reach the server. Check your connection and try again.' }
  }
  return { message: 'Something went wrong. Please try again.' }
}
