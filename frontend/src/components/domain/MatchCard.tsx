import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import type { OpportunityMatch } from "@/lib/api"
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react"

export function MatchCard({ match, onApply, applied, onCloseGap }: { match: OpportunityMatch; onApply: () => void; applied: boolean; onCloseGap: (skill: string) => void }) {
  const { opportunity: o, match_score, explanation: ex } = match
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <CardTitle>{o.title}</CardTitle>
          <CardDescription>
            {o.company_name} · {o.location} · {o.role_type.replace("_", " ")}
            {o.duration ? ` · ${o.duration}` : ""}
          </CardDescription>
        </div>
        <div className="text-right shrink-0">
          <div className="font-display text-2xl tabular-nums text-accent">{match_score.toFixed(0)}%</div>
          <div className="text-xs text-muted">match</div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {!ex.is_eligible ? (
          <Badge variant="warning">Not eligible yet</Badge>
        ) : (
          <Badge variant="success">Eligible</Badge>
        )}
        <div className="space-y-1.5 text-sm">
          {ex.matched_skills.map((s) => (
            <div key={s} className="flex items-center gap-2 text-success">
              <CheckCircle2 className="h-4 w-4 shrink-0" /> {s} requirement matched
            </div>
          ))}
          {ex.below_target_skills.map((s) => (
            <div key={s} className="flex items-center justify-between gap-2 text-warning">
              <span className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 shrink-0" /> {s} below target</span>
              <Button size="sm" variant="ghost" className="h-auto py-0.5 text-xs" onClick={() => onCloseGap(s)}>Close gap</Button>
            </div>
          ))}
          {ex.missing_eligibility.map((s) => (
            <div key={s} className="flex items-center gap-2 text-danger">
              <XCircle className="h-4 w-4 shrink-0" /> Missing: {s}
            </div>
          ))}
        </div>
        <p className="text-xs text-muted">{ex.relevant_evidence_count} relevant evidence items considered</p>
        {o.eligibility_notes && <p className="text-xs text-muted">Eligibility: {o.eligibility_notes}</p>}
        {o.capacity != null && (
          <p className="text-xs text-muted">
            {Math.max(o.capacity - o.enrolled_count, 0)} of {o.capacity} seats left
          </p>
        )}
        <Button className="w-full" disabled={applied || (o.capacity != null && o.enrolled_count >= o.capacity && !applied)} onClick={onApply}>
          {applied ? "Applied" : (o.capacity != null && o.enrolled_count >= o.capacity) ? "Full" : ex.is_eligible ? "Apply now" : "Become eligible / apply anyway"}
        </Button>
      </CardContent>
    </Card>
  )
}
