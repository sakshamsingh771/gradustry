import { useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { academicianApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

export default function AcademicianProfile() {
  const qc = useQueryClient()
  const profileQ = useQuery({ queryKey: ["academician-profile"], queryFn: () => academicianApi.myProfile().then((r) => r.data) })
  const collegesQ = useQuery({ queryKey: ["academician-colleges"], queryFn: () => academicianApi.colleges().then((r) => r.data) })

  const [form, setForm] = useState({ designation: "", institution: "", department: "", area_of_expertise: "", experience_years: 0, bio: "" })
  const [collegeId, setCollegeId] = useState<string>("")

  useEffect(() => {
    if (profileQ.data) {
      const p = profileQ.data
      setForm({
        designation: p.designation, institution: p.institution, department: p.department,
        area_of_expertise: p.area_of_expertise, experience_years: p.experience_years, bio: p.bio,
      })
    }
  }, [profileQ.data])

  const updateMutation = useMutation({
    mutationFn: () => academicianApi.updateProfile(form),
    onSuccess: () => { toast.success("Profile updated"); qc.invalidateQueries({ queryKey: ["academician-profile"] }) },
    onError: () => toast.error("Couldn't update profile"),
  })

  const joinMutation = useMutation({
    mutationFn: () => academicianApi.joinCollege(Number(collegeId)),
    onSuccess: (res) => {
      toast.success((res.data as { detail: string }).detail)
      qc.invalidateQueries({ queryKey: ["academician-profile"] })
      qc.invalidateQueries({ queryKey: ["academician-dashboard"] })
    },
    onError: () => toast.error("Couldn't send membership request"),
  })

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl">Academician Profile</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Professional information</CardTitle><CardDescription>{profileQ.data?.full_name} · {profileQ.data?.email}</CardDescription></CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); updateMutation.mutate() }}>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5"><Label>Designation</Label><Input value={form.designation} onChange={(e) => setForm((f) => ({ ...f, designation: e.target.value }))} /></div>
                <div className="space-y-1.5"><Label>Experience (years)</Label><Input type="number" min={0} value={form.experience_years} onChange={(e) => setForm((f) => ({ ...f, experience_years: Number(e.target.value) }))} /></div>
              </div>
              <div className="space-y-1.5"><Label>Institution</Label><Input value={form.institution} onChange={(e) => setForm((f) => ({ ...f, institution: e.target.value }))} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5"><Label>Department</Label><Input value={form.department} onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))} /></div>
                <div className="space-y-1.5"><Label>Area of expertise</Label><Input value={form.area_of_expertise} onChange={(e) => setForm((f) => ({ ...f, area_of_expertise: e.target.value }))} /></div>
              </div>
              <div className="space-y-1.5"><Label>Bio / professional summary</Label><Input value={form.bio} onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))} /></div>
              <Button type="submit" disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving…" : "Save changes"}</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>College affiliation</CardTitle><CardDescription>Link your institution for mentorship access</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            {profileQ.data?.college_name ? (
              <div className="flex items-center gap-2 text-sm">
                <span>{profileQ.data.college_name}</span>
                <Badge variant="outline">linked</Badge>
              </div>
            ) : (
              <>
                <Select value={collegeId} onChange={(e) => setCollegeId(e.target.value)}>
                  <option value="">Select your college…</option>
                  {collegesQ.data?.map((c) => <option key={c.id} value={c.id}>{c.college_name}{c.city ? ` (${c.city})` : ""}</option>)}
                </Select>
                <Button type="button" size="sm" disabled={!collegeId || joinMutation.isPending} onClick={() => joinMutation.mutate()}>
                  {joinMutation.isPending ? "Sending…" : "Request to join"}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
