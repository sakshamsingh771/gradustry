import { useQuery } from "@tanstack/react-query"
import { academicianApi } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"

export default function AcademicianStudents() {
  const studentsQ = useQuery({ queryKey: ["academician-students"], queryFn: () => academicianApi.students().then((r) => r.data) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl">Students</h1>
        <p className="text-muted">Students from your verified college, for mentorship and guidance.</p>
      </div>
      <Card>
        <CardContent className="pt-5">
          <table className="w-full text-sm">
            <thead className="text-left text-muted">
              <tr><th className="pb-2">Name</th><th className="pb-2">Branch</th><th className="pb-2">Year</th><th className="pb-2">Career Goal</th><th className="pb-2 text-right">Readiness</th></tr>
            </thead>
            <tbody>
              {studentsQ.data?.map((s) => (
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
          {studentsQ.data?.length === 0 && (
            <p className="py-4 text-sm text-muted">
              No students visible yet — link and get verified with a college from your Profile page to see its student roster here.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
