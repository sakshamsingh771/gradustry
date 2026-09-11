import { useQuery } from "@tanstack/react-query"
import { academicianApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const statusVariant: Record<string, "default" | "success" | "danger" | "warning" | "outline"> = {
  applied: "outline", accepted: "success", in_progress: "warning", completed: "success", rejected: "danger",
  shortlisted: "default", assessment: "warning", interview: "warning", selected: "success",
}

export default function AcademicianApplications() {
  const appsQ = useQuery({ queryKey: ["academician-applications"], queryFn: () => academicianApi.myApplications().then((r) => r.data) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Applications</h1>
        <p className="text-muted">Track every faculty opportunity you've registered interest in.</p>
      </div>
      <div className="space-y-3">
        {appsQ.data?.map((a) => (
          <Card key={a.id}>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
              <div>
                <p className="font-display text-base">{a.opportunity_title}</p>
                <p className="text-sm text-muted">{a.company_name} · Applied {new Date(a.applied_at).toLocaleDateString()}</p>
              </div>
              <Badge variant={statusVariant[a.status] ?? "outline"} className="capitalize">{a.status.replace("_", " ")}</Badge>
            </CardContent>
          </Card>
        ))}
        {appsQ.data?.length === 0 && <p className="text-sm text-muted">No applications yet — explore opportunities to get started.</p>}
      </div>
    </div>
  )
}
