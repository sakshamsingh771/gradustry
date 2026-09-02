import { useQuery } from "@tanstack/react-query"
import { collegeApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"

export default function CollegeStudents() {
  const studentsQ = useQuery({ queryKey: ["college-students"], queryFn: () => collegeApi.students().then((r) => r.data) })

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl">Students</h1>
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
          {studentsQ.data?.length === 0 && <p className="py-4 text-sm text-muted">No students linked to your college yet.</p>}
        </CardContent>
      </Card>
    </div>
  )
}
