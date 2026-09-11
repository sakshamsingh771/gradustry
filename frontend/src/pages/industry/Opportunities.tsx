import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { opportunityApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

interface ReqSkill { skill_name: string; min_proficiency: number; weight: number }

const STUDENT_ROLE_TYPES = [
  { value: "internship", label: "Internship" },
  { value: "job", label: "Job" },
]
const ACADEMICIAN_ROLE_TYPES = [
  { value: "faculty_internship", label: "Faculty Internship" },
  { value: "industrial_training", label: "Industrial Training" },
  { value: "fdp", label: "Faculty Development Programme (FDP)" },
  { value: "consultancy", label: "Consultancy" },
  { value: "research_collaboration", label: "Research Collaboration" },
  { value: "guest_lecture", label: "Guest Lecture" },
  { value: "mentorship", label: "Mentorship" },
]

export default function IndustryOpportunities() {
  const qc = useQueryClient()
  const oppsQ = useQuery({ queryKey: ["my-opportunities"], queryFn: () => opportunityApi.mine().then((r) => r.data) })
  const [form, setForm] = useState({ title: "", role_type: "internship", audience: "student" as "student" | "academician", description: "", location: "Remote", min_year_of_study: 1, final_year_only: false, stipend_or_ctc: "" })
  const [skills, setSkills] = useState<ReqSkill[]>([{ skill_name: "", min_proficiency: 60, weight: 1 }])

  const roleTypeOptions = form.audience === "academician" ? ACADEMICIAN_ROLE_TYPES : STUDENT_ROLE_TYPES

  const setAudience = (audience: "student" | "academician") => {
    const defaultRoleType = audience === "academician" ? ACADEMICIAN_ROLE_TYPES[0].value : STUDENT_ROLE_TYPES[0].value
    setForm((f) => ({ ...f, audience, role_type: defaultRoleType }))
  }

  const createMutation = useMutation({
    mutationFn: () => opportunityApi.create({
      ...form,
      required_skills: form.audience === "student" ? skills.filter((s) => s.skill_name) : [],
    }),
    onSuccess: () => {
      toast.success("Opportunity posted")
      qc.invalidateQueries({ queryKey: ["my-opportunities"] })
      setForm({ title: "", role_type: "internship", audience: "student", description: "", location: "Remote", min_year_of_study: 1, final_year_only: false, stipend_or_ctc: "" })
      setSkills([{ skill_name: "", min_proficiency: 60, weight: 1 }])
    },
    onError: () => toast.error("Couldn't post opportunity"),
  })

  const updateSkill = (i: number, patch: Partial<ReqSkill>) =>
    setSkills((s) => s.map((sk, idx) => (idx === i ? { ...sk, ...patch } : sk)))

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl">Opportunities</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader><CardTitle>Post a new opportunity</CardTitle><CardDescription>For students, or for academicians (FDP, consultancy, research, guest lecture, mentorship)</CardDescription></CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }}>
              <div className="space-y-1.5">
                <Label>Audience</Label>
                <Select value={form.audience} onChange={(e) => setAudience(e.target.value as "student" | "academician")}>
                  <option value="student">Students</option>
                  <option value="academician">Academicians / Faculty</option>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Category</Label>
                <Select value={form.role_type} onChange={(e) => setForm((f) => ({ ...f, role_type: e.target.value }))}>
                  {roleTypeOptions.map((rt) => <option key={rt.value} value={rt.value}>{rt.label}</option>)}
                </Select>
              </div>
              <div className="space-y-1.5"><Label>Title</Label><Input required value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5"><Label>Location</Label><Input value={form.location} onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))} /></div>
                <div className="space-y-1.5"><Label>Stipend / CTC</Label><Input value={form.stipend_or_ctc} onChange={(e) => setForm((f) => ({ ...f, stipend_or_ctc: e.target.value }))} /></div>
              </div>
              <div className="space-y-1.5"><Label>Description</Label><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></div>

              {form.audience === "student" && (
                <>
                  <div className="space-y-1.5"><Label>Min. year of study</Label><Input type="number" min={1} max={5} value={form.min_year_of_study} onChange={(e) => setForm((f) => ({ ...f, min_year_of_study: Number(e.target.value) }))} /></div>

                  <div className="space-y-2">
                    <Label>Required skills</Label>
                    {skills.map((s, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <Input placeholder="Skill" value={s.skill_name} onChange={(e) => updateSkill(i, { skill_name: e.target.value })} />
                        <Input type="number" className="w-20" placeholder="Min %" value={s.min_proficiency} onChange={(e) => updateSkill(i, { min_proficiency: Number(e.target.value) })} />
                        <button type="button" onClick={() => setSkills((sk) => sk.filter((_, idx) => idx !== i))} className="text-muted hover:text-danger"><Trash2 className="h-4 w-4" /></button>
                      </div>
                    ))}
                    <Button type="button" variant="outline" size="sm" onClick={() => setSkills((s) => [...s, { skill_name: "", min_proficiency: 60, weight: 1 }])}>
                      <Plus className="h-3.5 w-3.5" /> Add skill
                    </Button>
                  </div>
                </>
              )}

              <Button type="submit" className="w-full" disabled={createMutation.isPending}>{createMutation.isPending ? "Posting…" : "Post opportunity"}</Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-3 lg:col-span-2">
          {oppsQ.data?.map((o) => (
            <Card key={o.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle>{o.title}</CardTitle>
                    <CardDescription>{o.location} · {o.stipend_or_ctc || "Unpaid"}</CardDescription>
                  </div>
                  <Badge variant={o.audience === "academician" ? "default" : "outline"} className="capitalize">
                    {o.audience === "academician" ? "Faculty" : "Student"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {o.required_skills.map((s) => (
                  <span key={s.skill_name} className="rounded-full bg-surface-alt px-2.5 py-1 text-xs">{s.skill_name} ≥ {s.min_proficiency}%</span>
                ))}
                {o.audience === "academician" && !o.required_skills.length && (
                  <span className="text-xs text-muted capitalize">{o.role_type.replace("_", " ")}</span>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
