import { Navigate } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import type { Role } from "@/lib/api"

export function ProtectedRoute({ allow, children }: { allow: Role[]; children: React.ReactNode }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (!allow.includes(user.role)) return <Navigate to="/" replace />
  return <>{children}</>
}
