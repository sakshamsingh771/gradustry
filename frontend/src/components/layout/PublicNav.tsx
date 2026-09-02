import { Link, useNavigate } from "react-router-dom"
import { GraduationCap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "./ThemeToggle"

export function PublicNav() {
  const navigate = useNavigate()
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2">
          <GraduationCap className="h-6 w-6 text-accent" />
          <span className="font-display text-xl">Gradustry</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
          <a href="/#how-it-works" className="hover:text-foreground">How it works</a>
          <a href="/#passport" className="hover:text-foreground">Skill Passport</a>
          <Link to="/opportunities" className="hover:text-foreground">Opportunities</Link>
        </nav>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>Log in</Button>
          <Button size="sm" onClick={() => navigate("/register")}>Get started</Button>
        </div>
      </div>
    </header>
  )
}
