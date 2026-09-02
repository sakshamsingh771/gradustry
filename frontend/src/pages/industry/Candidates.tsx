import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

const STATUSES = ["applied", "shortlisted", "assessment", "interview", "selected", "rejected"]

export default function Candidates() {
  const qc = useQueryClient()
  const oppsQ = useQuery({ queryKey: ["my-opportunities"], queryFn: () => opportunityApi.mine().then((r) => r.data) })
  const [oppId, setOppId] = useState<number | null>(null)

  const appsQ = useQuery({
    queryKey: ["opportunity-applications", oppId],
    queryFn: () => opportunityApi.applicationsFor(oppId!).then((r) => r.data),
    enabled: !!oppId,
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => opportunityApi.updateStatus(id, status),
    onSuccess: () => {
      toast.success("Status updated")
      qc.invalidateQueries({ queryKey: ["opportunity-applications", oppId] })
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: (applicationId: number) =>
      opportunityApi.submitFeedback({
        application_id: applicationId, technical_skill: 8, problem_solving: 8,
        communication: 7.5, teamwork: 8, professionalism: 8, comments: "Strong performance overall.",
      }),
    onSuccess: () => toast.success("Feedback submitted — added to student's Skill Passport"),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl">Candidates</h1>
        <Select className="w-64" value={oppId ?? ""} onChange={(e) => setOppId(Number(e.target.value))}>
          <option value="">Select an opportunity</option>
          {oppsQ.data?.map((o) => <option key={o.id} value={o.id}>{o.title}</option>)}
        </Select>
      </div>

      <div className="space-y-3">
        {appsQ.data?.map((a) => (
          <Card key={a.id}>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
              <div>
                <p className="font-display text-base">{a.student_name}</p>
                <p className="text-sm text-muted">Match {a.match_score.toFixed(0)}% · Applied {new Date(a.applied_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-2">
                <Select className="w-40" value={a.status} onChange={(e) => statusMutation.mutate({ id: a.id, status: e.target.value })}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
                {a.status === "selected" && (
                  <Button size="sm" variant="outline" onClick={() => feedbackMutation.mutate(a.id)}>Submit feedback</Button>
                )}
                <Badge variant="outline">{a.match_score >= 80 ? "Strong fit" : a.match_score >= 60 ? "Good fit" : "Developing fit"}</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
        {oppId && appsQ.data?.length === 0 && <p className="text-sm text-muted">No applications yet for this opportunity.</p>}
        {!oppId && <p className="text-sm text-muted">Select an opportunity above to see its candidates.</p>}
      </div>
    </div>
  )
}
