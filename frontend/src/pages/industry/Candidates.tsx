import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Trash2, Plus } from "lucide-react"
import { toast } from "sonner"

const STUDENT_STATUSES = ["applied", "invited", "shortlisted", "assessment", "interview", "selected", "completed", "rejected"]
const ACADEMICIAN_STATUSES = ["applied", "accepted", "in_progress", "completed", "rejected"]

interface SkillRatingRow { skill_name: string; rating: number }

function FeedbackForm({ applicationId, onDone }: { applicationId: number; onDone: () => void }) {
  const [ratings, setRatings] = useState<SkillRatingRow[]>([{ skill_name: "", rating: 4 }])
  const [comments, setComments] = useState("")

  const mutation = useMutation({
    mutationFn: () =>
      opportunityApi.submitFeedback({
        application_id: applicationId,
        // Legacy holistic categories kept for backward compatibility with the
        // feedback record; skill Passport evidence is driven ONLY by skill_ratings below.
        technical_skill: 0, problem_solving: 0, communication: 0, teamwork: 0, professionalism: 0,
        comments,
        skill_ratings: ratings.filter((r) => r.skill_name.trim()),
      }),
    onSuccess: () => { toast.success("Feedback submitted — Skill Passport updated for the skills you rated"); onDone() },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Couldn't submit feedback"),
  })

  return (
    <div className="mt-3 space-y-2 rounded-md border border-border p-3">
      <p className="text-xs text-muted">Only rate skills you genuinely observed — each one becomes verified evidence on the student's Skill Passport.</p>
      {ratings.map((r, i) => (
        <div key={i} className="flex items-center gap-2">
          <Input placeholder="Skill (e.g. Python)" value={r.skill_name} onChange={(e) => setRatings((rs) => rs.map((row, idx) => idx === i ? { ...row, skill_name: e.target.value } : row))} />
          <Select className="w-28" value={r.rating} onChange={(e) => setRatings((rs) => rs.map((row, idx) => idx === i ? { ...row, rating: Number(e.target.value) } : row))}>
            {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n} / 5</option>)}
          </Select>
          <button type="button" onClick={() => setRatings((rs) => rs.filter((_, idx) => idx !== i))} className="text-muted hover:text-danger"><Trash2 className="h-4 w-4" /></button>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => setRatings((rs) => [...rs, { skill_name: "", rating: 4 }])}>
        <Plus className="h-3.5 w-3.5" /> Add rated skill
      </Button>
      <Input placeholder="Comments (optional)" value={comments} onChange={(e) => setComments(e.target.value)} />
      <div className="flex gap-2">
        <Button size="sm" disabled={mutation.isPending || !ratings.some((r) => r.skill_name.trim())} onClick={() => mutation.mutate()}>
          {mutation.isPending ? "Submitting…" : "Submit feedback"}
        </Button>
        <Button size="sm" variant="ghost" onClick={onDone}>Cancel</Button>
      </div>
    </div>
  )
}

export default function Candidates() {
  const qc = useQueryClient()
  const oppsQ = useQuery({ queryKey: ["my-opportunities"], queryFn: () => opportunityApi.mine().then((r) => r.data) })
  const [oppId, setOppId] = useState<number | null>(null)
  const [feedbackOpenFor, setFeedbackOpenFor] = useState<number | null>(null)

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
              <CardContent className="pt-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
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
                    {(a.status === "selected" || a.status === "completed") && a.applicant_type === "student" && (
                      <Button size="sm" variant="outline" onClick={() => setFeedbackOpenFor(feedbackOpenFor === a.id ? null : a.id)}>
                        {feedbackOpenFor === a.id ? "Close" : "Give feedback"}
                      </Button>
                    )}
                    <Badge variant={a.status === "completed" ? "success" : a.status === "rejected" ? "danger" : "outline"} className="capitalize">
                      {a.status.replace("_", " ")}
                    </Badge>
                  </div>
                </div>
                {feedbackOpenFor === a.id && (
                  <FeedbackForm applicationId={a.id} onDone={() => setFeedbackOpenFor(null)} />
                )}
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
