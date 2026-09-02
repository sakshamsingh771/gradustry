import { createContext, useContext, useState, type ReactNode } from "react"
import { authApi, type AuthUser, type Role } from "@/lib/api"

interface AuthContextType {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<AuthUser>
  register: (role: Role, payload: object) => Promise<AuthUser>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function readStoredUser(): AuthUser | null {
  const raw = localStorage.getItem("gradustry_user")
  return raw ? JSON.parse(raw) : null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(readStoredUser)
  const [loading, setLoading] = useState(false)

  const persist = (data: any): AuthUser => {
    const authUser: AuthUser = { user_id: data.user_id, full_name: data.full_name, role: data.role }
    localStorage.setItem("gradustry_token", data.access_token)
    localStorage.setItem("gradustry_user", JSON.stringify(authUser))
    setUser(authUser)
    return authUser
  }

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      const res = await authApi.login(email, password)
      return persist(res.data)
    } finally {
      setLoading(false)
    }
  }

  const register = async (role: Role, payload: object) => {
    setLoading(true)
    try {
      const fn = { student: authApi.registerStudent, college: authApi.registerCollege, industry: authApi.registerIndustry }[
        role as "student" | "college" | "industry"
      ]
      const res = await fn(payload)
      return persist(res.data)
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem("gradustry_token")
    localStorage.removeItem("gradustry_user")
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
