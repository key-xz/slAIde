export function getPlaceholderTypeLabel(type: string): string {
  const typeMap: Record<string, string> = {
    'TITLE': 'Title',
    'BODY': 'Body Text',
    'PICTURE': 'Image',
    'CHART': 'Chart',
    'TABLE': 'Table',
    'OBJECT': 'Object',
    'SUBTITLE': 'Subtitle',
    'DATE': 'Date',
    'FOOTER': 'Footer',
    'SLIDE_NUMBER': 'Slide Number',
  }
  
  const cleaned = type.replace('PLACEHOLDER_TYPE.', '')
  return typeMap[cleaned] || cleaned
}

export function isImagePlaceholder(type: string): boolean {
  const phType = type.replace('PLACEHOLDER_TYPE.', '')
  return phType.includes('PICTURE') || phType.includes('OBJECT')
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      resolve(reader.result as string)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export function downloadBase64File(
  base64Data: string,
  filename: string,
  mimeType: string
): void {
  const blob = new Blob(
    [Uint8Array.from(atob(base64Data), c => c.charCodeAt(0))],
    { type: mimeType }
  )
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
