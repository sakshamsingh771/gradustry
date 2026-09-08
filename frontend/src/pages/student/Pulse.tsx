import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { pulseApi, type PulseArticle } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bookmark, BookmarkCheck } from "lucide-react"

const IMPACT_VARIANT: Record<string, "success" | "outline" | "danger"> = { high: "danger", medium: "outline", low: "outline" }

function ArticleCard({ article, onToggleSave }: { article: PulseArticle; onToggleSave: (a: PulseArticle) => void }) {
  return (
    <Card>
      <CardContent className="space-y-2 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Badge variant="outline">{article.category}</Badge>
            <h3 className="mt-1 font-medium">{article.title}</h3>
          </div>
          <button onClick={() => onToggleSave(article)} className="shrink-0 text-muted hover:text-accent">
            {article.saved ? <BookmarkCheck className="h-5 w-5 text-accent" /> : <Bookmark className="h-5 w-5" />}
          </button>
        </div>
        <p className="text-sm text-muted">{article.summary}</p>
        {article.why_it_matters && (
          <div className="rounded-lg bg-surface-alt p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-accent">
              {article.why_it_matters.personalized ? "Why this matters to you" : "Get personalized relevance"}
            </p>
            <p className="mt-1 text-xs text-muted">{article.why_it_matters.recommended_action}</p>
            {article.why_it_matters.matched_skills && article.why_it_matters.matched_skills.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {article.why_it_matters.matched_skills.map((s) => <Badge key={s} variant="success">{s}</Badge>)}
              </div>
            )}
          </div>
        )}
        <div className="flex items-center justify-between text-xs text-muted">
          <span>{article.source} · {new Date(article.published_at).toLocaleDateString()}</span>
          <Badge variant={IMPACT_VARIANT[article.impact] ?? "outline"} className="uppercase">{article.impact} impact</Badge>
        </div>
      </CardContent>
    </Card>
  )
}

export default function Pulse() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<"for-you" | "all" | "saved">("for-you")

  const feedQ = useQuery({
    queryKey: ["pulse", tab],
    queryFn: () => (tab === "for-you" ? pulseApi.forYou() : tab === "saved" ? pulseApi.saved() : pulseApi.list()).then((r) => r.data),
  })

  const saveMut = useMutation({
    mutationFn: (a: PulseArticle) => (a.saved ? pulseApi.unsave(a.id) : pulseApi.save(a.id)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pulse"] }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Gradustry Pulse</h1>
        <p className="text-muted">Stay ahead of technology. Understand what it means for your career.</p>
      </div>

      <div className="flex gap-2">
        {(["for-you", "all", "saved"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`rounded-full px-4 py-1.5 text-sm ${tab === t ? "bg-accent text-white" : "bg-surface-alt text-muted"}`}>
            {t === "for-you" ? "For You" : t === "all" ? "All" : "Saved"}
          </button>
        ))}
      </div>

      {feedQ.isLoading && <p className="text-sm text-muted">Loading…</p>}
      {!feedQ.isLoading && !feedQ.data?.length && <p className="text-sm text-muted">No articles yet.</p>}
      <div className="grid gap-4 md:grid-cols-2">
        {feedQ.data?.map((a) => <ArticleCard key={a.id} article={a} onToggleSave={(article) => saveMut.mutate(article)} />)}
      </div>
    </div>
  )
}