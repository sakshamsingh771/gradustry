import { useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { aiApi, gapApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { AIBadge } from "@/components/domain/AIBadge"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

export default function AIRoadmap() {
  const rolesQ = useQuery({ queryKey: ["career-roles"], queryFn: () => gapApi.roles().then((r) => r.data as { title: string }[]) })
  const [role, setRole] = useState("Backend Developer")
  const [hours, setHours] = useState(6)
  const [result, setResult] = useState<any>(null)

  const generateMutation = useMutation({
    mutationFn: () => aiApi.roadmapGenerate(role, hours).then((r) => r.data),
    onSuccess: (data) => setResult(data),
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Couldn't generate a roadmap"),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">AI Personalized Roadmap</h1>
        <p className="text-muted">Grounded in your actual current scores and gaps — not generic advice.</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Generate a roadmap</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <div className="space-y-1.5">
            <label className="text-sm text-muted">Target career</label>
            <Select value={role} onChange={(e) => setRole(e.target.value)} className="w-56">
              {rolesQ.data?.map((r) => <option key={r.title} value={r.title}>{r.title}</option>)}
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm text-muted">Hours/week</label>
            <Input type="number" min={1} max={40} value={hours} onChange={(e) => setHours(Number(e.target.value))} className="w-24" />
          </div>
          <Button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
            {generateMutation.isPending ? "Generating…" : "Generate roadmap"}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>{result.roadmap.target_career}</CardTitle>
              <CardDescription>Priority skills: {result.roadmap.priority_skills.join(", ") || "none — you're on track"}</CardDescription>
            </div>
            <AIBadge usedAi={result.used_ai} />
          </CardHeader>
          <CardContent className="space-y-3">
            {result.note && <p className="text-xs text-muted">{result.note}</p>}
            {result.roadmap.steps.map((s: any, i: number) => (
              <div key={i} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wide text-accent">{s.week_label}</span>
                  <Badge variant="outline" className="capitalize">{s.resource_type}</Badge>
                </div>
                <p className="mt-1 font-medium">{s.title}</p>
                <p className="text-sm text-muted">{s.description}</p>
                {s.estimated_hours && <p className="mt-1 text-xs text-muted">~{s.estimated_hours}h</p>}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
