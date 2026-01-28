interface ErrorDisplayProps {
  error: string
}

export function ErrorDisplay({ error }: ErrorDisplayProps) {
  return (
    <div className="error-display" style={{ color: 'red' }}>
      <h3>Error</h3>
      <p>{error}</p>
    </div>
  )
}
