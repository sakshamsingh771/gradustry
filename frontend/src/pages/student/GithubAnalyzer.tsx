import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { aiApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AIBadge } from "@/components/domain/AIBadge"
import { Badge } from "@/components/ui/badge"
import { GitFork } from "lucide-react"
import { toast } from "sonner"

interface Skill { name: string; confidence: number }
interface Analysis { repository: string; skills: Skill[]; project_level: string; evidence_quality: number; architecture_notes: string }

export default function GitForkAnalyzer() {
  const qc = useQueryClient()
  const [url, setUrl] = useState("")
  const [result, setResult] = useState<{ used_ai: boolean; analysis: Analysis } | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const analyzeMutation = useMutation({
    mutationFn: () => aiApi.analyzeGithub(url).then((r) => r.data),
    onSuccess: (data) => {
      setResult(data)
      setSelected(new Set(data.analysis.skills.map((s: Skill) => s.name)))
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Couldn't analyze that repository"),
  })

  const acceptMutation = useMutation({
    mutationFn: () => {
      const skills = result!.analysis.skills.filter((s) => selected.has(s.name)).map((s) => ({ name: s.name, confidence: s.confidence, evidence: `Detected in ${result!.analysis.repository}` }))
      return aiApi.acceptSkills({ source: "github", source_title: result!.analysis.repository, skills })
    },
    onSuccess: (res) => {
      toast.success(res.data.detail)
      qc.invalidateQueries({ queryKey: ["skill-passport"] })
      setResult(null)
      setUrl("")
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">AI GitHub Project Analyzer</h1>
        <p className="text-muted">Paste a public repo link — this is AI-derived evidence confidence, not verified authorship.</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Analyze a repository</CardTitle><CardDescription>Public repos only, e.g. https://github.com/owner/repo</CardDescription></CardHeader>
        <CardContent className="flex items-end gap-3">
          <div className="flex-1 space-y-1.5">
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/you/your-project" />
          </div>
          <Button onClick={() => analyzeMutation.mutate()} disabled={!url || analyzeMutation.isPending}>
            <GitFork className="h-4 w-4" /> {analyzeMutation.isPending ? "Analyzing…" : "Analyze"}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>{result.analysis.repository}</CardTitle>
              <CardDescription className="capitalize">{result.analysis.project_level} project · evidence quality {(result.analysis.evidence_quality * 100).toFixed(0)}%</CardDescription>
            </div>
            <AIBadge usedAi={result.used_ai} />
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted">{result.analysis.architecture_notes}</p>
            <div className="space-y-2">
              {result.analysis.skills.map((s) => (
                <label key={s.name} className="flex items-center gap-3 rounded-lg border border-border p-3">
                  <input type="checkbox" checked={selected.has(s.name)} onChange={(e) => setSelected((prev) => {
                    const next = new Set(prev); e.target.checked ? next.add(s.name) : next.delete(s.name); return next
                  })} />
                  <span className="font-medium">{s.name}</span>
                  <Badge variant="outline">confidence {(s.confidence * 100).toFixed(0)}%</Badge>
                </label>
              ))}
              {result.analysis.skills.length === 0 && <p className="text-sm text-muted">No clear technology signals detected.</p>}
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => { setResult(null); setUrl("") }}>Start over</Button>
              <Button disabled={selected.size === 0 || acceptMutation.isPending} onClick={() => acceptMutation.mutate()}>
                {acceptMutation.isPending ? "Adding…" : `Accept ${selected.size} skill(s) into Skill Passport`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
