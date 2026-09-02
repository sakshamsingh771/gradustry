import { cn } from "@/lib/utils"

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
  return (
    <div
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-full bg-accent/15 text-sm font-semibold text-accent",
        className
      )}
    >
      {initials}
    </div>
  )
}
