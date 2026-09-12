import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

const STUDENT_STATUSES = ["applied", "shortlisted", "assessment", "interview", "selected", "completed", "rejected"]
const ACADEMICIAN_STATUSES = ["applied", "accepted", "in_progress", "completed", "rejected"]

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
    onSuccess: (_res, vars) => {
      toast.success(vars.status === "completed" ? "Marked completed — Skill Passport updated for any required skills" : "Status updated")
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
        <h1 className="font-display text-2xl">Candidates & Participants</h1>
        <Select className="w-72" value={oppId ?? ""} onChange={(e) => setOppId(Number(e.target.value))}>
          <option value="">Select an opportunity or program</option>
          {oppsQ.data?.map((o) => <option key={o.id} value={o.id}>{o.title}</option>)}
        </Select>
      </div>

      <div className="space-y-3">
        {appsQ.data?.map((a) => {
          const statuses = a.applicant_type === "academician" ? ACADEMICIAN_STATUSES : STUDENT_STATUSES
          const name = a.applicant_type === "academician" ? a.academician_name : a.student_name
          return (
            <Card key={a.id}>
              <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
                <div>
                  <p className="font-display text-base">{name}</p>
                  <p className="text-sm text-muted">
                    {a.applicant_type === "academician" ? "Academician" : "Student"}
                    {a.applicant_type === "student" ? ` · Match ${a.match_score.toFixed(0)}%` : ""} · Applied {new Date(a.applied_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Select className="w-40" value={a.status} onChange={(e) => statusMutation.mutate({ id: a.id, status: e.target.value })}>
                    {statuses.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </Select>
                  {a.status === "selected" && a.applicant_type === "student" && (
                    <Button size="sm" variant="outline" onClick={() => feedbackMutation.mutate(a.id)}>Submit feedback</Button>
                  )}
                  <Badge variant={a.status === "completed" ? "success" : a.status === "rejected" ? "danger" : "outline"} className="capitalize">
                    {a.status.replace("_", " ")}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )
        })}
        {oppId && appsQ.data?.length === 0 && <p className="text-sm text-muted">No applications yet for this opportunity.</p>}
        {!oppId && <p className="text-sm text-muted">Select an opportunity or Learning Hub program above to manage its participants.</p>}
      </div>
    </div>
  )
}
