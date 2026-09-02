import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GraduationCap, Eye, EyeOff } from "lucide-react"
import { toast } from "sonner"

const roleHome: Record<string, string> = {
  student: "/student", college: "/college", industry: "/industry", admin: "/admin",
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPw, setShowPw] = useState(false)
  const [remember, setRemember] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const user = await login(email, password)
      toast.success(`Welcome back, ${user.full_name.split(" ")[0]}`)
      navigate(roleHome[user.role] ?? "/")
    } catch {
      toast.error("Incorrect email or password")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-alt/40 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-sm">
        <Link to="/" className="flex items-center justify-center gap-2">
          <GraduationCap className="h-6 w-6 text-accent" />
          <span className="font-display text-lg">Gradustry</span>
        </Link>
        <h1 className="mt-6 text-center font-display text-2xl">Welcome back</h1>
        <p className="text-center text-sm text-muted">Log in to continue your skill journey.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input id="password" type={showPw ? "text" : "password"} required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
              <button type="button" onClick={() => setShowPw((s) => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted">
                {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 text-muted">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="rounded border-border" />
              Remember me
            </label>
            <a href="#" className="text-accent">Forgot password?</a>
          </div>
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Logging in…" : "Log in"}
          </Button>
          <Button type="button" variant="outline" className="w-full" onClick={() => toast("Google login is integration-ready — coming soon.")}>
            Continue with Google
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          New to Gradustry? <Link to="/register" className="text-accent">Create an account</Link>
        </p>

        <div className="mt-6 rounded-lg bg-surface-alt p-3 text-xs text-muted">
          <p className="font-medium text-foreground">Demo logins</p>
          <p>student@gradustry.dev / student123</p>
          <p>college@gradustry.dev / college123</p>
          <p>industry@gradustry.dev / industry123</p>
          <p>admin@gradustry.dev / admin123</p>
        </div>
      </div>
    </div>
  )
}
