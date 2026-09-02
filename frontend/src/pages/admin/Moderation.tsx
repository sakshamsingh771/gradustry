import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { adminApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

export default function Moderation() {
  const qc = useQueryClient()
  const queueQ = useQuery({ queryKey: ["evidence-queue"], queryFn: () => adminApi.evidenceQueue().then((r) => r.data) })

  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => adminApi.moderateEvidence(id, status),
    onSuccess: () => {
      toast.success("Updated")
      qc.invalidateQueries({ queryKey: ["evidence-queue"] })
    },
  })

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl">Evidence Moderation Queue</h1>
      <div className="space-y-3">
        {queueQ.data?.map((e: any) => (
          <Card key={e.id}>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
              <div>
                <p className="font-medium">{e.title}</p>
                <p className="text-sm text-muted">{e.student_name} · {e.skill_name} · {e.type.replace("_", " ")}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{e.status.replace("_", " ")}</Badge>
                <Button size="sm" onClick={() => mutation.mutate({ id: e.id, status: "verified" })}>Verify</Button>
                <Button size="sm" variant="destructive" onClick={() => mutation.mutate({ id: e.id, status: "suspicious" })}>Flag suspicious</Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {queueQ.data?.length === 0 && <p className="text-sm text-muted">Nothing pending review.</p>}
      </div>
    </div>
  )
}
