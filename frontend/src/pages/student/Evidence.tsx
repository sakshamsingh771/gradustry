import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { studentApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Plus } from "lucide-react"

const EVIDENCE_TYPES = [
  { value: "certificate", label: "Certificate" },
  { value: "github", label: "GitHub project" },
  { value: "project", label: "Project submission" },
]

export default function EvidenceCenter() {
  const qc = useQueryClient()
  const passportQ = useQuery({ queryKey: ["skill-passport"], queryFn: () => studentApi.skillPassport().then((r) => r.data) })
  const [form, setForm] = useState({ skill_name: "", type: "certificate", title: "", description: "", source_url: "" })

  const addMutation = useMutation({
    mutationFn: () => studentApi.addEvidence(form),
    onSuccess: () => {
      toast.success("Evidence added — awaiting review, score updated")
      qc.invalidateQueries({ queryKey: ["skill-passport"] })
      setForm({ skill_name: "", type: "certificate", title: "", description: "", source_url: "" })
    },
    onError: () => toast.error("Couldn't add evidence"),
  })

  const allEvidence = passportQ.data?.skills.flatMap((s) => s.evidences.map((e) => ({ ...e, skill_name: s.skill_name }))) ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Evidence Center</h1>
        <p className="text-muted">Every piece of evidence you add recalculates your Skill Passport score.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader><CardTitle>Add evidence</CardTitle><CardDescription>Certificate, GitHub project, or a submitted project</CardDescription></CardHeader>
          <CardContent>
            <form
              className="space-y-3"
              onSubmit={(e) => { e.preventDefault(); addMutation.mutate() }}
            >
              <div className="space-y-1.5">
                <Label>Skill</Label>
                <Input required value={form.skill_name} onChange={(e) => setForm((f) => ({ ...f, skill_name: e.target.value }))} placeholder="Python" />
              </div>
              <div className="space-y-1.5">
                <Label>Evidence type</Label>
                <Select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}>
                  {EVIDENCE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Title</Label>
                <Input required value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="NPTEL Python Certification" />
              </div>
              <div className="space-y-1.5">
                <Label>Link (optional)</Label>
                <Input value={form.source_url} onChange={(e) => setForm((f) => ({ ...f, source_url: e.target.value }))} placeholder="https://github.com/you/repo" />
              </div>
              <div className="space-y-1.5">
                <Label>Description (optional)</Label>
                <Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
              </div>
              <Button type="submit" className="w-full" disabled={addMutation.isPending}>
                <Plus className="h-4 w-4" /> {addMutation.isPending ? "Adding…" : "Add evidence"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>All evidence</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {allEvidence.length === 0 && (
              <p className="text-sm text-muted">No evidence yet — add your first certificate or project on the left.</p>
            )}
            {allEvidence.map((e) => (
              <div key={e.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                <div>
                  <p className="text-sm font-medium">{e.title}</p>
                  <p className="text-xs text-muted">{e.skill_name} · {e.type.replace("_", " ")}</p>
                </div>
                <Badge variant={e.status === "verified" ? "success" : e.status === "suspicious" ? "danger" : "outline"}>
                  {e.status.replace("_", " ")}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
