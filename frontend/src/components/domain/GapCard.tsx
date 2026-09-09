import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import type { GapItem } from "@/lib/api"

const severityColor: Record<string, string> = {
  matched: "bg-success",
  low: "bg-warning",
  medium: "bg-warning",
  high: "bg-danger",
}

const priorityColor: Record<string, string> = {
  High: "text-danger",
  Medium: "text-warning",
  Low: "text-muted",
  None: "text-success",
}

export function GapCard({ item, onBuildRoadmap }: { item: GapItem; onBuildRoadmap?: () => void }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-display text-base">{item.skill_name}</p>
          {item.priority !== "None" && (
            <p className={`text-xs font-semibold uppercase tracking-wide ${priorityColor[item.priority]}`}>
              Priority: {item.priority}
            </p>
          )}
        </div>
        <div className="shrink-0 text-right font-display text-lg tabular-nums">
          {item.current_score.toFixed(0)}<span className="text-muted text-sm"> / {item.target_score.toFixed(0)}</span>
        </div>
      </div>
      <Progress value={(item.current_score / item.target_score) * 100} className="mt-3" barClassName={severityColor[item.severity]} />

      {item.reasons?.length > 0 && (
        <ul className="mt-3 list-disc space-y-1 pl-4 text-sm text-muted">
          {item.reasons.map((r) => <li key={r}>{r}</li>)}
        </ul>
      )}

      {item.missing_subskills?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {item.missing_subskills.map((s) => (
            <span key={s} className="rounded-full border border-border px-2 py-0.5 text-xs text-muted">{s}</span>
          ))}
        </div>
      )}

      {item.severity !== "matched" && onBuildRoadmap && (
        <Button size="sm" variant="outline" className="mt-3" onClick={onBuildRoadmap}>
          Close This Gap
        </Button>
      )}
    </div>
  )
}