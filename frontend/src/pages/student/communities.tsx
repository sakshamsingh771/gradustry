import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { communityApi, type CommunityListItem } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Users, Lock } from "lucide-react"

function CommunityFeed({ communityId }: { communityId: number }) {
  const qc = useQueryClient()
  const [content, setContent] = useState("")
  const postsQ = useQuery({ queryKey: ["community-posts", communityId], queryFn: () => communityApi.posts(communityId).then((r) => r.data) })

  const postMut = useMutation({
    mutationFn: () => communityApi.createPost(communityId, content),
    onSuccess: () => { setContent(""); qc.invalidateQueries({ queryKey: ["community-posts", communityId] }) },
    onError: () => toast.error("Couldn't post"),
  })

  return (
    <div className="space-y-3">
      <form onSubmit={(e) => { e.preventDefault(); if (content.trim()) postMut.mutate() }} className="flex gap-2">
        <Input value={content} onChange={(e) => setContent(e.target.value)} placeholder="Share something…" />
        <Button type="submit" disabled={!content.trim() || postMut.isPending}>Post</Button>
      </form>
      {postsQ.data?.map((p) => (
        <div key={p.id} className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium">{p.author_name}</p>
          <p className="text-sm">{p.content}</p>
          <p className="mt-1 text-xs text-muted">{new Date(p.created_at).toLocaleString()} · {p.comment_count} comment(s)</p>
        </div>
      ))}
      {postsQ.data?.length === 0 && <p className="text-sm text-muted">No posts yet — be the first.</p>}
    </div>
  )
}

function InterestCommunities() {
  const qc = useQueryClient()
  const [active, setActive] = useState<number | null>(null)
  const listQ = useQuery({ queryKey: ["interest-communities"], queryFn: () => communityApi.listInterest().then((r) => r.data) })

  const joinMut = useMutation({
    mutationFn: (id: number) => communityApi.join(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interest-communities"] }),
  })

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {listQ.data?.map((c: CommunityListItem) => (
        <Card key={c.id}>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div><CardTitle>{c.name}</CardTitle><CardDescription>{c.description}</CardDescription></div>
            <Badge variant="outline"><Users className="mr-1 h-3 w-3 inline" />{c.member_count}</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {!c.is_member && <Button size="sm" variant="outline" onClick={() => joinMut.mutate(c.id)}>Join</Button>}
            {active === c.id ? <CommunityFeed communityId={c.id} /> : (
              <button className="text-sm text-accent" onClick={() => setActive(c.id)}>View discussion →</button>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function CollegeCommunity() {
  const collegeQ = useQuery({ queryKey: ["my-college-community"], queryFn: () => communityApi.myCollegeCommunity().then((r) => r.data) })

  if (collegeQ.isLoading) return <p className="text-sm text-muted">Loading…</p>
  if (!collegeQ.data) return <p className="text-sm text-muted">Join a college from your profile to unlock its community.</p>
  if (!collegeQ.data.verified) {
    return (
      <Card><CardContent className="flex items-center gap-3 p-4">
        <Lock className="h-5 w-5 text-muted" />
        <p className="text-sm text-muted">Your college membership is pending verification. Once approved, your college community unlocks here.</p>
      </CardContent></Card>
    )
  }
  if (!collegeQ.data.community) return <p className="text-sm text-muted">Your college community isn't set up yet.</p>
  return (
    <Card>
      <CardHeader><CardTitle>{collegeQ.data.community.name}</CardTitle><CardDescription>{collegeQ.data.community.description}</CardDescription></CardHeader>
      <CardContent><CommunityFeed communityId={collegeQ.data.community.id} /></CardContent>
    </Card>
  )
}

export default function Communities() {
  const [tab, setTab] = useState<"interest" | "college">("interest")
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Communities</h1>
        <p className="text-muted">Connect with peers by interest — or privately with your own college.</p>
      </div>
      <div className="flex gap-2">
        <button onClick={() => setTab("interest")} className={`rounded-full px-4 py-1.5 text-sm ${tab === "interest" ? "bg-accent text-white" : "bg-surface-alt text-muted"}`}>Interest Communities</button>
        <button onClick={() => setTab("college")} className={`rounded-full px-4 py-1.5 text-sm ${tab === "college" ? "bg-accent text-white" : "bg-surface-alt text-muted"}`}>My College</button>
      </div>
      {tab === "interest" ? <InterestCommunities /> : <CollegeCommunity />}
    </div>
  )
}