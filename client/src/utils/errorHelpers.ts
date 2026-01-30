/**
 * error handling utilities
 */

/**
 * extract error message from an unknown error
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  
  if (typeof error === 'string') {
    return error
  }
  
  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message)
  }
  
  return 'an unexpected error occurred'
}

/**
 * format error for user display
 */
export function formatErrorForDisplay(error: unknown): string {
  const message = getErrorMessage(error)
  
  // capitalize first letter
  return message.charAt(0).toUpperCase() + message.slice(1)
}

/**
 * check if error is a text overflow error
 */
export function isTextOverflowError(error: unknown): boolean {
  return (
    error instanceof Error &&
    error.message.includes('overflow') ||
    (error && typeof error === 'object' && 'overflow' in error)
  )
}
