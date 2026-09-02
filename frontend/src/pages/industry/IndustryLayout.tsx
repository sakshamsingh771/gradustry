import { Outlet } from "react-router-dom"
import { AppShell, type NavItem } from "@/components/layout/AppShell"
import { LayoutDashboard, Briefcase, Users } from "lucide-react"

const nav: NavItem[] = [
  { label: "Dashboard", to: "/industry", icon: LayoutDashboard },
  { label: "Opportunities", to: "/industry/opportunities", icon: Briefcase },
  { label: "Candidates", to: "/industry/candidates", icon: Users },
]

export default function IndustryLayout() {
  return <AppShell nav={nav}><Outlet /></AppShell>
}
