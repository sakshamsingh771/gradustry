import axios from "axios"

export const api = axios.create({ baseURL: "/api" })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("gradustry_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("gradustry_token")
      localStorage.removeItem("gradustry_user")
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login"
      }
    }
    return Promise.reject(err)
  }
)

// ---------- Types ----------
export type Role = "student" | "college" | "industry" | "admin"

export interface AuthUser {
  user_id: number
  full_name: string
  role: Role
}

export interface Evidence {
  id: number
  type: string
  title: string
  description: string
  source_url: string
  status: string
  signal_score: number
  created_at: string
}

export interface StudentSkill {
  id: number
  skill_name: string
  category: string
  proficiency_score: number
  confidence_level: string
  last_assessed_at: string | null
  evidence_count: number
  evidences: Evidence[]
}

export interface SkillPassport {
  student_id: number
  full_name: string
  career_goal: string
  career_readiness: number
  skills: StudentSkill[]
}

export interface GapItem {
  skill_name: string
  current_score: number
  target_score: number
  gap: number
  severity: "matched" | "low" | "medium" | "high"
  reason: string
}

export interface GapReport {
  role_title: string
  career_readiness: number
  matched: GapItem[]
  low_gap: GapItem[]
  medium_gap: GapItem[]
  high_gap: GapItem[]
}

export interface RoadmapStepT {
  id: number
  order_index: number
  title: string
  description: string
  resource_type: string
  status: string
}

export interface SkillRoadmap {
  skill_name: string
  baseline_score: number
  target_score: number
  current_score: number
  steps: RoadmapStepT[]
}

export interface OpportunityOut {
  id: number
  title: string
  role_type: string
  description: string
  location: string
  company_name: string
  min_year_of_study: number
  final_year_only: boolean
  stipend_or_ctc: string
  required_skills: { skill_name: string; min_proficiency: number; weight: number }[]
  created_at: string
}

export interface MatchExplanation {
  matched_skills: string[]
  below_target_skills: string[]
  missing_eligibility: string[]
  relevant_evidence_count: number
  is_eligible: boolean
}

export interface OpportunityMatch {
  opportunity: OpportunityOut
  match_score: number
  explanation: MatchExplanation
}

export interface ApplicationOut {
  id: number
  opportunity_id: number
  opportunity_title: string
  company_name: string
  student_id: number
  student_name?: string
  status: string
  match_score: number
  applied_at: string
}

// ---------- Auth ----------
export const authApi = {
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),
  registerStudent: (payload: object) => api.post("/auth/register/student", payload),
  registerCollege: (payload: object) => api.post("/auth/register/college", payload),
  registerIndustry: (payload: object) => api.post("/auth/register/industry", payload),
}

// ---------- Student ----------
export const studentApi = {
  skillPassport: () => api.get<SkillPassport>("/students/me/skill-passport"),
  addEvidence: (payload: { skill_name: string; type: string; title: string; description?: string; source_url?: string }) =>
    api.post("/students/me/evidence", payload),
  verifyEvidence: (id: number) => api.post(`/students/me/evidence/${id}/verify`),
  skillGrowth: (skillName: string) => api.get(`/students/me/skill-growth/${encodeURIComponent(skillName)}`),
  colleges: () => api.get("/students/colleges"),
  joinCollege: (collegeId: number) => api.post(`/students/me/join-college?college_id=${collegeId}`),
}

// ---------- Skill Gap ----------
export const gapApi = {
  roles: () => api.get("/gap/roles"),
  report: (roleTitle: string) => api.get<GapReport>(`/gap/report?role_title=${encodeURIComponent(roleTitle)}`),
  generateRoadmap: (skillName: string, targetScore = 70) =>
    api.post<SkillRoadmap>(`/gap/roadmap/${encodeURIComponent(skillName)}/generate?target_score=${targetScore}`),
  getRoadmap: (skillName: string) => api.get<SkillRoadmap>(`/gap/roadmap/${encodeURIComponent(skillName)}`),
  completeStep: (stepId: number) => api.patch(`/gap/roadmap/step/${stepId}/complete`),
}

