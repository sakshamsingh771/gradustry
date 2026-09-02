import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import type { GapItem } from "@/lib/api"

const severityColor: Record<string, string> = {
  matched: "bg-success",
  low: "bg-warning",
  medium: "bg-warning",
  high: "bg-danger",
}

export function GapCard({ item, onBuildRoadmap }: { item: GapItem; onBuildRoadmap?: () => void }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-display text-base">{item.skill_name}</p>
          <p className="mt-1 text-sm text-muted">{item.reason}</p>
        </div>
        <div className="shrink-0 text-right font-display text-lg tabular-nums">
          {item.current_score.toFixed(0)}<span className="text-muted text-sm"> / {item.target_score.toFixed(0)}</span>
        </div>
      </div>
      <Progress value={(item.current_score / item.target_score) * 100} className="mt-3" barClassName={severityColor[item.severity]} />
      {item.severity !== "matched" && onBuildRoadmap && (
        <Button size="sm" variant="outline" className="mt-3" onClick={onBuildRoadmap}>
          Build gap-closure roadmap
        </Button>
      )}
    </div>
  )
}
