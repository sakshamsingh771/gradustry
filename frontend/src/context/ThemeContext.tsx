import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

type Theme = "light" | "dark" | "system"

interface ThemeContextType {
  theme: Theme
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(
    () => (localStorage.getItem("gradustry_theme") as Theme) || "system"
  )

  useEffect(() => {
    const root = window.document.documentElement
    const apply = (t: Theme) => {
      const isDark =
        t === "dark" || (t === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)
      root.classList.toggle("dark", isDark)
    }
    apply(theme)
    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)")
      const listener = () => apply("system")
      mq.addEventListener("change", listener)
      return () => mq.removeEventListener("change", listener)
    }
  }, [theme])

  const setTheme = (t: Theme) => {
    localStorage.setItem("gradustry_theme", t)
    setThemeState(t)
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider")
  return ctx
}
