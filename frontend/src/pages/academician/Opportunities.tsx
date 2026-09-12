import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { academicianApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

const roleTypeLabels: Record<string, string> = {
  faculty_internship: "Faculty Internship",
  industrial_training: "Industrial Training",
  fdp: "Faculty Development Programme",
  consultancy: "Consultancy",
  research_collaboration: "Research Collaboration",
  guest_lecture: "Guest Lecture",
  mentorship: "Mentorship",
  workshop: "Workshop",
}

export default function AcademicianOpportunities() {
  const qc = useQueryClient()
  const oppsQ = useQuery({ queryKey: ["academician-opportunities"], queryFn: () => academicianApi.opportunities().then((r) => r.data) })
  const appsQ = useQuery({ queryKey: ["academician-applications"], queryFn: () => academicianApi.myApplications().then((r) => r.data) })

  const appliedIds = new Set((appsQ.data ?? []).map((a) => a.opportunity_id))

  const applyMutation = useMutation({
    mutationFn: (opportunityId: number) => academicianApi.apply(opportunityId),
    onSuccess: () => {
      toast.success("Applied — track its status under Applications")
      qc.invalidateQueries({ queryKey: ["academician-applications"] })
      qc.invalidateQueries({ queryKey: ["academician-dashboard"] })
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? "Couldn't apply"),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Opportunities for Faculty</h1>
        <p className="text-muted">FDPs, consultancy, research collaboration, guest lectures, and mentorship — posted by industry partners.</p>
      </div>

      <div className="space-y-3">
        {oppsQ.data?.map((o) => (
          <Card key={o.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle>{o.title}</CardTitle>
                  <CardDescription>{o.company_name} · {o.location}{o.stipend_or_ctc ? ` · ${o.stipend_or_ctc}` : ""}</CardDescription>
                </div>
                <Badge variant="default">{roleTypeLabels[o.role_type] ?? o.role_type}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted">{o.description}</p>
              <Button
                size="sm"
                disabled={appliedIds.has(o.id) || applyMutation.isPending}
                onClick={() => applyMutation.mutate(o.id)}
              >
                {appliedIds.has(o.id) ? "Applied" : applyMutation.isPending ? "Applying…" : "Apply / Register interest"}
              </Button>
            </CardContent>
          </Card>
        ))}
        {!oppsQ.data?.length && <p className="text-sm text-muted">No faculty opportunities are open right now — check back soon.</p>}
      </div>
    </div>
  )
}
