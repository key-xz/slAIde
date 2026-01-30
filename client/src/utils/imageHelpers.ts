/**
 * image handling utilities
 */

/**
 * convert file to base64 data URL
 */
export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result)
      } else {
        reject(new Error('failed to read file as data URL'))
      }
    }
    
    reader.onerror = () => {
      reject(new Error('failed to read file'))
    }
    
    reader.readAsDataURL(file)
  })
}

/**
 * validate image file type
 */
export function isValidImageType(file: File): boolean {
  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
  return validTypes.includes(file.type)
}

/**
 * validate image file size (in MB)
 */
export function isValidImageSize(file: File, maxSizeMB = 10): boolean {
  const maxSizeBytes = maxSizeMB * 1024 * 1024
  return file.size <= maxSizeBytes
}

/**
 * validate image file
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  if (!isValidImageType(file)) {
    return {
      valid: false,
      error: 'invalid image type. supported types: PNG, JPEG, GIF, WebP',
    }
  }
  
  if (!isValidImageSize(file)) {
    return {
      valid: false,
      error: 'image size exceeds 10MB limit',
    }
  }
  
  return { valid: true }
}

/**
 * create object URL from base64 (for optimization)
 */
export function base64ToObjectURL(base64: string): string {
  // extract mime type and data
  const matches = base64.match(/^data:([^;]+);base64,(.+)$/)
  if (!matches) {
    throw new Error('invalid base64 data URL')
  }
  
  const [, mimeType, data] = matches
  const bytes = atob(data)
  const array = new Uint8Array(bytes.length)
  
  for (let i = 0; i < bytes.length; i++) {
    array[i] = bytes.charCodeAt(i)
  }
  
  const blob = new Blob([array], { type: mimeType })
  return URL.createObjectURL(blob)
}

/**
 * cleanup object URL
 */
export function revokeObjectURL(url: string): void {
  URL.revokeObjectURL(url)
}
