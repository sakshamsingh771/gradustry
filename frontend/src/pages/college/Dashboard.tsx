import { useQuery } from "@tanstack/react-query"
import { collegeApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

export default function CollegeDashboard() {
  const dashQ = useQuery({ queryKey: ["college-dashboard"], queryFn: () => collegeApi.dashboard().then((r) => r.data) })
  const d = dashQ.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">{d?.college_name ?? "College"} Intelligence</h1>
        <p className="text-muted">Skill readiness and industry-demand insight across your students.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Total Students</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{d?.total_students ?? "—"}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Average Readiness</CardTitle></CardHeader><CardContent><p className="font-display text-3xl text-accent">{d?.average_readiness ?? "—"}%</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Placements (selected / applied)</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{d?.placement_stats?.selected ?? 0} / {d?.placement_stats?.applications ?? 0}</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Top skill gaps across your students</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {d?.top_gaps?.map((g: any) => (
            <div key={g.skill_name}>
              <div className="mb-1 flex justify-between text-sm"><span>{g.skill_name}</span><span className="text-muted">{g.average_score}% avg · {g.student_count} students</span></div>
              <Progress value={g.average_score} barClassName={g.average_score < 40 ? "bg-danger" : g.average_score < 65 ? "bg-warning" : "bg-success"} />
            </div>
          ))}
          {!d?.top_gaps?.length && <p className="text-sm text-muted">No student skill data yet.</p>}
        </CardContent>
      </Card>
    </div>
  )
}
