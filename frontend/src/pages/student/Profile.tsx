import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import {
  studentApi, educationApi, type Education, type EducationInput,
  projectApi, type Project, type ProjectInput,
  experienceApi, type Experience, type ExperienceInput,
  certificationApi, type Certification, type CertificationInput,
  achievementApi, type Achievement, type AchievementInput,
} from "@/lib/api"
import { toast } from "sonner"
import { Select } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/context/AuthContext"
import { CheckCircle2, Circle, BadgeCheck, FileStack, ClipboardList, GitFork, Pencil, Plus } from "lucide-react"
const CHECKLIST_LABELS: Record<string, string> = {
  personal_info: "Personal information",
  education: "Education & career goal",
  github_linked: "GitHub linked",
  skills: "Skills tracked",
  evidence: "Evidence added",
  assessment: "Assessment completed",
}
const emptyEducation: EducationInput = {
  institution: "", degree: "", field_of_study: "",
  start_year: new Date().getFullYear(), end_year: null, is_current: false, grade: "",
}

function EducationSection() {
  const qc = useQueryClient()
  const listQ = useQuery({ queryKey: ["education"], queryFn: () => educationApi.list().then((r) => r.data) })
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<EducationInput>(emptyEducation)
  const [error, setError] = useState("")

  const invalidate = () => qc.invalidateQueries({ queryKey: ["education"] })

  const createMut = useMutation({
    mutationFn: () => educationApi.create(form),
    onSuccess: () => { toast.success("Education added"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const updateMut = useMutation({
    mutationFn: () => educationApi.update(editingId as number, form),
    onSuccess: () => { toast.success("Education updated"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const deleteMut = useMutation({
    mutationFn: (id: number) => educationApi.remove(id),
    onSuccess: () => { toast.success("Education removed"); invalidate() },
    onError: () => toast.error("Couldn't remove this record"),
  })

  const openAdd = () => { setForm(emptyEducation); setEditingId(null); setError(""); setFormOpen(true) }
  const openEdit = (e: Education) => {
    setForm({ institution: e.institution, degree: e.degree, field_of_study: e.field_of_study, start_year: e.start_year, end_year: e.end_year, is_current: e.is_current, grade: e.grade })
    setEditingId(e.id); setError(""); setFormOpen(true)
  }
  const closeForm = () => { setFormOpen(false); setEditingId(null) }

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault()
    setError("")
    if (!form.institution.trim() || !form.degree.trim()) { setError("Institution and degree are required."); return }
    if (!form.is_current && form.end_year && form.end_year < form.start_year) { setError("End year can't be before start year."); return }
    editingId ? updateMut.mutate() : createMut.mutate()
  }

  const saving = createMut.isPending || updateMut.isPending

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div><CardTitle>Education</CardTitle><CardDescription>Your academic background</CardDescription></div>
        {!formOpen && <Button size="sm" variant="outline" onClick={openAdd}><Plus className="h-4 w-4" /> Add Education</Button>}
      </CardHeader>
      <CardContent className="space-y-3">
        {listQ.isLoading && <p className="text-sm text-muted">Loading…</p>}
        {!listQ.isLoading && !listQ.data?.length && !formOpen && (
          <p className="text-sm text-muted">No education added yet.</p>
        )}

        {listQ.data?.map((e) => (
          <div key={e.id} className="flex items-start justify-between rounded-lg border border-border p-3">
            <div>
              <p className="font-medium">{e.degree}{e.field_of_study && ` — ${e.field_of_study}`}</p>
              <p className="text-sm text-muted">{e.institution}</p>
              <p className="text-xs text-muted">
                {e.start_year} – {e.is_current ? "Present" : e.end_year ?? "—"}
                {e.grade && ` • ${e.grade}`}
              </p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button className="text-xs text-accent" onClick={() => openEdit(e)}>Edit</button>
              <button
                className="text-xs text-danger"
                onClick={() => { if (confirm("Delete this education record?")) deleteMut.mutate(e.id) }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}

        {formOpen && (
          <form onSubmit={submit} className="space-y-3 rounded-lg border border-border p-4">
            {error && <p className="text-sm text-danger">{error}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5"><Label>Institution *</Label><Input required value={form.institution} onChange={(e) => setForm((f) => ({ ...f, institution: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Degree *</Label><Input required value={form.degree} onChange={(e) => setForm((f) => ({ ...f, degree: e.target.value }))} placeholder="B.Tech" /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Field of study</Label><Input value={form.field_of_study} onChange={(e) => setForm((f) => ({ ...f, field_of_study: e.target.value }))} placeholder="Artificial Intelligence & Data Science" /></div>
              <div className="space-y-1.5"><Label>Start year *</Label><Input required type="number" value={form.start_year} onChange={(e) => setForm((f) => ({ ...f, start_year: Number(e.target.value) }))} /></div>
              <div className="space-y-1.5">
                <Label>End year</Label>
                <Input type="number" disabled={form.is_current} value={form.end_year ?? ""} onChange={(e) => setForm((f) => ({ ...f, end_year: e.target.value ? Number(e.target.value) : null }))} />
              </div>
              <div className="flex items-center gap-2 sm:col-span-2">
                <input type="checkbox" id="is_current" checked={form.is_current} onChange={(e) => setForm((f) => ({ ...f, is_current: e.target.checked, end_year: e.target.checked ? null : f.end_year }))} />
                <Label htmlFor="is_current">Currently pursuing</Label>
              </div>
              <div className="space-y-1.5"><Label>CGPA / Percentage</Label><Input value={form.grade} onChange={(e) => setForm((f) => ({ ...f, grade: e.target.value }))} placeholder="8.7 CGPA" /></div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>{saving ? "Saving…" : editingId ? "Save changes" : "Add"}</Button>
              <Button type="button" variant="ghost" onClick={closeForm}>Cancel</Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

const emptyProject: ProjectInput = {
  title: "", description: "", technologies: "", github_url: "", live_url: "",
  role: "", start_date: null, end_date: null, is_ongoing: false,
}

function ProjectsSection() {
  const qc = useQueryClient()
  const listQ = useQuery({ queryKey: ["projects"], queryFn: () => projectApi.list().then((r) => r.data) })
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<ProjectInput>(emptyProject)
  const [error, setError] = useState("")

  const invalidate = () => qc.invalidateQueries({ queryKey: ["projects"] })
  const createMut = useMutation({
    mutationFn: () => projectApi.create(form),
    onSuccess: () => { toast.success("Project added"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const updateMut = useMutation({
    mutationFn: () => projectApi.update(editingId as number, form),
    onSuccess: () => { toast.success("Project updated"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const deleteMut = useMutation({
    mutationFn: (id: number) => projectApi.remove(id),
    onSuccess: () => { toast.success("Project removed"); invalidate() },
    onError: () => toast.error("Couldn't remove this project"),
  })

  const openAdd = () => { setForm(emptyProject); setEditingId(null); setError(""); setFormOpen(true) }
  const openEdit = (p: Project) => {
    setForm({ title: p.title, description: p.description, technologies: p.technologies, github_url: p.github_url, live_url: p.live_url, role: p.role, start_date: p.start_date, end_date: p.end_date, is_ongoing: p.is_ongoing })
    setEditingId(p.id); setError(""); setFormOpen(true)
  }
  const closeForm = () => { setFormOpen(false); setEditingId(null) }

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault()
    setError("")
    if (!form.title.trim()) { setError("Title is required."); return }
    if (!form.is_ongoing && form.end_date && form.start_date && form.end_date < form.start_date) { setError("End date can't be before start date."); return }
    editingId ? updateMut.mutate() : createMut.mutate()
  }
  const saving = createMut.isPending || updateMut.isPending

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div><CardTitle>Projects</CardTitle><CardDescription>What you've built — with proof</CardDescription></div>
        {!formOpen && <Button size="sm" variant="outline" onClick={openAdd}><Plus className="h-4 w-4" /> Add Project</Button>}
      </CardHeader>
      <CardContent className="space-y-3">
        {listQ.isLoading && <p className="text-sm text-muted">Loading…</p>}
        {!listQ.isLoading && !listQ.data?.length && !formOpen && <p className="text-sm text-muted">No projects added yet.</p>}
        {listQ.data?.map((p) => (
          <div key={p.id} className="flex items-start justify-between rounded-lg border border-border p-3">
            <div>
              <p className="font-medium">{p.title}</p>
              {p.role && <p className="text-sm text-muted">{p.role}</p>}
              {p.technologies && <p className="text-xs text-muted">{p.technologies}</p>}
              {p.github_url && <a href={p.github_url} target="_blank" rel="noreferrer" className="text-xs text-accent">{p.github_url}</a>}
            </div>
            <div className="flex shrink-0 gap-2">
              <button className="text-xs text-accent" onClick={() => openEdit(p)}>Edit</button>
              <button className="text-xs text-danger" onClick={() => { if (confirm("Delete this project?")) deleteMut.mutate(p.id) }}>Delete</button>
            </div>
          </div>
        ))}
        {formOpen && (
          <form onSubmit={submit} className="space-y-3 rounded-lg border border-border p-4">
            {error && <p className="text-sm text-danger">{error}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2"><Label>Title *</Label><Input required value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Description</Label><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Technologies</Label><Input value={form.technologies} onChange={(e) => setForm((f) => ({ ...f, technologies: e.target.value }))} placeholder="FastAPI, React, PostgreSQL" /></div>
              <div className="space-y-1.5"><Label>Your role</Label><Input value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))} placeholder="Full-stack developer" /></div>
              <div className="space-y-1.5"><Label>GitHub URL</Label><Input value={form.github_url} onChange={(e) => setForm((f) => ({ ...f, github_url: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Live URL</Label><Input value={form.live_url} onChange={(e) => setForm((f) => ({ ...f, live_url: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Start date</Label><Input type="date" value={form.start_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value || null }))} /></div>
              <div className="space-y-1.5"><Label>End date</Label><Input type="date" disabled={form.is_ongoing} value={form.end_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value || null }))} /></div>
              <div className="flex items-center gap-2 sm:col-span-2">
                <input type="checkbox" id="is_ongoing" checked={form.is_ongoing} onChange={(e) => setForm((f) => ({ ...f, is_ongoing: e.target.checked, end_date: e.target.checked ? null : f.end_date }))} />
                <Label htmlFor="is_ongoing">Ongoing</Label>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>{saving ? "Saving…" : editingId ? "Save changes" : "Add"}</Button>
              <Button type="button" variant="ghost" onClick={closeForm}>Cancel</Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

const emptyExperience: ExperienceInput = {
  organization: "", role: "", description: "", start_date: null, end_date: null, is_current: false, skills_used: "",
}

function ExperienceSection() {
  const qc = useQueryClient()
  const listQ = useQuery({ queryKey: ["experience"], queryFn: () => experienceApi.list().then((r) => r.data) })
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<ExperienceInput>(emptyExperience)
  const [error, setError] = useState("")

  const invalidate = () => qc.invalidateQueries({ queryKey: ["experience"] })
  const createMut = useMutation({
    mutationFn: () => experienceApi.create(form),
    onSuccess: () => { toast.success("Experience added"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const updateMut = useMutation({
    mutationFn: () => experienceApi.update(editingId as number, form),
    onSuccess: () => { toast.success("Experience updated"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const deleteMut = useMutation({
    mutationFn: (id: number) => experienceApi.remove(id),
    onSuccess: () => { toast.success("Experience removed"); invalidate() },
    onError: () => toast.error("Couldn't remove this record"),
  })

  const openAdd = () => { setForm(emptyExperience); setEditingId(null); setError(""); setFormOpen(true) }
  const openEdit = (x: Experience) => {
    setForm({ organization: x.organization, role: x.role, description: x.description, start_date: x.start_date, end_date: x.end_date, is_current: x.is_current, skills_used: x.skills_used })
    setEditingId(x.id); setError(""); setFormOpen(true)
  }
  const closeForm = () => { setFormOpen(false); setEditingId(null) }

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault()
    setError("")
    if (!form.organization.trim() || !form.role.trim()) { setError("Organization and role are required."); return }
    if (!form.is_current && form.end_date && form.start_date && form.end_date < form.start_date) { setError("End date can't be before start date."); return }
    editingId ? updateMut.mutate() : createMut.mutate()
  }
  const saving = createMut.isPending || updateMut.isPending

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div><CardTitle>Experience</CardTitle><CardDescription>Internships and jobs</CardDescription></div>
        {!formOpen && <Button size="sm" variant="outline" onClick={openAdd}><Plus className="h-4 w-4" /> Add Experience</Button>}
      </CardHeader>
      <CardContent className="space-y-3">
        {listQ.isLoading && <p className="text-sm text-muted">Loading…</p>}
        {!listQ.isLoading && !listQ.data?.length && !formOpen && <p className="text-sm text-muted">No experience added yet.</p>}
        {listQ.data?.map((x) => (
          <div key={x.id} className="flex items-start justify-between rounded-lg border border-border p-3">
            <div>
              <p className="font-medium">{x.role} — {x.organization}</p>
              <p className="text-xs text-muted">{x.start_date ?? "—"} – {x.is_current ? "Present" : x.end_date ?? "—"}</p>
              {x.skills_used && <p className="text-xs text-muted">{x.skills_used}</p>}
            </div>
            <div className="flex shrink-0 gap-2">
              <button className="text-xs text-accent" onClick={() => openEdit(x)}>Edit</button>
              <button className="text-xs text-danger" onClick={() => { if (confirm("Delete this experience record?")) deleteMut.mutate(x.id) }}>Delete</button>
            </div>
          </div>
        ))}
        {formOpen && (
          <form onSubmit={submit} className="space-y-3 rounded-lg border border-border p-4">
            {error && <p className="text-sm text-danger">{error}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5"><Label>Organization *</Label><Input required value={form.organization} onChange={(e) => setForm((f) => ({ ...f, organization: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Role *</Label><Input required value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Description</Label><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Skills used</Label><Input value={form.skills_used} onChange={(e) => setForm((f) => ({ ...f, skills_used: e.target.value }))} placeholder="Python, SQL" /></div>
              <div className="space-y-1.5"><Label>Start date</Label><Input type="date" value={form.start_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value || null }))} /></div>
              <div className="space-y-1.5"><Label>End date</Label><Input type="date" disabled={form.is_current} value={form.end_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value || null }))} /></div>
              <div className="flex items-center gap-2 sm:col-span-2">
                <input type="checkbox" id="is_current" checked={form.is_current} onChange={(e) => setForm((f) => ({ ...f, is_current: e.target.checked, end_date: e.target.checked ? null : f.end_date }))} />
                <Label htmlFor="is_current">Currently working here</Label>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>{saving ? "Saving…" : editingId ? "Save changes" : "Add"}</Button>
              <Button type="button" variant="ghost" onClick={closeForm}>Cancel</Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

const emptyCertification: CertificationInput = {
  name: "", issuer: "", issue_date: null, expiry_date: null, credential_id: "", credential_url: "", proof_url: "",
}

function CertificationsSection() {
  const qc = useQueryClient()
  const listQ = useQuery({ queryKey: ["certifications"], queryFn: () => certificationApi.list().then((r) => r.data) })
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<CertificationInput>(emptyCertification)
  const [error, setError] = useState("")

  const invalidate = () => qc.invalidateQueries({ queryKey: ["certifications"] })
  const createMut = useMutation({
    mutationFn: () => certificationApi.create(form),
    onSuccess: () => { toast.success("Certification added"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const updateMut = useMutation({
    mutationFn: () => certificationApi.update(editingId as number, form),
    onSuccess: () => { toast.success("Certification updated"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const deleteMut = useMutation({
    mutationFn: (id: number) => certificationApi.remove(id),
    onSuccess: () => { toast.success("Certification removed"); invalidate() },
    onError: () => toast.error("Couldn't remove this record"),
  })

  const openAdd = () => { setForm(emptyCertification); setEditingId(null); setError(""); setFormOpen(true) }
  const openEdit = (c: Certification) => {
    setForm({ name: c.name, issuer: c.issuer, issue_date: c.issue_date, expiry_date: c.expiry_date, credential_id: c.credential_id, credential_url: c.credential_url, proof_url: c.proof_url })
    setEditingId(c.id); setError(""); setFormOpen(true)
  }
  const closeForm = () => { setFormOpen(false); setEditingId(null) }

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault()
    setError("")
    if (!form.name.trim() || !form.issuer.trim()) { setError("Name and issuer are required."); return }
    editingId ? updateMut.mutate() : createMut.mutate()
  }
  const saving = createMut.isPending || updateMut.isPending

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div><CardTitle>Certifications</CardTitle><CardDescription>Self-reported — not authenticity-verified</CardDescription></div>
        {!formOpen && <Button size="sm" variant="outline" onClick={openAdd}><Plus className="h-4 w-4" /> Add Certification</Button>}
      </CardHeader>
      <CardContent className="space-y-3">
        {listQ.isLoading && <p className="text-sm text-muted">Loading…</p>}
        {!listQ.isLoading && !listQ.data?.length && !formOpen && <p className="text-sm text-muted">No certifications added yet.</p>}
        {listQ.data?.map((c) => (
          <div key={c.id} className="flex items-start justify-between rounded-lg border border-border p-3">
            <div>
              <p className="font-medium">{c.name}</p>
              <p className="text-sm text-muted">{c.issuer}{c.issue_date && ` • ${c.issue_date}`}</p>
              {c.credential_url && <a href={c.credential_url} target="_blank" rel="noreferrer" className="text-xs text-accent">Credential link</a>}
            </div>
            <div className="flex shrink-0 gap-2">
              <button className="text-xs text-accent" onClick={() => openEdit(c)}>Edit</button>
              <button className="text-xs text-danger" onClick={() => { if (confirm("Delete this certification?")) deleteMut.mutate(c.id) }}>Delete</button>
            </div>
          </div>
        ))}
        {formOpen && (
          <form onSubmit={submit} className="space-y-3 rounded-lg border border-border p-4">
            {error && <p className="text-sm text-danger">{error}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5"><Label>Name *</Label><Input required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Issuer *</Label><Input required value={form.issuer} onChange={(e) => setForm((f) => ({ ...f, issuer: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Issue date</Label><Input type="date" value={form.issue_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, issue_date: e.target.value || null }))} /></div>
              <div className="space-y-1.5"><Label>Expiry date</Label><Input type="date" value={form.expiry_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, expiry_date: e.target.value || null }))} /></div>
              <div className="space-y-1.5"><Label>Credential ID</Label><Input value={form.credential_id} onChange={(e) => setForm((f) => ({ ...f, credential_id: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Credential URL</Label><Input value={form.credential_url} onChange={(e) => setForm((f) => ({ ...f, credential_url: e.target.value }))} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Proof URL (self-submitted)</Label><Input value={form.proof_url} onChange={(e) => setForm((f) => ({ ...f, proof_url: e.target.value }))} /></div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>{saving ? "Saving…" : editingId ? "Save changes" : "Add"}</Button>
              <Button type="button" variant="ghost" onClick={closeForm}>Cancel</Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

const emptyAchievement: AchievementInput = {
  title: "", organization: "", date: null, description: "", proof_url: "",
}

function AchievementsSection() {
  const qc = useQueryClient()
  const listQ = useQuery({ queryKey: ["achievements"], queryFn: () => achievementApi.list().then((r) => r.data) })
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<AchievementInput>(emptyAchievement)
  const [error, setError] = useState("")

  const invalidate = () => qc.invalidateQueries({ queryKey: ["achievements"] })
  const createMut = useMutation({
    mutationFn: () => achievementApi.create(form),
    onSuccess: () => { toast.success("Achievement added"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const updateMut = useMutation({
    mutationFn: () => achievementApi.update(editingId as number, form),
    onSuccess: () => { toast.success("Achievement updated"); invalidate(); closeForm() },
    onError: () => setError("Couldn't save — check the fields and try again."),
  })
  const deleteMut = useMutation({
    mutationFn: (id: number) => achievementApi.remove(id),
    onSuccess: () => { toast.success("Achievement removed"); invalidate() },
    onError: () => toast.error("Couldn't remove this record"),
  })

  const openAdd = () => { setForm(emptyAchievement); setEditingId(null); setError(""); setFormOpen(true) }
  const openEdit = (a: Achievement) => {
    setForm({ title: a.title, organization: a.organization, date: a.date, description: a.description, proof_url: a.proof_url })
    setEditingId(a.id); setError(""); setFormOpen(true)
  }
  const closeForm = () => { setFormOpen(false); setEditingId(null) }

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault()
    setError("")
    if (!form.title.trim()) { setError("Title is required."); return }
    editingId ? updateMut.mutate() : createMut.mutate()
  }
  const saving = createMut.isPending || updateMut.isPending

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div><CardTitle>Achievements</CardTitle><CardDescription>Awards and recognitions</CardDescription></div>
        {!formOpen && <Button size="sm" variant="outline" onClick={openAdd}><Plus className="h-4 w-4" /> Add Achievement</Button>}
      </CardHeader>
      <CardContent className="space-y-3">
        {listQ.isLoading && <p className="text-sm text-muted">Loading…</p>}
        {!listQ.isLoading && !listQ.data?.length && !formOpen && <p className="text-sm text-muted">No achievements added yet.</p>}
        {listQ.data?.map((a) => (
          <div key={a.id} className="flex items-start justify-between rounded-lg border border-border p-3">
            <div>
              <p className="font-medium">{a.title}</p>
              <p className="text-sm text-muted">{a.organization}{a.date && ` • ${a.date}`}</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button className="text-xs text-accent" onClick={() => openEdit(a)}>Edit</button>
              <button className="text-xs text-danger" onClick={() => { if (confirm("Delete this achievement?")) deleteMut.mutate(a.id) }}>Delete</button>
            </div>
          </div>
        ))}
        {formOpen && (
          <form onSubmit={submit} className="space-y-3 rounded-lg border border-border p-4">
            {error && <p className="text-sm text-danger">{error}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2"><Label>Title *</Label><Input required value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Organization</Label><Input value={form.organization} onChange={(e) => setForm((f) => ({ ...f, organization: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Date</Label><Input type="date" value={form.date ?? ""} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value || null }))} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Description</Label><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Proof URL (self-submitted)</Label><Input value={form.proof_url} onChange={(e) => setForm((f) => ({ ...f, proof_url: e.target.value }))} /></div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>{saving ? "Saving…" : editingId ? "Save changes" : "Add"}</Button>
              <Button type="button" variant="ghost" onClick={closeForm}>Cancel</Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

export default function Profile() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const profileQ = useQuery({ queryKey: ["my-profile"], queryFn: () => studentApi.myProfile().then((r) => r.data) })
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const startEdit = () => {
    if (!profileQ.data) return
    setForm({
      bio: profileQ.data.bio, branch: profileQ.data.branch,
      career_goal: profileQ.data.career_goal, github_username: profileQ.data.github_username,
      year_of_study: String(profileQ.data.year_of_study),
    })
    setEditing(true)
  }

  const save = async () => {
    setSaving(true)
    try {
      await studentApi.updateProfile({ ...form, year_of_study: Number(form.year_of_study) })
      await qc.invalidateQueries({ queryKey: ["my-profile"] })
      toast.success("Profile updated")
      setEditing(false)
    } catch {
      toast.error("Couldn't save profile")
    } finally {
      setSaving(false)
    }
  }

  const profile = profileQ.data

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <Card>
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex gap-4">
            <Avatar name={user?.full_name ?? "?"} className="h-16 w-16 text-lg" />
            <div>
              <h1 className="font-display text-2xl">{profile?.full_name}</h1>
              <p className="text-muted">{profile?.branch || "Branch not set"} {profile?.year_of_study ? `• Year ${profile.year_of_study}` : ""}</p>
              {profile?.college_name && <p className="text-sm text-muted">{profile.college_name}</p>}
              <p className="mt-2 max-w-md text-sm">{profile?.bio || "No bio yet — add one to strengthen your profile."}</p>
              {profile?.github_username && (
                <a href={`https://github.com/${profile.github_username}`} target="_blank" rel="noreferrer" className="mt-2 inline-block text-sm text-accent">
                  github.com/{profile.github_username}
                </a>
              )}
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={startEdit}><Pencil className="h-4 w-4" /> Edit Profile</Button>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {editing && (
            <Card>
              <CardHeader><CardTitle>Edit personal information</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div><Label>Bio</Label><Input value={form.bio ?? ""} onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))} /></div>
                <div><Label>Branch</Label><Input value={form.branch ?? ""} onChange={(e) => setForm((f) => ({ ...f, branch: e.target.value }))} /></div>
                <div><Label>Year of study</Label><Input type="number" value={form.year_of_study ?? ""} onChange={(e) => setForm((f) => ({ ...f, year_of_study: e.target.value }))} /></div>
                <div><Label>Career goal</Label><Input value={form.career_goal ?? ""} onChange={(e) => setForm((f) => ({ ...f, career_goal: e.target.value }))} /></div>
                <div><Label>GitHub username</Label><Input value={form.github_username ?? ""} onChange={(e) => setForm((f) => ({ ...f, github_username: e.target.value }))} /></div>
                <div className="flex gap-2">
                  <Button onClick={save} disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
                  <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
                </div>
              </CardContent>
            </Card>
          )}
          <EducationSection />
          <ProjectsSection />
          <ExperienceSection />
          <CertificationsSection />
          <AchievementsSection />
          <Card>
            <CardHeader><CardTitle>Career identity</CardTitle><CardDescription>Detailed career sections live in their dedicated tools below.</CardDescription></CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <Link to="/student/passport" className="flex items-center gap-3 rounded-xl border border-border p-4 hover:border-accent">
                <BadgeCheck className="h-5 w-5 text-accent" /><div><p className="font-medium">Skill Passport</p><p className="text-xs text-muted">Evidence-backed skills</p></div>
              </Link>
              <Link to="/student/evidence" className="flex items-center gap-3 rounded-xl border border-border p-4 hover:border-accent">
                <FileStack className="h-5 w-5 text-accent" /><div><p className="font-medium">Evidence Center</p><p className="text-xs text-muted">Add proof for your skills</p></div>
              </Link>
              <Link to="/student/assessments" className="flex items-center gap-3 rounded-xl border border-border p-4 hover:border-accent">
                <ClipboardList className="h-5 w-5 text-accent" /><div><p className="font-medium">Assessments</p><p className="text-xs text-muted">Your test history</p></div>
              </Link>
              <Link to="/student/github-analyzer" className="flex items-center gap-3 rounded-xl border border-border p-4 hover:border-accent">
                <GitFork className="h-5 w-5 text-accent" /><div><p className="font-medium">GitHub Analyzer</p><p className="text-xs text-muted">Project signal analysis</p></div>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* SIDEBAR */}
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Profile Strength</CardTitle></CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-muted">Complete</span>
                <span className="font-display text-2xl text-accent">{profile?.strength.score ?? 0}%</span>
              </div>
              <Progress value={profile?.strength.score ?? 0} className="mt-2" />
              <div className="mt-4 space-y-2">
                {profile && Object.entries(profile.strength.checklist).map(([key, done]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    {done ? <CheckCircle2 className="h-4 w-4 text-success" /> : <Circle className="h-4 w-4 text-muted" />}
                    <span className={done ? "" : "text-muted"}>{CHECKLIST_LABELS[key]}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Visibility</CardTitle></CardHeader>
            <CardContent>
              <Badge variant={profile?.profile_visible ? "success" : "outline"}>
                {profile?.profile_visible ? "Visible to colleges" : "Private"}
              </Badge>
              <p className="mt-2 text-xs text-muted">Controlled from Edit Profile.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}