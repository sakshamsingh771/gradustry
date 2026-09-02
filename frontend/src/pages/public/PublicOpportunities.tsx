import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { opportunityApi } from "@/lib/api"
import { PublicNav } from "@/components/layout/PublicNav"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function PublicOpportunities() {
  const navigate = useNavigate()
  const q = useQuery({ queryKey: ["public-opportunities"], queryFn: () => opportunityApi.list().then((r) => r.data) })

  return (
    <div>
      <PublicNav />
      <div className="mx-auto max-w-5xl px-6 py-12">
        <h1 className="font-display text-3xl">Open opportunities</h1>
        <p className="mt-1 text-muted">Log in as a student to see your personalized, explainable match score for each.</p>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {q.data?.map((o) => (
            <Card key={o.id}>
              <CardHeader><CardTitle>{o.title}</CardTitle><CardDescription>{o.company_name} · {o.location} · {o.role_type}</CardDescription></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {o.required_skills.map((s) => <span key={s.skill_name} className="rounded-full bg-surface-alt px-2.5 py-1 text-xs">{s.skill_name}</span>)}
                </div>
                <Button className="mt-4 w-full" variant="outline" onClick={() => navigate("/register")}>Log in to see your match</Button>
              </CardContent>
            </Card>
          ))}
          {q.data?.length === 0 && <p className="text-sm text-muted">No opportunities posted yet.</p>}
        </div>
      </div>
    </div>
  )
}
