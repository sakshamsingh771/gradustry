import { Outlet } from "react-router-dom"
import { AppShell, type NavItem } from "@/components/layout/AppShell"
import { LayoutDashboard, User, Briefcase, ClipboardList, Users } from "lucide-react"

const nav: NavItem[] = [
  { label: "Dashboard", to: "/academician", icon: LayoutDashboard },
  { label: "Profile", to: "/academician/profile", icon: User },
  { label: "Opportunities", to: "/academician/opportunities", icon: Briefcase },
  { label: "Applications", to: "/academician/applications", icon: ClipboardList },
  { label: "Students", to: "/academician/students", icon: Users },
]

export default function AcademicianLayout() {
  return <AppShell nav={nav}><Outlet /></AppShell>
}
