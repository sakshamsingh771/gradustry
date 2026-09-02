import { Outlet } from "react-router-dom"
import { AppShell, type NavItem } from "@/components/layout/AppShell"
import { LayoutDashboard, ShieldAlert, School, Building2 } from "lucide-react"

const nav: NavItem[] = [
  { label: "Dashboard", to: "/admin", icon: LayoutDashboard },
  { label: "Moderation", to: "/admin/moderation", icon: ShieldAlert },
  { label: "Colleges", to: "/admin/colleges", icon: School },
  { label: "Companies", to: "/admin/companies", icon: Building2 },
]

export default function AdminLayout() {
  return <AppShell nav={nav}><Outlet /></AppShell>
}
