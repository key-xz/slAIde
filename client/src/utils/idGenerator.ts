/**
 * unique ID generation utilities
 */

let idCounter = 0

/**
 * generate a unique ID with an optional prefix
 */
export function generateId(prefix = 'id'): string {
  const timestamp = Date.now()
  const counter = idCounter++
  return `${prefix}_${timestamp}_${counter}`
}

/**
 * generate a unique slide ID
 */
export function generateSlideId(): string {
  return generateId('slide')
}

/**
 * generate a unique image ID
 */
export function generateImageId(): string {
  return generateId('image')
}

/**
 * generate a unique chunk ID
 */
export function generateChunkId(): string {
  return generateId('chunk')
}

/**
 * reset the ID counter (useful for testing)
 */
export function resetIdCounter(): void {
  idCounter = 0
}
