import { useQuery } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function IndustryDashboard() {
  const oppsQ = useQuery({ queryKey: ["my-opportunities"], queryFn: () => opportunityApi.mine().then((r) => r.data) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Industry Dashboard</h1>
        <p className="text-muted">Manage postings and review explainable candidate matches.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Active Opportunities</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{oppsQ.data?.length ?? "—"}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Required Skills Tracked</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{new Set(oppsQ.data?.flatMap((o) => o.required_skills.map((s) => s.skill_name))).size || 0}</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle>Your postings</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {oppsQ.data?.map((o) => (
            <div key={o.id} className="flex items-center justify-between rounded-lg border border-border p-3">
              <div><p className="font-medium">{o.title}</p><p className="text-xs text-muted">{o.location} · {o.role_type}</p></div>
              <span className="text-xs text-muted">{o.required_skills.length} required skills</span>
            </div>
          ))}
          {!oppsQ.data?.length && <p className="text-sm text-muted">You haven't posted any opportunities yet.</p>}
        </CardContent>
      </Card>
    </div>
  )
}
