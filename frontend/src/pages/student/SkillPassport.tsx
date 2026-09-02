import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { studentApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { SkillLedgerRow } from "@/components/domain/SkillLedgerRow"
import { Badge } from "@/components/ui/badge"
import type { StudentSkill } from "@/lib/api"

export default function SkillPassport() {
  const passportQ = useQuery({ queryKey: ["skill-passport"], queryFn: () => studentApi.skillPassport().then((r) => r.data) })
  const [selected, setSelected] = useState<StudentSkill | null>(null)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl">Skill Passport</h1>
          <p className="text-muted">Your evidence-backed credential — {passportQ.data?.full_name}</p>
        </div>
        <div className="rounded-xl border border-border bg-surface px-5 py-3 text-center">
          <p className="text-xs text-muted">Career Readiness</p>
          <p className="font-display text-2xl text-accent">{passportQ.data?.career_readiness ?? "—"}%</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Skills ledger</CardTitle><CardDescription>Tap a skill to see its evidence and "why?"</CardDescription></CardHeader>
          <CardContent>
            {passportQ.data?.skills.map((s) => (
              <SkillLedgerRow key={s.id} skill={s} onClick={() => setSelected(s)} />
            ))}
            {!passportQ.data?.skills.length && <p className="text-sm text-muted">No skills yet. Add evidence from the Evidence Center.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{selected ? selected.skill_name : "Select a skill"}</CardTitle>
            {selected && <CardDescription>Evidence Confidence: {selected.confidence_level}</CardDescription>}
          </CardHeader>
          <CardContent className="space-y-3">
            {!selected && <p className="text-sm text-muted">Click any skill on the left to see the evidence behind its score.</p>}
            {selected?.evidences.map((e) => (
              <div key={e.id} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{e.title}</span>
                  <Badge variant={e.status === "verified" ? "success" : e.status === "suspicious" ? "danger" : "outline"}>
                    {e.status.replace("_", " ")}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-muted capitalize">{e.type.replace("_", " ")} · signal {e.signal_score}/100</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
