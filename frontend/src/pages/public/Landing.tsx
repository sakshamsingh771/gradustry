import { Link, useNavigate } from "react-router-dom"
import { PublicNav } from "@/components/layout/PublicNav"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { ShieldCheck, TrendingUp, Target, Route, Building2, LineChart } from "lucide-react"

const journey = [
  { icon: ShieldCheck, title: "Skill Passport", body: "A single, evidence-backed credential for every skill you claim." },
  { icon: Target, title: "AI Skill Gap", body: "See exactly how far you are from the role you want, and why." },
  { icon: Route, title: "Gap Closure Path", body: "A staged roadmap — learn, practice, build, re-assess." },
  { icon: TrendingUp, title: "Opportunity Match", body: "Explainable matches, not keyword guesswork." },
  { icon: Building2, title: "Industry Feedback", body: "Real evaluations feed back into your passport." },
  { icon: LineChart, title: "Skill Growth", body: "Watch your readiness compound over every semester." },
]

export default function Landing() {
  const navigate = useNavigate()
  return (
    <div>
      <PublicNav />

      <section className="mx-auto max-w-5xl px-6 pb-20 pt-16 text-center md:pt-24">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-block rounded-full border border-border bg-surface-alt px-3 py-1 text-xs text-muted">
            Academia–Industry Skill Intelligence
          </span>
          <h1 className="mt-6 font-display text-4xl leading-tight md:text-6xl">
            Turn your skills into your career.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base text-muted md:text-lg">
            Measure your skills. Build credible evidence. Close your skill gaps. Become industry-ready.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" onClick={() => navigate("/register")}>Build Your Skill Passport</Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/opportunities")}>Explore Opportunities</Button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mx-auto mt-16 max-w-md rounded-2xl border border-border bg-surface p-6 text-left shadow-sm"
        >
          <div className="flex items-center justify-between">
            <p className="font-display text-lg">Career Readiness</p>
            <span className="font-display text-3xl text-accent">78%</span>
          </div>
          <div className="mt-4 space-y-3">
            {[["Python", 84], ["React", 76], ["SQL", 68], ["Docker", 31]].map(([label, val]) => (
              <div key={label as string}>
                <div className="mb-1 flex justify-between text-xs text-muted">
                  <span>{label}</span><span>{val}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-surface-alt">
                  <div className="h-full rounded-full bg-accent" style={{ width: `${val}%` }} />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      <section id="how-it-works" className="border-t border-border bg-surface-alt/40 py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-2xl md:text-3xl">One continuous loop, not a job board.</h2>
          <p className="mt-2 max-w-2xl text-muted">
            Every stage feeds the next — evidence sharpens your score, your score reveals your gaps, closing gaps opens doors, and industry feedback closes the loop.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {journey.map(({ icon: Icon, title, body }) => (
              <div key={title} className="rounded-xl border border-border bg-surface p-5">
                <Icon className="h-5 w-5 text-accent" />
                <p className="mt-3 font-display text-base">{title}</p>
                <p className="mt-1 text-sm text-muted">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="passport" className="mx-auto max-w-5xl px-6 py-20">
        <div className="grid items-center gap-10 md:grid-cols-2">
          <div>
            <h2 className="font-display text-2xl md:text-3xl">Evidence, not vibes.</h2>
            <p className="mt-3 text-muted">
              Every skill score on Gradustry traces back to something real: a certificate, a GitHub project, an
              assessment, or verified industry feedback. We call this <em>evidence confidence</em> — never a
              claim of certainty, always a transparent "why?".
            </p>
            <Link to="/register" className="mt-5 inline-block text-accent underline underline-offset-4">
              Start building your passport →
            </Link>
          </div>
          <div className="rounded-xl border border-border bg-surface p-5">
            <p className="font-display text-lg">Python — 84%</p>
            <div className="mt-3 space-y-2 text-sm text-muted">
              <p>✓ Certificate — verified</p>
              <p>✓ GitHub project — verified</p>
              <p>✓ Assessment — 86%</p>
              <p>✓ Industry feedback — 8.4 / 10</p>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-surface-alt/40 py-16">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-display text-2xl md:text-3xl">Ready to see your readiness score?</h2>
          <Button size="lg" className="mt-6" onClick={() => navigate("/register")}>Build Your Skill Passport</Button>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 px-6 text-sm text-muted sm:flex-row">
          <span>© {new Date().getFullYear()} Gradustry</span>
          <span>Built for SIH 2026 · Academia–Industry Skill Intelligence</span>
        </div>
      </footer>
    </div>
  )
}
