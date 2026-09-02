import { Moon, Sun, Monitor } from "lucide-react"
import { useTheme } from "@/context/ThemeContext"
import { cn } from "@/lib/utils"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const options = [
    { key: "light", icon: Sun },
    { key: "dark", icon: Moon },
    { key: "system", icon: Monitor },
  ] as const

  return (
    <div className="flex items-center gap-0.5 rounded-full border border-border bg-surface-alt p-0.5">
      {options.map(({ key, icon: Icon }) => (
        <button
          key={key}
          onClick={() => setTheme(key)}
          aria-label={`${key} theme`}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-full transition-colors",
            theme === key ? "bg-surface text-accent shadow-sm" : "text-muted hover:text-foreground"
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </button>
      ))}
    </div>
  )
}
