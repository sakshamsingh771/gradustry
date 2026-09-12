import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { collegeApi, type CollegeFilters } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Select } from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">{label}</CardTitle></CardHeader>
      <CardContent>
        <p className="font-display text-3xl">{value}</p>
        {sub && <p className="mt-1 text-xs text-muted">{sub}</p>}
      </CardContent>
    </Card>
  )
}

export default function CollegeDashboard() {
  const [filters, setFilters] = useState<CollegeFilters>({})
  const activeFilters = useMemo(
    () => Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")) as CollegeFilters,
    [filters],
  )

  const filterOptionsQ = useQuery({ queryKey: ["college-filters"], queryFn: () => collegeApi.filters().then((r) => r.data) })
  const dashQ = useQuery({ queryKey: ["college-dashboard", activeFilters], queryFn: () => collegeApi.dashboard(activeFilters).then((r) => r.data) })
  const skillsQ = useQuery({ queryKey: ["college-skills", activeFilters], queryFn: () => collegeApi.skillAnalytics(activeFilters).then((r) => r.data) })
  const internshipsQ = useQuery({ queryKey: ["college-internships", activeFilters], queryFn: () => collegeApi.internshipAnalytics(activeFilters).then((r) => r.data) })
  const collabQ = useQuery({ queryKey: ["college-collaboration"], queryFn: () => collegeApi.collaborationAnalytics().then((r) => r.data) })

  const d = dashQ.data
  const opts = filterOptionsQ.data

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl">{d?.college_name ?? "College"} Intelligence</h1>
          <p className="text-muted">Skill readiness, placements, and industry-academia collaboration across your institution.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Select className="w-40" value={filters.branch ?? ""} onChange={(e) => setFilters((f) => ({ ...f, branch: e.target.value || undefined }))}>
            <option value="">All departments</option>
            {opts?.branches.map((b) => <option key={b} value={b}>{b}</option>)}
          </Select>
          <Select className="w-32" value={filters.year_of_study ?? ""} onChange={(e) => setFilters((f) => ({ ...f, year_of_study: e.target.value ? Number(e.target.value) : undefined }))}>
            <option value="">All years</option>
            {opts?.years_of_study.map((y) => <option key={y} value={y}>Year {y}</option>)}
          </Select>
          <Select className="w-44" value={filters.career_goal ?? ""} onChange={(e) => setFilters((f) => ({ ...f, career_goal: e.target.value || undefined }))}>
            <option value="">All target roles</option>
            {opts?.career_goals.map((g) => <option key={g} value={g}>{g}</option>)}
          </Select>
          <Select className="w-36" value={filters.skill ?? ""} onChange={(e) => setFilters((f) => ({ ...f, skill: e.target.value || undefined }))}>
            <option value="">All skills</option>
            {opts?.skills.map((s) => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Students" value={d?.total_students ?? "—"} sub={`${d?.total_academicians ?? 0} academicians`} />
        <StatCard label="Average Readiness" value={`${d?.average_readiness ?? 0}%`} sub={`${d?.placement_readiness.ready_count ?? 0} placement-ready`} />
        <StatCard label="Internship Participation" value={`${d?.internship_participation.students_applied ?? 0}`} sub={`${d?.internship_participation.students_selected ?? 0} selected`} />
        <StatCard label="Industry Partners" value={d?.industry_collaboration.distinct_industry_partners ?? 0} sub={`${d?.industry_collaboration.total_engagements ?? 0} engagements`} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader><CardTitle className="text-sm">Students by skill level</CardTitle></CardHeader>
          <CardContent className="flex gap-2">
            <Badge variant="danger">Beginner: {d?.students_by_skill_level.Beginner ?? 0}</Badge>
            <Badge variant="warning">Intermediate: {d?.students_by_skill_level.Intermediate ?? 0}</Badge>
            <Badge variant="success">Advanced: {d?.students_by_skill_level.Advanced ?? 0}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Skill development (30-day)</CardTitle></CardHeader>
          <CardContent>
            {d?.skill_development_progress.has_data ? (
              <p className="text-sm">{d.skill_development_progress.previous_avg}% → {d.skill_development_progress.current_avg}%
                <span className={d.skill_development_progress.delta >= 0 ? "text-success" : "text-danger"}> ({d.skill_development_progress.delta >= 0 ? "+" : ""}{d.skill_development_progress.delta})</span>
              </p>
            ) : (
              <p className="text-sm text-muted">Not enough history yet — check back after 30 days of activity.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Opportunities</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm">{d?.opportunities.active_engaged ?? 0} active engaged · {d?.opportunities.completed_engagements ?? 0} completed</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="skills">
        <TabsList>
          <TabsTrigger value="skills">Skill Analytics</TabsTrigger>
          <TabsTrigger value="internships">Internships & Placement</TabsTrigger>
          <TabsTrigger value="collaboration">Collaboration</TabsTrigger>
        </TabsList>

        <TabsContent value="skills" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Top skills</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {skillsQ.data?.top_skills.map((s) => (
                  <div key={s.skill_name}>
                    <div className="mb-1 flex justify-between text-sm"><span>{s.skill_name}</span><span className="text-muted">{s.average_score}% avg · {s.student_count} students</span></div>
                    <Progress value={s.average_score} barClassName="bg-success" />
                  </div>
                ))}
                {!skillsQ.data?.top_skills.length && <p className="text-sm text-muted">No student skill data yet.</p>}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Common skill gaps</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {skillsQ.data?.common_gaps.map((g) => (
                  <div key={g.skill_name}>
                    <div className="mb-1 flex justify-between text-sm"><span>{g.skill_name}</span><span className="text-muted">{g.average_score}% avg · {g.student_count} students</span></div>
                    <Progress value={g.average_score} barClassName={g.average_score < 40 ? "bg-danger" : "bg-warning"} />
                  </div>
                ))}
                {!skillsQ.data?.common_gaps.length && <p className="text-sm text-muted">No student skill data yet.</p>}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader><CardTitle>Proficiency distribution</CardTitle></CardHeader>
            <CardContent className="h-64">
              {skillsQ.data?.proficiency_distribution.some((b) => b.count > 0) ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={skillsQ.data.proficiency_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="var(--color-accent, #6366f1)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <p className="text-sm text-muted">No proficiency data yet.</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Readiness trend</CardTitle></CardHeader>
            <CardContent className="h-64">
              {skillsQ.data?.readiness_trend.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={skillsQ.data.readiness_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="average_score" stroke="var(--color-accent, #6366f1)" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : <p className="text-sm text-muted">No history yet — trend appears once skill scores accumulate over time.</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Emerging / in-demand skills</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {skillsQ.data?.emerging_skills.map((e) => (
                <div key={e.skill_name} className="flex items-center justify-between text-sm">
                  <span>{e.skill_name}</span>
                  <span className="text-muted">{e.opportunities_requiring} active opportunities require it · {e.students_with_skill} of your students have it</span>
                </div>
              ))}
              {!skillsQ.data?.emerging_skills.length && <p className="text-sm text-muted">No active opportunities with skill requirements yet.</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="internships" className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total Applications" value={internshipsQ.data?.total_applications ?? 0} />
            <StatCard label="In Process" value={internshipsQ.data?.in_process ?? 0} sub="shortlisted / assessment / interview" />
            <StatCard label="Selected" value={internshipsQ.data?.selected ?? 0} />
            <StatCard label="Rejected" value={internshipsQ.data?.rejected ?? 0} />
          </div>
          <Card>
            <CardHeader><CardTitle>Applications over time</CardTitle></CardHeader>
            <CardContent className="h-64">
              {internshipsQ.data?.monthly_trend.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={internshipsQ.data.monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="applications" stroke="var(--color-accent, #6366f1)" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : <p className="text-sm text-muted">No applications yet.</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="collaboration" className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Academicians engaged" value={collabQ.data?.total_academicians ?? 0} />
            <StatCard label="Total engagements" value={collabQ.data?.total_engagements ?? 0} />
            <StatCard label="Distinct industry partners" value={collabQ.data?.distinct_industry_partners ?? 0} />
          </div>
          <Card>
            <CardHeader><CardTitle>By category</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {collabQ.data?.by_category.map((c) => (
                <div key={c.category} className="flex items-center justify-between text-sm">
                  <span className="capitalize">{c.category.replace("_", " ")}</span>
                  <div className="flex gap-1">
                    {Object.entries(c.by_status).map(([status, count]) => (
                      <span key={status} className="rounded-full bg-surface-alt px-2 py-0.5 text-xs capitalize">{status}: {count}</span>
                    ))}
                  </div>
                </div>
              ))}
              {!collabQ.data?.by_category.length && (
                <p className="text-sm text-muted">No academician-industry engagements yet — link and verify faculty from the Academician module to see activity here.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
