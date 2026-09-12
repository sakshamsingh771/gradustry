import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { collegeApi, type CollegeFilters } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Select } from "@/components/ui/select"

export default function CollegeStudents() {
  const [filters, setFilters] = useState<CollegeFilters>({})
  const activeFilters = useMemo(
    () => Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")) as CollegeFilters,
    [filters],
  )
  const optsQ = useQuery({ queryKey: ["college-filters"], queryFn: () => collegeApi.filters().then((r) => r.data) })
  const studentsQ = useQuery({ queryKey: ["college-students", activeFilters], queryFn: () => collegeApi.students(activeFilters).then((r) => r.data) })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-display text-2xl">Students</h1>
        <div className="flex flex-wrap gap-2">
          <Select className="w-40" value={filters.branch ?? ""} onChange={(e) => setFilters((f) => ({ ...f, branch: e.target.value || undefined }))}>
            <option value="">All departments</option>
            {optsQ.data?.branches.map((b) => <option key={b} value={b}>{b}</option>)}
          </Select>
          <Select className="w-32" value={filters.year_of_study ?? ""} onChange={(e) => setFilters((f) => ({ ...f, year_of_study: e.target.value ? Number(e.target.value) : undefined }))}>
            <option value="">All years</option>
            {optsQ.data?.years_of_study.map((y) => <option key={y} value={y}>Year {y}</option>)}
          </Select>
          <Select className="w-44" value={filters.career_goal ?? ""} onChange={(e) => setFilters((f) => ({ ...f, career_goal: e.target.value || undefined }))}>
            <option value="">All target roles</option>
            {optsQ.data?.career_goals.map((g) => <option key={g} value={g}>{g}</option>)}
          </Select>
          <Select className="w-36" value={filters.skill ?? ""} onChange={(e) => setFilters((f) => ({ ...f, skill: e.target.value || undefined }))}>
            <option value="">All skills</option>
            {optsQ.data?.skills.map((s) => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>
      </div>
      <Card>
        <CardContent className="pt-5">
          <table className="w-full text-sm">
            <thead className="text-left text-muted">
              <tr><th className="pb-2">Name</th><th className="pb-2">Branch</th><th className="pb-2">Year</th><th className="pb-2">Career Goal</th><th className="pb-2 text-right">Readiness</th></tr>
            </thead>
            <tbody>
              {studentsQ.data?.map((s: any) => (
                <tr key={s.student_id} className="border-t border-border">
                  <td className="py-2">{s.full_name}</td>
                  <td className="py-2">{s.branch || "—"}</td>
                  <td className="py-2">{s.year_of_study}</td>
                  <td className="py-2">{s.career_goal || "—"}</td>
                  <td className="py-2 text-right font-medium">{s.readiness}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          {studentsQ.data?.length === 0 && <p className="py-4 text-sm text-muted">No students match these filters.</p>}
        </CardContent>
      </Card>
    </div>
  )
}
