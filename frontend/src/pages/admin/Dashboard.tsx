import { useQuery } from "@tanstack/react-query"
import { adminApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function AdminDashboard() {
  const statsQ = useQuery({ queryKey: ["admin-stats"], queryFn: () => adminApi.stats().then((r) => r.data) })
  const s = statsQ.data
  const cards = [
    ["Students", s?.students], ["Colleges", s?.colleges], ["Companies", s?.companies],
    ["Opportunities", s?.opportunities], ["Applications", s?.applications],
    ["Pending Evidence", s?.pending_evidence], ["Pending Colleges", s?.pending_colleges],
    ["Pending Companies", s?.pending_companies], ["Career Roles", s?.career_roles],
  ]
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Platform Command Center</h1>
        <p className="text-muted">Cross-role oversight and moderation.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {cards.map(([label, val]) => (
          <Card key={label as string}>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">{label}</CardTitle></CardHeader>
            <CardContent><p className="font-display text-3xl">{val ?? "—"}</p></CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
