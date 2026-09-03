import { Link, useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { PublicNav } from "@/components/layout/PublicNav"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useAuth } from "@/context/AuthContext"
import { studentApi, opportunityApi, aiApi } from "@/lib/api"
import {
  ShieldCheck, TrendingUp, Target, Route as RouteIcon, Building2, LineChart,
  FileUp, GitFork, Sparkles, Bot, ClipboardList, BadgeCheck, ArrowRight,
  Search, User, School, Compass, CheckCircle2,
} from "lucide-react"

const roleHome: Record<string, string> = { student: "/student", college: "/college", industry: "/industry", admin: "/admin" }

const understandCards = [
  { icon: BadgeCheck, title: "Skills", body: "What you know, scored per skill." },
  { icon: ShieldCheck, title: "Evidence", body: "What proves you know it — certs, projects, assessments." },
  { icon: Target, title: "Skill Gap", body: "What's missing for the role you want." },
  { icon: RouteIcon, title: "Roadmap", body: "What to learn next, staged and specific." },
  { icon: LineChart, title: "Career Readiness", body: "How prepared you are, right now." },
  { icon: TrendingUp, title: "Opportunity Match", body: "Where your skills fit, explained." },
]

const loop = ["Discover", "Prove", "Measure", "Improve", "Match", "Industry Feedback", "Better Skills", "Better Opportunities"]

const aiFeatures = [
  { icon: FileUp, title: "AI Resume Analyzer", body: "Turn your resume into structured skill evidence.", to: "/student/resume-analyzer" },
  { icon: GitFork, title: "AI GitHub Analyzer", body: "Understand the technical signals behind your projects.", to: "/student/github-analyzer" },
  { icon: Sparkles, title: "Adaptive AI Assessment", body: "Assessments that adjust to what you actually know.", to: "/student/adaptive-assessment" },
  { icon: RouteIcon, title: "AI Career Roadmap", body: "A generated, staged plan to close your gaps.", to: "/student/ai-roadmap" },
  { icon: Bot, title: "AI Career Copilot", body: "Ask \"Am I ready?\" and get a real answer.", to: "/student/copilot" },
]

const roleEntries = [
  { icon: User, title: "Students", body: "Build skills → prove skills → get matched.", role: "student" as const },
  { icon: School, title: "Colleges", body: "Track student skill development and readiness.", role: "college" as const },
  { icon: Building2, title: "Industry", body: "Discover evidence-backed talent.", role: "industry" as const },
]

