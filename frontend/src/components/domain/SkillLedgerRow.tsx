import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import type { StudentSkill } from "@/lib/api"

const confidenceVariant: Record<string, "success" | "warning" | "outline" | "danger"> = {
  High: "success",
  Medium: "warning",
  Low: "outline",
  None: "outline",
}

export function SkillLedgerRow({ skill, onClick }: { skill: StudentSkill; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="grid w-full grid-cols-[1fr_auto] items-center gap-4 border-b border-border py-4 text-left last:border-b-0 hover:bg-surface-alt/50 -mx-2 px-2 rounded-md transition-colors"
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-display text-base">{skill.skill_name}</span>
          <Badge variant={confidenceVariant[skill.confidence_level] ?? "outline"}>
            {skill.confidence_level} confidence
          </Badge>
        </div>
        <div className="mt-2 flex items-center gap-3">
          <Progress value={skill.proficiency_score} className="max-w-xs" />
          <span className="text-sm text-muted">{skill.evidence_count} evidence item{skill.evidence_count === 1 ? "" : "s"}</span>
        </div>
      </div>
      <div className="font-display text-2xl tabular-nums">{skill.proficiency_score.toFixed(0)}<span className="text-sm text-muted">%</span></div>
    </button>
  )
}
