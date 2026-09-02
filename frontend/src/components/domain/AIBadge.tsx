import { Sparkles, Cpu } from "lucide-react"
import { cn } from "@/lib/utils"

export function AIBadge({ usedAi, className }: { usedAi: boolean; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        usedAi ? "border-ai-accent/30 bg-ai-accent/10 text-ai-accent" : "border-border bg-surface-alt text-muted",
        className
      )}
    >
      {usedAi ? <Sparkles className="h-3 w-3" /> : <Cpu className="h-3 w-3" />}
      {usedAi ? "AI analysis" : "Standard analysis"}
    </span>
  )
}
