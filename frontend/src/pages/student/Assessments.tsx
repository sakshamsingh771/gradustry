import { useState } from "react"
import { useSearchParams } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { assessmentApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { CheckCircle2, XCircle } from "lucide-react"

interface QuestionT { id: number; topic: string; difficulty: string; question_type: string; prompt: string; options: string[] }

export default function Assessments() {
  const [params] = useSearchParams()
  const qc = useQueryClient()
  const [skillName, setSkillName] = useState(params.get("skill") || "")
  const [attempt, setAttempt] = useState<{ attempt_id: number; skill_name: string; questions: QuestionT[] } | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<any>(null)

  const startMutation = useMutation({
    mutationFn: () => assessmentApi.start({ skill_name: skillName, num_questions: 3 }).then((r) => r.data),
    onSuccess: (data) => { setAttempt(data); setResult(null); setAnswers({}) },
    onError: () => toast.error("Couldn't start assessment"),
  })

  const submitMutation = useMutation({
    mutationFn: () => assessmentApi.submit({
      attempt_id: attempt!.attempt_id,
      answers: Object.fromEntries(Object.entries(answers).map(([qid, val]) => [qid, [val]])),
    }).then((r) => r.data),
    onSuccess: (data) => {
      setResult(data)
      qc.invalidateQueries({ queryKey: ["skill-passport"] })
      qc.invalidateQueries({ queryKey: ["gap-report"] })
      toast.success(`Scored ${data.score_percent}% — ${data.gap_status}`)
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Assessment Engine</h1>
        <p className="text-muted">Gap-specific assessments — not a generic test.</p>
      </div>

      {!attempt && (
        <Card>
          <CardHeader><CardTitle>Start an assessment</CardTitle><CardDescription>Pick the skill you want to be re-assessed on.</CardDescription></CardHeader>
          <CardContent className="flex items-end gap-3">
            <div className="flex-1 space-y-1.5">
              <Label>Skill</Label>
              <Input value={skillName} onChange={(e) => setSkillName(e.target.value)} placeholder="Python, Docker, SQL…" />
            </div>
            <Button onClick={() => startMutation.mutate()} disabled={!skillName || startMutation.isPending}>
              {startMutation.isPending ? "Preparing…" : "Start"}
            </Button>
          </CardContent>
        </Card>
      )}

      {attempt && !result && (
        <Card>
          <CardHeader><CardTitle>{attempt.skill_name} assessment</CardTitle><CardDescription>{attempt.questions.length} question(s)</CardDescription></CardHeader>
          <CardContent className="space-y-6">
            {attempt.questions.map((q, i) => (
              <div key={q.id}>
                <p className="font-medium">{i + 1}. {q.prompt}</p>
                <div className="mt-2 space-y-2">
                  {q.options.map((opt, idx) => (
                    <label key={idx} className="flex items-center gap-2 rounded-md border border-border p-2 text-sm hover:bg-surface-alt">
                      <input
                        type="radio"
                        name={`q-${q.id}`}
                        checked={answers[q.id] === String(idx)}
                        onChange={() => setAnswers((a) => ({ ...a, [q.id]: String(idx) }))}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            <Button onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending || Object.keys(answers).length < attempt.questions.length}>
              {submitMutation.isPending ? "Submitting…" : "Submit assessment"}
            </Button>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Result: {result.score_percent}%</CardTitle>
            <CardDescription>
              {result.previous_score}% → {result.new_proficiency}% ({result.delta >= 0 ? "+" : ""}{result.delta}) · <Badge variant={result.gap_status === "Gap Closed" ? "success" : result.gap_status === "Gap Partially Closed" ? "warning" : "outline"}>{result.gap_status}</Badge>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {result.per_question_feedback.map((f: any) => (
              <div key={f.question_id} className="rounded-lg border border-border p-3">
                <div className="flex items-start gap-2">
                  {f.is_correct ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" /> : <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />}
                  <div>
                    <p className="text-sm font-medium">{f.prompt}</p>
                    <p className="mt-1 text-xs text-muted">{f.explanation}</p>
                  </div>
                </div>
              </div>
            ))}
            <Button variant="outline" onClick={() => { setAttempt(null); setResult(null) }}>Take another assessment</Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
