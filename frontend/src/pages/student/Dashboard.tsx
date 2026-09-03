import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { studentApi, opportunityApi, aiApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/context/AuthContext"
import { Sparkles, FileUp, GitFork, Bot, Target, User, Briefcase, ClipboardList, CheckCircle2, AlertTriangle } from "lucide-react"

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
  const profileQ = useQuery({ queryKey: ["my-profile"], queryFn: () => studentApi.myProfile().then((r) => r.data) })
  const activityQ = useQuery({ queryKey: ["activity-status"], queryFn: () => studentApi.activityStatus().then((r) => r.data) })

  const passport = passportQ.data
  const strength = profileQ.data?.strength
  const evidenceCount = passport?.skills.reduce((acc, s) => acc + s.evidence_count, 0) ?? 0
  const bestMatch = matchesQ.data?.[0]
  const hour = new Date().getHours()
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening"

  // --- Next Best Action: derived from real data, first matching rule wins ---
  const nextAction = (() => {
    if (strength && strength.score < 60) return { text: "Your profile is incomplete — finish it to unlock better matches.", cta: "Complete Profile", to: "/student/profile" }
    if (activityQ.data && !activityQ.data.resume_analyzed) return { text: "Your resume hasn't been analyzed yet.", cta: "Analyze Resume", to: "/student/resume-analyzer" }
    const weakest = passport?.skills.filter((s) => s.evidence_count === 0).sort((a, b) => b.proficiency_score - a.proficiency_score)[0]
    if (weakest) return { text: `${weakest.skill_name} has no supporting evidence yet.`, cta: `Strengthen ${weakest.skill_name}`, to: "/student/evidence" }
    const noAssessment = passport?.skills.find((s) => !s.last_assessed_at)
    if (noAssessment) return { text: `You haven't been assessed on ${noAssessment.skill_name} yet.`, cta: "Take Assessment", to: "/student/adaptive-assessment" }
    return { text: "You're in good shape — keep exploring opportunities that fit.", cta: "Explore Opportunities", to: "/student/opportunities" }
  })()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">{greeting}, {user?.full_name.split(" ")[0]}</h1>
        <p className="text-muted">Here's where you stand and what you should do next.</p>
      </div>

      {/* CAREER SNAPSHOT */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Career Readiness</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl text-accent">{passport?.career_readiness ?? "—"}%</p><Progress value={passport?.career_readiness ?? 0} className="mt-2" /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Profile Strength</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{strength?.score ?? "—"}%</p><Progress value={strength?.score ?? 0} className="mt-2" /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Skills Tracked</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{passport?.skills.length ?? "—"}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted font-normal">Evidence Items</CardTitle></CardHeader>
          <CardContent><p className="font-display text-3xl">{evidenceCount}</p></CardContent>
        </Card>
      </div>

      {/* NEXT BEST ACTION */}
      <Card className="border-accent/40 bg-accent/5">
        <CardContent className="flex flex-col items-start gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Target className="h-5 w-5 shrink-0 text-accent" />
            <p className="font-medium">{nextAction.text}</p>
          </div>
          <Link to={nextAction.to} className="shrink-0 rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:opacity-90">
            {nextAction.cta}
          </Link>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Skill Intelligence</CardTitle></CardHeader>
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
            <Link to="/student/gap" className="inline-block pt-2 text-sm text-accent">View full Skill Gap analysis →</Link>
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
              </>
            ) : <p className="text-sm text-muted">Add skills and evidence to unlock AI Insights.</p>}
            <Link to="/student/copilot" className="inline-block pt-1 text-sm text-accent">Ask Career Copilot →</Link>
          </CardContent>
        </Card>
      </div>

      {/* RESUME / GITHUB HEALTH */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div className="flex items-center gap-3">
              <FileUp className="h-5 w-5 text-accent" />
              <div>
                <p className="font-medium">Resume</p>
                {activityQ.data?.resume_analyzed ? (
                  <p className="flex items-center gap-1 text-xs text-success"><CheckCircle2 className="h-3 w-3" /> Analyzed · {activityQ.data.resume_skills_detected} skills detected</p>
                ) : (
                  <p className="flex items-center gap-1 text-xs text-warning"><AlertTriangle className="h-3 w-3" /> Not analyzed</p>
                )}
              </div>
            </div>
            <Link to="/student/resume-analyzer" className="text-sm text-accent">{activityQ.data?.resume_analyzed ? "Re-analyze" : "Analyze"}</Link>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div className="flex items-center gap-3">
              <GitFork className="h-5 w-5 text-accent" />
              <div>
                <p className="font-medium">GitHub</p>
                {activityQ.data?.github_connected ? (
                  <p className="flex items-center gap-1 text-xs text-success"><CheckCircle2 className="h-3 w-3" /> {activityQ.data.github_repos_analyzed} repositories analyzed</p>
                ) : (
                  <p className="flex items-center gap-1 text-xs text-warning"><AlertTriangle className="h-3 w-3" /> Not connected</p>
                )}
              </div>
            </div>
            <Link to="/student/github-analyzer" className="text-sm text-accent">{activityQ.data?.github_connected ? "Analyze more" : "Connect"}</Link>
          </CardContent>
        </Card>
      </div>

      {/* OPPORTUNITY MATCHING */}
      <Card>
        <CardHeader className="flex-row items-center gap-2 space-y-0"><Briefcase className="h-4 w-4 text-accent" /><CardTitle>Best matches for you</CardTitle></CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {matchesQ.data?.slice(0, 3).map((m) => (
            <div key={m.opportunity.id} className="rounded-lg border border-border p-3">
              <p className="font-medium">{m.opportunity.title}</p>
              <p className="text-xs text-muted">{m.opportunity.company_name}</p>
              <Badge className="mt-2" variant={m.match_score >= 70 ? "success" : "outline"}>{m.match_score.toFixed(0)}% Match</Badge>
              {m.explanation.below_target_skills.length > 0 && (
                <p className="mt-2 text-xs text-warning">Missing: {m.explanation.below_target_skills.join(", ")}</p>
              )}
            </div>
          ))}
          {!matchesQ.data?.length && <p className="text-sm text-muted">No matches yet — add skills and evidence to unlock recommendations.</p>}
        </CardContent>
      </Card>

      {/* QUICK ACTIONS */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Link to="/student/profile" className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 hover:border-accent">
          <User className="h-5 w-5 text-accent" /><div><p className="font-medium">Edit Profile</p><p className="text-xs text-muted">Update your career identity</p></div>
        </Link>
        <Link to="/student/adaptive-assessment" className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 hover:border-accent">
          <ClipboardList className="h-5 w-5 text-accent" /><div><p className="font-medium">Take Assessment</p><p className="text-xs text-muted">Prove a skill</p></div>
        </Link>
        <Link to="/student/copilot" className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 hover:border-accent">
          <Bot className="h-5 w-5 text-accent" /><div><p className="font-medium">Career Copilot</p><p className="text-xs text-muted">Ask "Am I ready?"</p></div>
        </Link>
      </div>
    </div>
  )
}