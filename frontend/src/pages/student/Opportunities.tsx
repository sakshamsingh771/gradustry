import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { MatchCard } from "@/components/domain/MatchCard"
import { toast } from "sonner"

export default function StudentOpportunities() {
  const qc = useQueryClient()
  const matchesQ = useQuery({ queryKey: ["matches"], queryFn: () => opportunityApi.matches().then((r) => r.data) })
  const appsQ = useQuery({ queryKey: ["my-applications"], queryFn: () => opportunityApi.myApplications().then((r) => r.data) })

  const applyMutation = useMutation({
    mutationFn: (opportunityId: number) => opportunityApi.apply(opportunityId),
    onSuccess: () => {
      toast.success("Application submitted")
      qc.invalidateQueries({ queryKey: ["my-applications"] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Couldn't apply"),
  })

  const appliedIds = new Set(appsQ.data?.map((a) => a.opportunity_id))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Opportunities</h1>
        <p className="text-muted">Ranked by explainable match score — not keywords.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {matchesQ.data?.map((m) => (
          <MatchCard
            key={m.opportunity.id}
            match={m}
            applied={appliedIds.has(m.opportunity.id)}
            onApply={() => applyMutation.mutate(m.opportunity.id)}
          />
        ))}
        {matchesQ.data?.length === 0 && <p className="text-sm text-muted">No opportunities posted yet — check back soon.</p>}
      </div>
    </div>
  )
}
