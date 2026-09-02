import { type ReactNode } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { ThemeToggle } from "./ThemeToggle"
import { Avatar } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { GraduationCap, LogOut } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
}

export function AppShell({ nav, children }: { nav: NavItem[]; children: ReactNode }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-surface md:flex">
        <Link to="/" className="flex items-center gap-2 px-6 py-5">
          <GraduationCap className="h-6 w-6 text-accent" />
          <span className="font-display text-lg">Gradustry</span>
        </Link>
        <nav className="flex-1 space-y-1 px-3">
          {nav.map((item) => {
            const active = location.pathname === item.to
            const Icon = item.icon
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active ? "bg-accent/15 text-accent" : "text-muted hover:bg-surface-alt hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="border-t border-border p-3">
          <button
            onClick={() => { logout(); navigate("/") }}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted hover:bg-surface-alt hover:text-danger"
          >
            <LogOut className="h-4 w-4" /> Log out
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface px-4 py-3 md:px-8">
          <div className="md:hidden flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-accent" />
            <span className="font-display">Gradustry</span>
          </div>
          <div className="hidden md:block" />
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <div className="flex items-center gap-2">
              <Avatar name={user?.full_name ?? "?"} />
              <div className="hidden text-sm sm:block">
                <p className="font-medium leading-tight">{user?.full_name}</p>
                <p className="capitalize leading-tight text-muted">{user?.role}</p>
              </div>
            </div>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">{children}</main>
        <nav className="fixed inset-x-0 bottom-0 z-10 flex justify-around border-t border-border bg-surface p-2 md:hidden">
          {nav.slice(0, 5).map((item) => {
            const Icon = item.icon
            const active = location.pathname === item.to
            return (
              <Link key={item.to} to={item.to} className={cn("flex flex-col items-center gap-0.5 px-2 py-1 text-[10px]", active ? "text-accent" : "text-muted")}>
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
