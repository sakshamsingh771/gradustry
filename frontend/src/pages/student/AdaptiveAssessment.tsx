import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { aiApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { AIBadge } from "@/components/domain/AIBadge"
import { CheckCircle2, XCircle } from "lucide-react"
import { toast } from "sonner"

interface Question { topic: string; difficulty: string; question_type: string; prompt: string; options: string[] }

export default function AdaptiveAssessment() {
  const qc = useQueryClient()
  const [skillName, setSkillName] = useState("")
  const [session, setSession] = useState<{ session_id: number; step: number; max_steps: number; difficulty: string; question: Question; used_ai: boolean } | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [lastFeedback, setLastFeedback] = useState<any>(null)
  const [final, setFinal] = useState<any>(null)

  const startMutation = useMutation({
    mutationFn: () => aiApi.adaptiveStart(skillName).then((r) => r.data),
    onSuccess: (data) => { setSession(data); setFinal(null); setLastFeedback(null); setSelectedAnswer(null) },
    onError: () => toast.error("Couldn't start the adaptive session"),
  })

  const nextMutation = useMutation({
    mutationFn: () => aiApi.adaptiveNext(session!.session_id, [selectedAnswer!]).then((r) => r.data),
    onSuccess: (data) => {
      setLastFeedback(data.last_feedback)
      setSelectedAnswer(null)
      if (data.status === "completed") {
        setFinal(data)
        setSession(null)
        qc.invalidateQueries({ queryKey: ["skill-passport"] })
        toast.success(`Adaptive assessment complete — ${data.score_percent}%`)
      } else {
        setSession({ session_id: data.session_id, step: data.step, max_steps: data.max_steps, difficulty: data.difficulty, question: data.question, used_ai: data.used_ai })
      }
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Adaptive AI Assessment</h1>
        <p className="text-muted">Difficulty adjusts to you — correct answers escalate, wrong answers trigger a diagnostic follow-up.</p>
      </div>

      {!session && !final && (
        <Card>
          <CardHeader><CardTitle>Start a session</CardTitle><CardDescription>5 adaptive questions on the skill of your choice</CardDescription></CardHeader>
          <CardContent className="flex items-end gap-3">
            <Input value={skillName} onChange={(e) => setSkillName(e.target.value)} placeholder="Python, Docker, FastAPI…" className="flex-1" />
            <Button onClick={() => startMutation.mutate()} disabled={!skillName || startMutation.isPending}>
              {startMutation.isPending ? "Preparing…" : "Start"}
            </Button>
          </CardContent>
        </Card>
      )}

      {session && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Step {session.step} of {session.max_steps}</CardTitle>
              <CardDescription className="capitalize">{session.question.topic} · {session.difficulty}</CardDescription>
            </div>
            <AIBadge usedAi={session.used_ai} />
          </CardHeader>
          <CardContent className="space-y-4">
            {lastFeedback && (
              <div className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${lastFeedback.is_correct ? "border-success/30 bg-success/5" : "border-danger/30 bg-danger/5"}`}>
                {lastFeedback.is_correct ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" /> : <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />}
                <p>{lastFeedback.explanation}</p>
              </div>
            )}
            <p className="font-medium">{session.question.prompt}</p>
            <div className="space-y-2">
              {session.question.options.map((opt, idx) => (
                <label key={idx} className="flex items-center gap-2 rounded-md border border-border p-2 text-sm hover:bg-surface-alt">
                  <input type="radio" name="adaptive-answer" checked={selectedAnswer === String(idx)} onChange={() => setSelectedAnswer(String(idx))} />
                  {opt}
                </label>
              ))}
            </div>
            <Button onClick={() => nextMutation.mutate()} disabled={selectedAnswer === null || nextMutation.isPending}>
              {nextMutation.isPending ? "Checking…" : "Submit answer"}
            </Button>
          </CardContent>
        </Card>
      )}

      {final && (
        <Card>
          <CardHeader><CardTitle>Session complete — {final.score_percent}%</CardTitle>
            <CardDescription>New proficiency: {final.new_proficiency}% ({final.confidence_level} confidence)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {final.weak_topics.map((t: string) => <Badge key={t} variant="warning">Weak: {t}</Badge>)}
              {final.weak_topics.length === 0 && <Badge variant="success">No weak topics identified</Badge>}
            </div>
            <Button variant="outline" onClick={() => setFinal(null)}>Take another</Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
