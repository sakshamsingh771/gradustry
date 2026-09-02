import { Outlet } from "react-router-dom"
import { AppShell, type NavItem } from "@/components/layout/AppShell"
import { LayoutDashboard, BadgeCheck, Target, FileStack, ClipboardList, Briefcase, ListChecks, FileUp, GitFork, Sparkles, Bot } from "lucide-react"

const nav: NavItem[] = [
  { label: "Dashboard", to: "/student", icon: LayoutDashboard },
  { label: "Skill Passport", to: "/student/passport", icon: BadgeCheck },
  { label: "Skill Gap", to: "/student/gap", icon: Target },
  { label: "Evidence", to: "/student/evidence", icon: FileStack },
  { label: "Assessments", to: "/student/assessments", icon: ClipboardList },
  { label: "AI Assessment", to: "/student/adaptive-assessment", icon: Sparkles },
  { label: "AI Roadmap", to: "/student/ai-roadmap", icon: Sparkles },
  { label: "Resume Analyzer", to: "/student/resume-analyzer", icon: FileUp },
  { label: "GitHub Analyzer", to: "/student/github-analyzer", icon: GitFork },
  { label: "Career Copilot", to: "/student/copilot", icon: Bot },
  { label: "Opportunities", to: "/student/opportunities", icon: Briefcase },
  { label: "Applications", to: "/student/applications", icon: ListChecks },
]

export default function StudentLayout() {
  return (
    <AppShell nav={nav}>
      <Outlet />
    </AppShell>
  )
}
