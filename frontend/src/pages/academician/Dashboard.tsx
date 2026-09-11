import { useQuery } from "@tanstack/react-query"
import { academicianApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function AcademicianDashboard() {
  const dashQ = useQuery({ queryKey: ["academician-dashboard"], queryFn: () => academicianApi.dashboard().then((r) => r.data) })
  const d = dashQ.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Welcome, {d?.full_name ?? "…"}</h1>
        <p className="text-muted">{d?.designation}{d?.designation && d?.institution ? " · " : ""}{d?.institution}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Open opportunities for you</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{d?.open_opportunities ?? "—"}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Applications submitted</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{d?.applications_total ?? "—"}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-normal text-muted">Students visible to you</CardTitle></CardHeader><CardContent><p className="font-display text-3xl">{d?.total_students_visible ?? "—"}</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>College affiliation</CardTitle></CardHeader>
        <CardContent>
          {d?.college_name ? (
            <div className="flex items-center gap-2">
              <span>{d.college_name}</span>
              <Badge variant={d.college_membership_status === "verified" ? "success" : "warning"}>
                {d.college_membership_status}
              </Badge>
            </div>
          ) : (
            <p className="text-sm text-muted">You haven't linked a college yet. Do this from your Profile page.</p>
          )}
        </CardContent>
      </Card>

      {d?.applications_total ? (
        <Card>
          <CardHeader><CardTitle>Applications by status</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {Object.entries(d.applications_by_status).map(([status, count]) => (
              <span key={status} className="rounded-full bg-surface-alt px-2.5 py-1 text-xs capitalize">{status.replace("_", " ")}: {count}</span>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