// ---------- Assessments ----------
export const assessmentApi = {
  start: (payload: { skill_name: string; topic_focus?: string; num_questions?: number }) =>
    api.post("/assessments/start", payload),
  submit: (payload: { attempt_id: number; answers: Record<string, string[]> }) =>
    api.post("/assessments/submit", payload),
}

// ---------- Opportunities ----------
export const opportunityApi = {
  list: () => api.get<OpportunityOut[]>("/opportunities"),
  mine: () => api.get<OpportunityOut[]>("/opportunities/industry/mine"),
  create: (payload: object) => api.post("/opportunities", payload),
  matches: () => api.get<OpportunityMatch[]>("/opportunities/matches/for-me"),
  apply: (opportunityId: number) => api.post<ApplicationOut>("/opportunities/apply", { opportunity_id: opportunityId }),
  myApplications: () => api.get<ApplicationOut[]>("/opportunities/applications/mine"),
  applicationsFor: (opportunityId: number) => api.get<ApplicationOut[]>(`/opportunities/${opportunityId}/applications`),
  updateStatus: (applicationId: number, status: string) =>
    api.patch(`/opportunities/applications/${applicationId}/status`, { status }),
  submitFeedback: (payload: object) => api.post("/opportunities/feedback", payload),
}

// ---------- College ----------
export const collegeApi = {
  dashboard: () => api.get("/college/dashboard"),
  students: () => api.get("/college/students"),
}

// ---------- Admin ----------
export const adminApi = {
  stats: () => api.get("/admin/stats"),
  evidenceQueue: () => api.get("/admin/moderation/evidence"),
  moderateEvidence: (id: number, newStatus: string) =>
    api.patch(`/admin/moderation/evidence/${id}?new_status=${newStatus}`),
  colleges: () => api.get("/admin/colleges"),
  verifyCollege: (id: number) => api.patch(`/admin/colleges/${id}/verify`),
  companies: () => api.get("/admin/companies"),
  verifyCompany: (id: number) => api.patch(`/admin/companies/${id}/verify`),
}

// ---------- AI ----------
export interface ReadinessBreakdown {
  overall_readiness: number
  weights: Record<string, number>
  components: Record<string, number>
  weighted_contributions: Record<string, number>
}

export const aiApi = {
  status: () => api.get<{ ai_configured: boolean; provider: string }>("/ai/status"),
  analyzeResume: (file: File) => {
    const form = new FormData()
    form.append("file", file)
    return api.post("/ai/resume/analyze", form, { headers: { "Content-Type": "multipart/form-data" } })
  },
  analyzeGithub: (repoUrl: string) => api.post("/ai/github/analyze", { repo_url: repoUrl }),
  acceptSkills: (payload: { source: "resume" | "github"; source_title?: string; skills: { name: string; confidence: number; evidence?: string }[] }) =>
    api.post("/ai/skills/accept", payload),
  analyzeEvidence: (evidenceId: number) => api.post(`/ai/evidence/${evidenceId}/analyze`),
  adaptiveStart: (skillName: string) => api.post("/ai/assessment/adaptive/start", { skill_name: skillName }),
  adaptiveNext: (sessionId: number, answer: string[]) => api.post("/ai/assessment/adaptive/next", { session_id: sessionId, answer }),
  roadmapGenerate: (targetCareer: string, weeklyHours = 6) => api.post("/ai/roadmap/generate", { target_career: targetCareer, weekly_hours: weeklyHours }),
  insights: () => api.get<ReadinessBreakdown>("/ai/insights"),
  copilotChat: (question: string) => api.post("/ai/copilot/chat", { question }),
  copilotHistory: () => api.get("/ai/copilot/history"),
}
