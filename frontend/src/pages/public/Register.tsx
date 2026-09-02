import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { GraduationCap, User, School, Building2 } from "lucide-react"
import { toast } from "sonner"
import type { Role } from "@/lib/api"

const roleHome: Record<string, string> = {
  student: "/student", college: "/college", industry: "/industry",
}

const roleCards = [
  { role: "student" as Role, icon: User, title: "Student", body: "Build your Skill Passport and find opportunities." },
  { role: "college" as Role, icon: School, title: "College", body: "Track student readiness and curriculum gaps." },
  { role: "industry" as Role, icon: Building2, title: "Industry", body: "Post roles and hire with explainable matching." },
]

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [role, setRole] = useState<Role | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState<Record<string, string>>({})

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!role) return
    setSubmitting(true)
    try {
      let payload: object = {}
      if (role === "student") {
        payload = { full_name: form.full_name, email: form.email, password: form.password, branch: form.branch || "", year_of_study: Number(form.year_of_study) || 1, career_goal: form.career_goal || "" }
      } else if (role === "college") {
        payload = { full_name: form.full_name, email: form.email, password: form.password, college_name: form.college_name, city: form.city || "" }
      } else {
        payload = { full_name: form.full_name, email: form.email, password: form.password, company_name: form.company_name, industry_sector: form.industry_sector || "" }
      }
      const user = await register(role, payload)
      toast.success(`Account created — welcome, ${user.full_name.split(" ")[0]}`)
      navigate(roleHome[user.role] ?? "/")
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Registration failed")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-alt/40 px-4 py-10">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-surface p-8 shadow-sm">
        <Link to="/" className="flex items-center justify-center gap-2">
          <GraduationCap className="h-6 w-6 text-accent" />
          <span className="font-display text-lg">Gradustry</span>
        </Link>

        {!role ? (
          <>
            <h1 className="mt-6 text-center font-display text-2xl">How will you use Gradustry?</h1>
            <div className="mt-6 grid gap-3">
              {roleCards.map(({ role: r, icon: Icon, title, body }) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className="flex items-start gap-4 rounded-xl border border-border p-4 text-left transition-colors hover:border-accent hover:bg-accent/5"
                >
                  <Icon className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
                  <div>
                    <p className="font-display">{title}</p>
                    <p className="text-sm text-muted">{body}</p>
                  </div>
                </button>
              ))}
            </div>
          </>
        ) : (
          <>
            <button onClick={() => setRole(null)} className="mt-6 text-sm text-muted hover:text-foreground">← Change role</button>
            <h1 className="mt-2 font-display text-2xl capitalize">{role} registration</h1>
            <form onSubmit={onSubmit} className="mt-4 space-y-4">
              <div className="space-y-1.5">
                <Label>Full name</Label>
                <Input required value={form.full_name || ""} onChange={set("full_name")} />
              </div>
              <div className="space-y-1.5">
                <Label>Email</Label>
                <Input type="email" required value={form.email || ""} onChange={set("email")} />
              </div>
              <div className="space-y-1.5">
                <Label>Password</Label>
                <Input type="password" required minLength={6} value={form.password || ""} onChange={set("password")} />
              </div>

              {role === "student" && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label>Branch</Label>
                      <Input value={form.branch || ""} onChange={set("branch")} placeholder="AI & Data Science" />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Year of study</Label>
                      <Input type="number" min={1} max={5} value={form.year_of_study || ""} onChange={set("year_of_study")} />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Career goal (optional)</Label>
                    <Input value={form.career_goal || ""} onChange={set("career_goal")} placeholder="Backend Developer" />
                  </div>
                </>
              )}

              {role === "college" && (
                <>
                  <div className="space-y-1.5">
                    <Label>College name</Label>
                    <Input required value={form.college_name || ""} onChange={set("college_name")} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>City</Label>
                    <Input value={form.city || ""} onChange={set("city")} />
                  </div>
                </>
              )}

              {role === "industry" && (
                <>
                  <div className="space-y-1.5">
                    <Label>Company name</Label>
                    <Input required value={form.company_name || ""} onChange={set("company_name")} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Industry sector</Label>
                    <Input value={form.industry_sector || ""} onChange={set("industry_sector")} placeholder="Software / Cloud" />
                  </div>
                </>
              )}

              <Button type="submit" className={cn("w-full")} disabled={submitting}>
                {submitting ? "Creating account…" : "Create account"}
              </Button>
            </form>
          </>
        )}

        <p className="mt-6 text-center text-sm text-muted">
          Already have an account? <Link to="/login" className="text-accent">Log in</Link>
        </p>
      </div>
    </div>
  )
}
