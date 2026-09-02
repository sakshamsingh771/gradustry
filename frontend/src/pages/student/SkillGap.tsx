import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { gapApi, studentApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { GapCard } from "@/components/domain/GapCard"
import { Progress } from "@/components/ui/progress"
import { toast } from "sonner"
import { useNavigate } from "react-router-dom"

export default function SkillGap() {
  const navigate = useNavigate()
  const passportQ = useQuery({ queryKey: ["skill-passport"], queryFn: () => studentApi.skillPassport().then((r) => r.data) })
  const rolesQ = useQuery({ queryKey: ["career-roles"], queryFn: () => gapApi.roles().then((r) => r.data as { title: string }[]) })
  const [roleTitle, setRoleTitle] = useState(passportQ.data?.career_goal || "Backend Developer")

  const reportQ = useQuery({
    queryKey: ["gap-report", roleTitle],
    queryFn: () => gapApi.report(roleTitle).then((r) => r.data),
    enabled: !!roleTitle,
    retry: false,
  })

  const roadmapMutation = useMutation({
    mutationFn: (skillName: string) => gapApi.generateRoadmap(skillName, 70),
    onSuccess: (_res, skillName) => {
      toast.success(`Roadmap generated for ${skillName}`)
      navigate(`/student/assessments?skill=${encodeURIComponent(skillName)}`)
    },
  })

  const report = reportQ.data

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl">Skill Gap Engine</h1>
          <p className="text-muted">Compare your demonstrated skills against a target career role.</p>
        </div>
        <Select value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} className="w-64">
          {rolesQ.data?.map((r) => <option key={r.title} value={r.title}>{r.title}</option>)}
        </Select>
      </div>

      {report && (
        <Card>
          <CardHeader><CardTitle>Career Readiness for {report.role_title}</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <p className="font-display text-4xl text-accent">{report.career_readiness}%</p>
              <Progress value={report.career_readiness} className="flex-1" />
            </div>
          </CardContent>
        </Card>
      )}

      {report && (
        <div className="grid gap-6 md:grid-cols-2">
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">High gaps</h2>
            {report.high_gap.map((g) => <GapCard key={g.skill_name} item={g} onBuildRoadmap={() => roadmapMutation.mutate(g.skill_name)} />)}
            {!report.high_gap.length && <p className="text-sm text-muted">None — nice work.</p>}

            <h2 className="pt-4 text-sm font-semibold uppercase tracking-wide text-muted">Medium gaps</h2>
            {report.medium_gap.map((g) => <GapCard key={g.skill_name} item={g} onBuildRoadmap={() => roadmapMutation.mutate(g.skill_name)} />)}
            {!report.medium_gap.length && <p className="text-sm text-muted">None.</p>}
          </section>
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Low gaps</h2>
            {report.low_gap.map((g) => <GapCard key={g.skill_name} item={g} onBuildRoadmap={() => roadmapMutation.mutate(g.skill_name)} />)}
            {!report.low_gap.length && <p className="text-sm text-muted">None.</p>}

            <h2 className="pt-4 text-sm font-semibold uppercase tracking-wide text-muted">Matched</h2>
            {report.matched.map((g) => <GapCard key={g.skill_name} item={g} />)}
            {!report.matched.length && <p className="text-sm text-muted">None yet.</p>}
          </section>
        </div>
      )}

      {reportQ.isError && (
        <Card><CardContent className="pt-5 text-sm text-muted">No requirements found for this role yet — pick another, or ask an admin to add it.</CardContent></Card>
      )}
    </div>
  )
}
