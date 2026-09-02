import { useState, useRef, useEffect } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { aiApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AIBadge } from "@/components/domain/AIBadge"
import { Bot, User, Send } from "lucide-react"

const SUGGESTED = [
  "Am I ready for this internship?",
  "What skills am I missing?",
  "What should I learn next?",
  "What should I do this week?",
]

interface Turn { question: string; answer: string; used_ai: boolean }

export default function CareerCopilot() {
  const historyQ = useQuery({ queryKey: ["copilot-history"], queryFn: () => aiApi.copilotHistory().then((r) => r.data as any[]) })
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)

  const askMutation = useMutation({
    mutationFn: (question: string) => aiApi.copilotChat(question).then((r) => r.data),
    onSuccess: (data, question) => setTurns((t) => [...t, { question, answer: data.answer, used_ai: data.used_ai }]),
  })

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }) }, [turns])

  const ask = (q: string) => {
    if (!q.trim()) return
    askMutation.mutate(q)
    setInput("")
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h1 className="font-display text-2xl">Gradustry Career Copilot</h1>
        <p className="text-muted">Answers grounded only in your own Skill Passport, gaps, and applications.</p>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex-1 space-y-4 overflow-y-auto pt-5">
          {historyQ.data?.map((h) => (
            <div key={h.id} className="space-y-2">
              <div className="flex items-start justify-end gap-2">
                <div className="max-w-md rounded-2xl rounded-tr-sm bg-accent/10 px-4 py-2 text-sm">{h.question}</div>
                <User className="mt-1 h-5 w-5 shrink-0 text-muted" />
              </div>
              <div className="flex items-start gap-2">
                <Bot className="mt-1 h-5 w-5 shrink-0 text-accent" />
                <div className="max-w-md rounded-2xl rounded-tl-sm bg-surface-alt px-4 py-2 text-sm">{h.answer}</div>
              </div>
            </div>
          ))}
          {turns.map((t, i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-start justify-end gap-2">
                <div className="max-w-md rounded-2xl rounded-tr-sm bg-accent/10 px-4 py-2 text-sm">{t.question}</div>
                <User className="mt-1 h-5 w-5 shrink-0 text-muted" />
              </div>
              <div className="flex items-start gap-2">
                <Bot className="mt-1 h-5 w-5 shrink-0 text-accent" />
                <div className="max-w-md space-y-1 rounded-2xl rounded-tl-sm bg-surface-alt px-4 py-2 text-sm">
                  <p>{t.answer}</p>
                  <AIBadge usedAi={t.used_ai} className="mt-1" />
                </div>
              </div>
            </div>
          ))}
          {turns.length === 0 && !historyQ.data?.length && (
            <div className="flex flex-wrap gap-2 pt-4">
              {SUGGESTED.map((q) => (
                <button key={q} onClick={() => ask(q)} className="rounded-full border border-border px-3 py-1.5 text-sm hover:bg-surface-alt">
                  {q}
                </button>
              ))}
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>
        <div className="flex items-center gap-2 border-t border-border p-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask(input)}
            placeholder="Ask about your readiness, gaps, or next steps…"
          />
          <Button size="icon" onClick={() => ask(input)} disabled={askMutation.isPending}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </div>
  )
}
