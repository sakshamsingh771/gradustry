import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { aiApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AIBadge } from "@/components/domain/AIBadge"
import { Upload, FileText } from "lucide-react"
import { toast } from "sonner"

interface Skill { name: string; confidence: number; evidence: string }

export default function ResumeAnalyzer() {
  const qc = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<{ used_ai: boolean; extraction: { skills: Skill[] } } | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const analyzeMutation = useMutation({
    mutationFn: () => aiApi.analyzeResume(file!).then((r) => r.data),
    onSuccess: (data) => {
      setResult(data)
      setSelected(new Set(data.extraction.skills.map((s: Skill) => s.name)))
    },
    onError: () => toast.error("Couldn't analyze that file"),
  })

  const acceptMutation = useMutation({
    mutationFn: () => {
      const skills = result!.extraction.skills.filter((s) => selected.has(s.name))
      return aiApi.acceptSkills({ source: "resume", source_title: file?.name, skills })
    },
    onSuccess: (res) => {
      toast.success(res.data.detail)
      qc.invalidateQueries({ queryKey: ["skill-passport"] })
      setResult(null)
      setFile(null)
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">AI Resume Analyzer</h1>
        <p className="text-muted">Upload your resume — AI extracts skills for you to review, not auto-verify.</p>
      </div>

      {!result && (
        <Card>
          <CardHeader><CardTitle>Upload resume</CardTitle><CardDescription>PDF, DOCX, or plain text — max 5MB</CardDescription></CardHeader>
          <CardContent className="space-y-4">
            <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border p-10 text-center hover:border-accent">
              <Upload className="h-6 w-6 text-muted" />
              <span className="text-sm">{file ? file.name : "Click to choose a file"}</span>
              <input type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </label>
            <Button className="w-full" disabled={!file || analyzeMutation.isPending} onClick={() => analyzeMutation.mutate()}>
              {analyzeMutation.isPending ? "Analyzing…" : "Analyze resume"}
            </Button>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div><CardTitle>Detected skills</CardTitle><CardDescription>Uncheck anything that isn't accurate before accepting.</CardDescription></div>
            <AIBadge usedAi={result.used_ai} />
          </CardHeader>
          <CardContent className="space-y-3">
            {result.extraction.skills.map((s) => (
              <label key={s.name} className="flex items-start gap-3 rounded-lg border border-border p-3">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={selected.has(s.name)}
                  onChange={(e) => setSelected((prev) => {
                    const next = new Set(prev)
                    e.target.checked ? next.add(s.name) : next.delete(s.name)
                    return next
                  })}
                />
                <div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-3.5 w-3.5 text-muted" />
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs text-muted">confidence {(s.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{s.evidence}</p>
                </div>
              </label>
            ))}
            {result.extraction.skills.length === 0 && <p className="text-sm text-muted">No skills detected in this file.</p>}
            <div className="flex gap-3 pt-2">
              <Button variant="outline" onClick={() => { setResult(null); setFile(null) }}>Start over</Button>
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
