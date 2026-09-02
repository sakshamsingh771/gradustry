import { Outlet } from "react-router-dom"
import { AppShell, type NavItem } from "@/components/layout/AppShell"
import { LayoutDashboard, Users } from "lucide-react"

const nav: NavItem[] = [
  { label: "Dashboard", to: "/college", icon: LayoutDashboard },
  { label: "Students", to: "/college/students", icon: Users },
]

export default function CollegeLayout() {
  return <AppShell nav={nav}><Outlet /></AppShell>
}
