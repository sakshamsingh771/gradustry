import { useEffect, useRef, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import { GraduationCap, LogOut, LayoutDashboard, Menu, X } from "lucide-react"
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
// College/industry/admin have no separate profile route in this project,
// so their "Profile" action falls back to their dashboard rather than
// pointing at a page that doesn't exist.
const roleProfile: Record<Role, string> = {
  student: "/student/passport",
  college: "/college",
  industry: "/industry",
  admin: "/admin",
}

// Role-specific secondary link shown next to Dashboard/Profile/Logout.
// Every "to" here is a real route that already exists in App.tsx.
const roleLinks: Record<Role, { label: string; to: string }[]> = {
  student: [{ label: "Opportunities", to: "/student/opportunities" }],
  college: [{ label: "Students", to: "/college/students" }],
  industry: [
    { label: "Talent", to: "/industry/candidates" },
    { label: "Opportunities", to: "/industry/opportunities" },
  ],
  admin: [{ label: "Moderation", to: "/admin/moderation" }],
}

const publicLinks = [
  { label: "Home", to: "/" },
  { label: "Opportunities", to: "/opportunities" },
  { label: "Skill Intelligence", to: "/student/gap" },
  { label: "Roadmap", to: "/student/ai-roadmap" },
]

export function PublicNav() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  const handleLogout = () => {
    logout()
    setMobileOpen(false)
    navigate("/")
  }

  const go = (to: string) => {
    setMobileOpen(false)
    navigate(to)
  }

  // Close on Escape
  useEffect(() => {
    if (!mobileOpen) return
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setMobileOpen(false) }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [mobileOpen])

  // Close on outside click
  useEffect(() => {
    if (!mobileOpen) return
    const onClick = (e: MouseEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) setMobileOpen(false)
    }
    document.addEventListener("mousedown", onClick)
    return () => document.removeEventListener("mousedown", onClick)
  }, [mobileOpen])

  const mobileNavItems = user
    ? [...roleLinks[user.role], { label: "Dashboard", to: roleHome[user.role] }, { label: "Profile", to: roleProfile[user.role] }]
    : publicLinks

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2">
          <GraduationCap className="h-6 w-6 text-accent" />
          <span className="font-display text-xl">Gradustry</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-7 text-sm text-muted md:flex">
          <Link to="/" className="hover:text-foreground">Home</Link>
          <Link to="/opportunities" className="hover:text-foreground">Opportunities</Link>
          <Link to="/student/gap" className="hover:text-foreground">Skill Intelligence</Link>
          <Link to="/student/ai-roadmap" className="hover:text-foreground">Roadmap</Link>
          {user && roleLinks[user.role].map((l) => (
            <Link key={l.to} to={l.to} className="hover:text-foreground">{l.label}</Link>
          ))}
        </nav>

        {/* Desktop right side */}
        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle />
          {user ? (
            <>
              <button
                onClick={() => navigate(roleProfile[user.role])}
                className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-surface-alt"
              >
                <Avatar name={user.full_name} className="h-8 w-8 text-xs" />
                <span className="text-sm font-medium">{user.full_name.split(" ")[0]}</span>
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

        {/* Mobile: hamburger only */}
        <button
          className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-surface-alt md:hidden"
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileOpen}
          aria-controls="mobile-nav-drawer"
          onClick={() => setMobileOpen((v) => !v)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-nav-drawer"
            ref={drawerRef}
            role="dialog"
            aria-label="Mobile navigation"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-border bg-background md:hidden"
          >
            <nav className="flex flex-col gap-1 px-4 py-4">
              {mobileNavItems.map((item) => (
                <button
                  key={item.to}
                  onClick={() => go(item.to)}
                  className="rounded-md px-3 py-2 text-left text-sm font-medium text-muted hover:bg-surface-alt hover:text-foreground"
                >
                  {item.label}
                </button>
              ))}

              <div className="mt-2 flex items-center justify-between border-t border-border pt-3">
                <ThemeToggle />
                {user ? (
                  <Button variant="ghost" size="sm" onClick={handleLogout}>
                    <LogOut className="h-4 w-4" /> Logout
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={() => go("/login")}>Log in</Button>
                    <Button size="sm" onClick={() => go("/register")}>Sign up</Button>
                  </div>
                )}
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}