export default function Landing() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const isStudent = user?.role === "student"

  const passportQ = useQuery({
    queryKey: ["skill-passport"], queryFn: () => studentApi.skillPassport().then((r) => r.data), enabled: isStudent,
  })
  const matchesQ = useQuery({
    queryKey: ["matches"], queryFn: () => opportunityApi.matches().then((r) => r.data), enabled: isStudent,
  })
  const insightsQ = useQuery({
    queryKey: ["ai-insights"], queryFn: () => aiApi.insights().then((r) => r.data), enabled: isStudent,
  })
  const publicOppsQ = useQuery({
    queryKey: ["public-opportunities"], queryFn: () => opportunityApi.list().then((r) => r.data), enabled: !isStudent,
  })

  const passport = passportQ.data
  const verifiedSkills = passport?.skills.filter((s) => s.confidence_level === "High").length ?? 0

  const primaryCta = isStudent
    ? { label: "View My Profile", to: "/student/passport" }
    : { label: "Build My Career Profile", to: user ? roleHome[user.role] : "/register" }

  const quickActions = [
    { icon: BadgeCheck, title: "Complete Your Profile", to: isStudent ? "/student/passport" : "/register" },
    { icon: FileUp, title: "Upload Resume", to: isStudent ? "/student/resume-analyzer" : "/register" },
    { icon: GitFork, title: "Analyze GitHub", to: isStudent ? "/student/github-analyzer" : "/register" },
    { icon: ClipboardList, title: "Assess Your Skills", to: isStudent ? "/student/assessments" : "/register" },
    { icon: Target, title: "Find Skill Gaps", to: isStudent ? "/student/gap" : "/register" },
    { icon: Search, title: "Explore Opportunities", to: "/opportunities" },
  ]

  return (
    <div>
      <PublicNav />

      {/* HERO */}
      <section className="mx-auto max-w-6xl px-6 pb-16 pt-16 md:pt-24">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <span className="inline-block rounded-full border border-border bg-surface-alt px-3 py-1 text-xs text-muted">
              Discover → Prove → Improve → Get Matched
            </span>
            <h1 className="mt-6 font-display text-4xl leading-tight md:text-6xl">
              {isStudent ? `Welcome back, ${user!.full_name.split(" ")[0]}.` : "Build Skills. Prove Them. Get Discovered."}
            </h1>
            <p className="mt-5 max-w-xl text-base text-muted md:text-lg">
              {isStudent
                ? "Here's where your skill journey stands — and what to do next."
                : "Gradustry helps you build real skills, prove them with evidence, identify your gaps, follow a personalized roadmap, and discover opportunities that actually fit."}
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button size="lg" onClick={() => navigate(primaryCta.to)}>{primaryCta.label}</Button>
              <Button size="lg" variant="outline" onClick={() => navigate("/opportunities")}>Explore Opportunities</Button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}
            className="rounded-2xl border border-border bg-surface p-6 shadow-sm"
          >
            {isStudent && passport ? (
              <>
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg">Career Readiness</p>
                  <span className="font-display text-3xl text-accent">{passport.career_readiness}%</span>
                </div>
                <div className="mt-4 space-y-3">
                  {passport.skills.slice(0, 4).map((s) => (
                    <div key={s.id}>
                      <div className="mb-1 flex justify-between text-xs text-muted">
                        <span>{s.skill_name}</span><span>{s.proficiency_score.toFixed(0)}%</span>
                      </div>
                      <Progress value={s.proficiency_score} />
                    </div>
                  ))}
                  {!passport.skills.length && <p className="text-sm text-muted">No skills tracked yet — add evidence to get started.</p>}
                </div>
              </>
            ) : (
              <>
                <p className="font-display text-lg">The Gradustry Loop</p>
                <div className="mt-4 space-y-3">
                  {[Compass, ShieldCheck, TrendingUp, Target].map((Icon, i) => (
                    <div key={i} className="flex items-center gap-3 rounded-lg bg-surface-alt p-3">
                      <Icon className="h-5 w-5 shrink-0 text-accent" />
                      <span className="text-sm">{["Discover opportunities", "Prove your skills", "Improve with a roadmap", "Get matched"][i]}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </motion.div>
        </div>
      </section>

      {/* QUICK CAREER ACTIONS */}
      <section className="border-t border-border bg-surface-alt/40 py-16">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl md:text-3xl">Quick actions</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {quickActions.map(({ icon: Icon, title, to }) => (
              <button
                key={title}
                onClick={() => navigate(to)}
                className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 text-left hover:border-accent"
              >
                <Icon className="h-5 w-5 shrink-0 text-accent" />
                <span className="font-medium">{title}</span>
                <ArrowRight className="ml-auto h-4 w-4 text-muted" />
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* YOUR CAREER, UNDERSTOOD */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-display text-2xl md:text-3xl">Your career, understood.</h2>
        <p className="mt-2 max-w-2xl text-muted">Six layers of intelligence, all connected.</p>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {understandCards.map(({ icon: Icon, title, body }) => (
            <div key={title} className="rounded-xl border border-border bg-surface p-5">
              <Icon className="h-5 w-5 text-accent" />
              <p className="mt-3 font-display text-base">{title}</p>
              <p className="mt-1 text-sm text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CAREER LOOP */}
      <section className="border-t border-border bg-surface-alt/40 py-20">
        <div className="mx-auto max-w-4xl px-6">
          <h2 className="font-display text-2xl md:text-3xl">The Gradustry Career Loop</h2>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            {loop.map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <span className="rounded-full border border-border bg-surface px-4 py-2 text-sm">{step}</span>
                {i < loop.length - 1 && <ArrowRight className="h-4 w-4 text-muted" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* OPPORTUNITY DISCOVERY */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-display text-2xl md:text-3xl">Opportunities for you</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {(isStudent ? matchesQ.data : undefined)?.slice(0, 6).map((m) => (
            <Card key={m.opportunity.id}>
              <CardHeader>
                <CardTitle>{m.opportunity.title}</CardTitle>
                <CardDescription>{m.opportunity.company_name} · {m.opportunity.location}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-accent">Match: {m.match_score.toFixed(0)}%</p>
                {m.explanation.below_target_skills.length > 0 && (
                  <p className="mt-1 text-xs text-muted">Gap: {m.explanation.below_target_skills.join(", ")}</p>
                )}
                <Button className="mt-4 w-full" variant="outline" onClick={() => navigate("/student/opportunities")}>View</Button>
              </CardContent>
            </Card>
          ))}
          {!isStudent && publicOppsQ.data?.slice(0, 6).map((o) => (
            <Card key={o.id}>
              <CardHeader>
                <CardTitle>{o.title}</CardTitle>
                <CardDescription>{o.company_name} · {o.location} · {o.role_type}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {o.required_skills.map((s) => <span key={s.skill_name} className="rounded-full bg-surface-alt px-2.5 py-1 text-xs">{s.skill_name}</span>)}
                </div>
                <Button className="mt-4 w-full" variant="outline" onClick={() => navigate("/register")}>Log in to see your match</Button>
              </CardContent>
            </Card>
          ))}
          {isStudent && matchesQ.data?.length === 0 && (
            <p className="text-sm text-muted">No opportunities matched yet. Complete your profile to unlock personalized matches.</p>
          )}
          {!isStudent && publicOppsQ.data?.length === 0 && <p className="text-sm text-muted">No opportunities posted yet.</p>}
        </div>
      </section>

      {/* AI CAREER INTELLIGENCE */}
      <section className="border-t border-border bg-surface-alt/40 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl md:text-3xl">AI Career Intelligence</h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {aiFeatures.map(({ icon: Icon, title, body, to }) => (
              <button
                key={title}
                onClick={() => navigate(isStudent ? to : "/register")}
                className="rounded-xl border border-border bg-surface p-5 text-left hover:border-accent"
              >
                <Icon className="h-5 w-5 text-accent" />
                <p className="mt-3 font-display text-base">{title}</p>
                <p className="mt-1 text-sm text-muted">{body}</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* CAREER READINESS */}
      <section className="mx-auto max-w-4xl px-6 py-20">
        <h2 className="font-display text-2xl md:text-3xl">Career Readiness</h2>
        {isStudent && insightsQ.data ? (
          <div className="mt-6 rounded-xl border border-border bg-surface p-6">
            <div className="flex items-center justify-between">
              <span className="text-muted">Overall readiness</span>
              <span className="font-display text-3xl text-accent">{insightsQ.data.overall_readiness}%</span>
            </div>
            <div className="mt-4 space-y-3">
              {Object.entries(insightsQ.data.components).map(([key, val]) => (
                <div key={key}>
                  <div className="mb-1 flex justify-between text-xs text-muted"><span className="capitalize">{key.replace("_", " ")}</span><span>{val as number}%</span></div>
                  <Progress value={val as number} className="h-1.5" />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-border bg-surface p-6">
            <p className="text-muted">Your readiness score is calculated from your skills, evidence, assessments, and industry feedback — not guessed.</p>
            <Button className="mt-4" onClick={() => navigate("/register")}>See my readiness score</Button>
          </div>
        )}
      </section>

      {/* WHY GRADUSTRY */}
      <section id="why-gradustry" className="border-t border-border bg-surface-alt/40 py-20">
        <div className="mx-auto max-w-4xl px-6">
          <h2 className="font-display text-2xl md:text-3xl">Why Gradustry</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div className="rounded-xl border border-border bg-surface p-5">
              <p className="text-sm text-muted">Traditional platforms</p>
              <p className="mt-2 font-display">Profile → Search → Apply</p>
            </div>
            <div className="rounded-xl border border-accent bg-surface p-5">
              <p className="text-sm text-accent">Gradustry</p>
              <p className="mt-2 font-display text-sm leading-relaxed">
                Profile → Evidence → Skill Intelligence → Skill Gap → Roadmap → Readiness → Match → Opportunity
              </p>
            </div>
          </div>
        </div>
      </section>

               {/* ROLE-BASED ENTRY */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-display text-2xl md:text-3xl">Built for everyone in the loop</h2>
        <div className="mt-8 grid gap-5 sm:grid-cols-3">
          {roleEntries.map(({ icon: Icon, title, body, role }) => {
            const isOwnRole = user?.role === role
            return (
              <div key={title} className="rounded-xl border border-border bg-surface p-6 text-center">
                <Icon className="mx-auto h-6 w-6 text-accent" />
                <p className="mt-3 font-display text-lg">{title}</p>
                <p className="mt-1 text-sm text-muted">{body}</p>
                {!user && (
                  <Button variant="outline" size="sm" className="mt-4" onClick={() => navigate("/register")}>
                    Get Started
                  </Button>
                )}
                {user && isOwnRole && (
                  <Button variant="outline" size="sm" className="mt-4" onClick={() => navigate(roleHome[role])}>
                    Go to Dashboard
                  </Button>
                )}
                {user && !isOwnRole && (
                  <p className="mt-4 text-xs text-muted">Not available for your account type</p>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="border-t border-border bg-surface-alt/40 py-16">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <CheckCircle2 className="mx-auto h-8 w-8 text-accent" />
          <h2 className="mt-4 font-display text-2xl md:text-3xl">Don't just apply for opportunities. Become ready for them.</h2>
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <Button size="lg" onClick={() => navigate(primaryCta.to)}>{primaryCta.label}</Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/opportunities")}>Explore Opportunities</Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 text-sm text-muted sm:flex-row">
          <span>© {new Date().getFullYear()} Gradustry</span>
          <span>Built for SIH 2026 · Academia–Industry Skill Intelligence</span>
        </div>
      </footer>
    </div>
  )
}