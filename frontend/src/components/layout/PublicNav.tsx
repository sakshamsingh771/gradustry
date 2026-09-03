import { Link, useNavigate } from "react-router-dom"
import { GraduationCap, LogOut, LayoutDashboard } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar } from "@/components/ui/avatar"
import { ThemeToggle } from "./ThemeToggle"
import { useAuth } from "@/context/AuthContext"
import type { Role } from "@/lib/api"

const roleHome: Record<Role, string> = {
  student: "/student",
  college: "/college",
  industry: "/industry",
  admin: "/admin",
}

// Only the student role has a dedicated "profile" page (Skill Passport).
// Other roles land on their dashboard — we don't invent routes that don't exist.
const roleProfile: Record<Role, string> = {
  student: "/student/passport",
  college: "/college",
  industry: "/industry",
  admin: "/admin",
}

export function PublicNav() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate("/")
  }

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2">
          <GraduationCap className="h-6 w-6 text-accent" />
          <span className="font-display text-xl">Gradustry</span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
          <Link to="/opportunities" className="hover:text-foreground">Opportunities</Link>
          <Link to="/student/gap" className="hover:text-foreground">Skill Intelligence</Link>
          <Link to="/student/ai-roadmap" className="hover:text-foreground">Roadmap</Link>
          <a href="/#why-gradustry" className="hover:text-foreground">About</a>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />

          {user ? (
            <>
              <button
                onClick={() => navigate(roleProfile[user.role])}
                className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-surface-alt"
              >
                <Avatar name={user.full_name} className="h-8 w-8 text-xs" />
                <span className="hidden text-sm font-medium sm:block">{user.full_name.split(" ")[0]}</span>
              </button>
              <Button variant="outline" size="sm" onClick={() => navigate(roleHome[user.role])}>
                <LayoutDashboard className="h-4 w-4" /> Dashboard
              </Button>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" /> Logout
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>Log in</Button>
              <Button size="sm" onClick={() => navigate("/register")}>Get started</Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}