import { useAuth } from '../contexts/AuthContext'
import { Auth } from './Auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Auth />
  }

  return <>{children}</>
}
