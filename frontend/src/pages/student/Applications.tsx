import { useQuery } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const STAGES = ["applied", "shortlisted", "assessment", "interview", "selected"]
const statusVariant: Record<string, "default" | "success" | "danger" | "warning" | "outline"> = {
  applied: "outline", shortlisted: "default", assessment: "warning", interview: "warning", selected: "success", rejected: "danger",
}

export default function Applications() {
  const appsQ = useQuery({ queryKey: ["my-applications"], queryFn: () => opportunityApi.myApplications().then((r) => r.data) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Applications</h1>
        <p className="text-muted">Track every opportunity you've applied to.</p>
      </div>
      <div className="space-y-3">
        {appsQ.data?.map((a) => (
          <Card key={a.id}>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
              <div>
                <p className="font-display text-base">{a.opportunity_title}</p>
                <p className="text-sm text-muted">{a.company_name} · Applied {new Date(a.applied_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted">Match {a.match_score.toFixed(0)}%</span>
                <Badge variant={statusVariant[a.status] ?? "outline"} className="capitalize">{a.status}</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
        {appsQ.data?.length === 0 && <p className="text-sm text-muted">No applications yet — explore opportunities to get started.</p>}
      </div>
    </div>
  )
}
