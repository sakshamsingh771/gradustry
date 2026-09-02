import { Routes, Route } from "react-router-dom"
import { ProtectedRoute } from "@/routes/ProtectedRoute"

import Landing from "@/pages/public/Landing"
import Login from "@/pages/public/Login"
import Register from "@/pages/public/Register"
import PublicOpportunities from "@/pages/public/PublicOpportunities"

import StudentLayout from "@/pages/student/StudentLayout"
import StudentDashboard from "@/pages/student/Dashboard"
import SkillPassport from "@/pages/student/SkillPassport"
import SkillGap from "@/pages/student/SkillGap"
import EvidenceCenter from "@/pages/student/Evidence"
import Assessments from "@/pages/student/Assessments"
import StudentOpportunities from "@/pages/student/Opportunities"
import Applications from "@/pages/student/Applications"
import ResumeAnalyzer from "@/pages/student/ResumeAnalyzer"
import GithubAnalyzer from "@/pages/student/GithubAnalyzer"
import AdaptiveAssessment from "@/pages/student/AdaptiveAssessment"
import AIRoadmap from "@/pages/student/AIRoadmap"
import CareerCopilot from "@/pages/student/CareerCopilot"

import CollegeLayout from "@/pages/college/CollegeLayout"
import CollegeDashboard from "@/pages/college/Dashboard"
import CollegeStudents from "@/pages/college/Students"

import IndustryLayout from "@/pages/industry/IndustryLayout"
import IndustryDashboard from "@/pages/industry/Dashboard"
import IndustryOpportunities from "@/pages/industry/Opportunities"
import Candidates from "@/pages/industry/Candidates"

import AdminLayout from "@/pages/admin/AdminLayout"
import AdminDashboard from "@/pages/admin/Dashboard"
import Moderation from "@/pages/admin/Moderation"
import AdminColleges from "@/pages/admin/Colleges"
import AdminCompanies from "@/pages/admin/Companies"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/opportunities" element={<PublicOpportunities />} />

      <Route path="/student" element={<ProtectedRoute allow={["student"]}><StudentLayout /></ProtectedRoute>}>
        <Route index element={<StudentDashboard />} />
        <Route path="passport" element={<SkillPassport />} />
        <Route path="gap" element={<SkillGap />} />
        <Route path="evidence" element={<EvidenceCenter />} />
        <Route path="assessments" element={<Assessments />} />
        <Route path="opportunities" element={<StudentOpportunities />} />
        <Route path="applications" element={<Applications />} />
        <Route path="resume-analyzer" element={<ResumeAnalyzer />} />
        <Route path="github-analyzer" element={<GithubAnalyzer />} />
        <Route path="adaptive-assessment" element={<AdaptiveAssessment />} />
        <Route path="ai-roadmap" element={<AIRoadmap />} />
        <Route path="copilot" element={<CareerCopilot />} />
      </Route>

      <Route path="/college" element={<ProtectedRoute allow={["college"]}><CollegeLayout /></ProtectedRoute>}>
        <Route index element={<CollegeDashboard />} />
        <Route path="students" element={<CollegeStudents />} />
      </Route>

      <Route path="/industry" element={<ProtectedRoute allow={["industry"]}><IndustryLayout /></ProtectedRoute>}>
        <Route index element={<IndustryDashboard />} />
        <Route path="opportunities" element={<IndustryOpportunities />} />
        <Route path="candidates" element={<Candidates />} />
      </Route>

      <Route path="/admin" element={<ProtectedRoute allow={["admin"]}><AdminLayout /></ProtectedRoute>}>
        <Route index element={<AdminDashboard />} />
        <Route path="moderation" element={<Moderation />} />
        <Route path="colleges" element={<AdminColleges />} />
        <Route path="companies" element={<AdminCompanies />} />
      </Route>

      <Route path="*" element={<Landing />} />
    </Routes>
  )
}
