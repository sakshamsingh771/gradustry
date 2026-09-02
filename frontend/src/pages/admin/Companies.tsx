import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { adminApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function AdminCompanies() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ["admin-companies"], queryFn: () => adminApi.companies().then((r) => r.data) })
  const verify = useMutation({
    mutationFn: (id: number) => adminApi.verifyCompany(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-companies"] }),
  })
  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl">Companies</h1>
      <div className="space-y-3">
        {q.data?.map((c: any) => (
          <Card key={c.id}><CardContent className="flex items-center justify-between pt-5">
            <p className="font-medium">{c.company_name}</p>
            <div className="flex items-center gap-2">
              <Badge variant={c.verified ? "success" : "outline"}>{c.verified ? "Verified" : "Pending"}</Badge>
              {!c.verified && <Button size="sm" onClick={() => verify.mutate(c.id)}>Verify</Button>}
            </div>
          </CardContent></Card>
        ))}
      </div>
    </div>
  )
}
