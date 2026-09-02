import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { studentApi, opportunityApi, aiApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useAuth } from "@/context/AuthContext"
import { Sparkles, FileUp, GitFork, Bot } from "lucide-react"

const COMPONENT_LABELS: Record<string, string> = {
  skills: "Skills", assessments: "Assessments", evidence: "Evidence",
  projects: "Projects", industry_feedback: "Industry feedback", consistency: "Consistency",
}

export default function StudentDashboard() {
  const { user } = useAuth()
  const passportQ = useQuery({ queryKey: ["skill-passport"], queryFn: () => studentApi.skillPassport().then((r) => r.data) })
  const matchesQ = useQuery({ queryKey: ["matches"], queryFn: () => opportunityApi.matches().then((r) => r.data) })
  const appsQ = useQuery({ queryKey: ["my-applications"], queryFn: () => opportunityApi.myApplications().then((r) => r.data) })
  const insightsQ = useQuery({ queryKey: ["ai-insights"], queryFn: () => aiApi.insights().then((r) => r.data) })

  const passport = passportQ.data
  const verifiedSkills = passport?.skills.filter((s) => s.confidence_level === "High").length ?? 0
  const evidenceCount = passport?.skills.reduce((acc, s) => acc + s.evidence_count, 0) ?? 0
  const bestMatch = matchesQ.data?.[0]
  const hour = new Date().getHours()
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening"

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">{greeting}, {user?.full_name.split(" ")[0]}</h1>
        <p className="text-muted">Here's where your skill journey stands today.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Career Readiness</CardTitle></CardHeader>
          <CardContent>
            <p className="font-display text-3xl text-accent">{passport?.career_readiness ?? "—"}%</p>
            <Progress value={passport?.career_readiness ?? 0} className="mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Verified Skills</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{verifiedSkills}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Evidence Count</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{evidenceCount}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Recommended</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{matchesQ.data?.length ?? "—"}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Active Applications</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{appsQ.data?.filter((a) => !["rejected", "selected"].includes(a.status)).length ?? "—"}</p></CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Skill overview</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {passport?.skills.slice(0, 6).map((s) => (
              <div key={s.id}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{s.skill_name}</span>
                  <span className="text-muted">{s.proficiency_score.toFixed(0)}%</span>
                </div>
                <Progress value={s.proficiency_score} barClassName={s.proficiency_score < 40 ? "bg-danger" : s.proficiency_score < 65 ? "bg-warning" : "bg-success"} />
              </div>
            ))}
            {!passport?.skills.length && <p className="text-sm text-muted">No skills tracked yet — add evidence to get started.</p>}
            <Link to="/student/passport" className="inline-block pt-2 text-sm text-accent">View full Skill Passport →</Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center gap-2 space-y-0"><Sparkles className="h-4 w-4 text-accent" /><CardTitle>AI Insights</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {insightsQ.data ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted">Overall readiness</span>
                  <span className="font-display text-xl text-accent">{insightsQ.data.overall_readiness}%</span>
                </div>
                {Object.entries(insightsQ.data.components).map(([key, val]) => (
                  <div key={key}>
                    <div className="mb-1 flex justify-between text-xs text-muted">
                      <span>{COMPONENT_LABELS[key] ?? key} ({(insightsQ.data!.weights[key] * 100).toFixed(0)}%)</span>
                      <span>{val as number}%</span>
                    </div>
                    <Progress value={val as number} className="h-1.5" />
                  </div>
                ))}
                {bestMatch && (
                  <div className="rounded-lg bg-surface-alt p-3 text-sm">
                    <p className="text-xs text-muted">Best opportunity</p>
                    <p className="font-medium">{bestMatch.opportunity.title}</p>
                    <p className="text-xs text-accent">Match: {bestMatch.match_score.toFixed(0)}%</p>
                  </div>
                )}
              </>
            ) : <p className="text-sm text-muted">Add skills and evidence to unlock AI Insights.</p>}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Link to="/student/resume-analyzer" className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 hover:border-accent">
          <FileUp className="h-5 w-5 text-accent" /><div><p className="font-medium">AI Resume Analyzer</p><p className="text-xs text-muted">Extract skills from your resume</p></div>
        </Link>
        <Link to="/student/github-analyzer" className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 hover:border-accent">
          <GitFork className="h-5 w-5 text-accent" /><div><p className="font-medium">AI GitHub Analyzer</p><p className="text-xs text-muted">Analyze a project repository</p></div>
        </Link>
        <Link to="/student/copilot" className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 hover:border-accent">
          <Bot className="h-5 w-5 text-accent" /><div><p className="font-medium">Career Copilot</p><p className="text-xs text-muted">Ask "Am I ready?"</p></div>
        </Link>
      </div>
    </div>
  )
}
