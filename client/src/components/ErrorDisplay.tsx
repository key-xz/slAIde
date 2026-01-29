interface ErrorDisplayProps {
  error: string
}

export function ErrorDisplay({ error }: ErrorDisplayProps) {
  return (
    <div className="p-4 bg-yellow-50 border border-yellow-300 rounded my-4 text-yellow-800">
      <h3 className="font-semibold mb-2">error</h3>
      <p>{error}</p>
    </div>
  )
}
