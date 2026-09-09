import { useParams, useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { gapApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

export default function SkillRoadmapView() {
  const { skillName = "" } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const roadmapQ = useQuery({
    queryKey: ["roadmap", skillName],
    queryFn: () => gapApi.getRoadmap(skillName).then((r) => r.data),
    enabled: !!skillName,
  })

  const completeMutation = useMutation({
    mutationFn: (stepId: number) => gapApi.completeStep(stepId),
    onSuccess: () => {
      toast.success("Step marked complete")
      qc.invalidateQueries({ queryKey: ["roadmap", skillName] })
    },
  })

  const roadmap = roadmapQ.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Close the gap: {skillName}</h1>
        {roadmap && (
          <p className="text-muted">
            {roadmap.baseline_score.toFixed(0)} → {roadmap.current_score.toFixed(0)} → target {roadmap.target_score.toFixed(0)}
          </p>
        )}
      </div>

      {roadmap && (
        <Card>
          <CardHeader><CardTitle>Progress</CardTitle></CardHeader>
          <CardContent>
            <Progress value={(roadmap.current_score / roadmap.target_score) * 100} />
          </CardContent>
        </Card>
      )}

      {roadmap && (
        <Card>
          <CardHeader><CardTitle>Learning Plan</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {roadmap.steps.map((s, i) => (
              <div key={s.id} className="flex items-start justify-between gap-3 rounded-lg border border-border p-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted">Step {i + 1} · {s.resource_type}</p>
                  <p className="font-display">{s.title}</p>
                  <p className="text-sm text-muted">{s.description}</p>
                </div>
                {s.status === "completed" ? (
                  <span className="shrink-0 text-sm text-success">Done</span>
                ) : (
                  <Button size="sm" variant="outline" className="shrink-0" onClick={() => completeMutation.mutate(s.id)}>
                    Mark complete
                  </Button>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {roadmap && roadmap.resources.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Learning Resources</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {roadmap.resources.map((r) => (
              <a key={r.id} href={r.url} target="_blank" rel="noreferrer"
                 className="block rounded-lg border border-border p-3 hover:border-accent">
                <p className="font-display text-sm">{r.title}</p>
                <p className="text-xs text-muted">{r.provider} · {r.difficulty} · {r.duration_minutes} min</p>
              </a>
            ))}
          </CardContent>
        </Card>
      )}

      <Button onClick={() => navigate(`/student/assessments?skill=${encodeURIComponent(skillName)}`)}>
        Ready — take reassessment
      </Button>
    </div>
  )
}