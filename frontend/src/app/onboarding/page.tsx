"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Check, ChevronRight, ChevronLeft, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/utils/cn";
import { profileApi, extractApiError } from "@/services/api";

const STEPS = [
  { id: 1, title: "Personal Details", description: "Tell us about yourself" },
  { id: 2, title: "Professional Details", description: "Your work experience & skills" },
  { id: 3, title: "Job Preferences", description: "What kind of role are you looking for?" },
  { id: 4, title: "Career Objective", description: "Define your career direction" },
];

const SKILL_SUGGESTIONS = [
  "JavaScript", "TypeScript", "React", "Node.js", "Python", "FastAPI", "SQL",
  "PostgreSQL", "AWS", "Docker", "Kubernetes", "Git", "REST API", "GraphQL",
  "Machine Learning", "Data Analysis", "Project Management", "Agile", "Scrum",
  "Java", "C#", ".NET", "Vue.js", "Angular", "MongoDB", "Redis", "CI/CD",
];

const EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship"];
const WORK_MODES = ["Remote", "Hybrid", "On-site"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [personalData, setPersonalData] = useState({
    full_name: "", phone: "", current_location: "", preferred_locations: "",
    linkedin_url: "", portfolio_url: "", website_url: "",
  });

  const [professionalData, setProfessionalData] = useState({
    current_title: "", current_company: "", total_experience_years: "",
    professional_summary: "", technical_skills: [] as string[],
    soft_skills: [] as string[], industries: "", education: "",
    certifications: "",
  });

  const [preferencesData, setPreferencesData] = useState({
    preferred_titles: "", preferred_industries: "", preferred_companies: "",
    preferred_countries: "", preferred_cities: "",
    employment_types: [] as string[], work_modes: [] as string[],
    expected_salary: "", min_salary: "", currency: "USD",
    notice_period: "", willing_to_relocate: false,
  });

  const [objectiveData, setObjectiveData] = useState({
    career_objective: "", short_term_goals: "", long_term_goals: "",
    desired_responsibilities: "",
  });

  const [skillInput, setSkillInput] = useState("");
  const [softSkillInput, setSoftSkillInput] = useState("");

  const addSkill = (type: "technical" | "soft") => {
    const val = type === "technical" ? skillInput.trim() : softSkillInput.trim();
    if (!val) return;
    if (type === "technical") {
      if (!professionalData.technical_skills.includes(val)) {
        setProfessionalData(p => ({ ...p, technical_skills: [...p.technical_skills, val] }));
      }
      setSkillInput("");
    } else {
      if (!professionalData.soft_skills.includes(val)) {
        setProfessionalData(p => ({ ...p, soft_skills: [...p.soft_skills, val] }));
      }
      setSoftSkillInput("");
    }
  };

  const removeSkill = (skill: string, type: "technical" | "soft") => {
    if (type === "technical") {
      setProfessionalData(p => ({ ...p, technical_skills: p.technical_skills.filter(s => s !== skill) }));
    } else {
      setProfessionalData(p => ({ ...p, soft_skills: p.soft_skills.filter(s => s !== skill) }));
    }
  };

  const toggleEmployment = (type: string) => {
    setPreferencesData(p => ({
      ...p,
      employment_types: p.employment_types.includes(type)
        ? p.employment_types.filter(t => t !== type)
        : [...p.employment_types, type],
    }));
  };

  const toggleWorkMode = (mode: string) => {
    setPreferencesData(p => ({
      ...p,
      work_modes: p.work_modes.includes(mode)
        ? p.work_modes.filter(m => m !== mode)
        : [...p.work_modes, mode],
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const payload = {
        personal: personalData,
        professional: {
          ...professionalData,
          total_experience_years: parseFloat(professionalData.total_experience_years) || 0,
          industries: professionalData.industries.split(",").map(s => s.trim()).filter(Boolean),
        },
        preferences: {
          ...preferencesData,
          preferred_titles: preferencesData.preferred_titles.split(",").map(s => s.trim()).filter(Boolean),
          preferred_industries: preferencesData.preferred_industries.split(",").map(s => s.trim()).filter(Boolean),
          preferred_companies: preferencesData.preferred_companies.split(",").map(s => s.trim()).filter(Boolean),
          preferred_countries: preferencesData.preferred_countries.split(",").map(s => s.trim()).filter(Boolean),
          preferred_cities: preferencesData.preferred_cities.split(",").map(s => s.trim()).filter(Boolean),
          remote_ok: preferencesData.work_modes.includes("Remote"),
          hybrid_ok: preferencesData.work_modes.includes("Hybrid"),
          onsite_ok: preferencesData.work_modes.includes("On-site"),
          full_time: preferencesData.employment_types.includes("Full-time"),
          part_time: preferencesData.employment_types.includes("Part-time"),
          contract: preferencesData.employment_types.includes("Contract"),
          internship: preferencesData.employment_types.includes("Internship"),
          expected_salary: parseFloat(preferencesData.expected_salary) || undefined,
          min_salary: parseFloat(preferencesData.min_salary) || undefined,
        },
        objective: objectiveData,
      };

      await profileApi.completeOnboarding(payload);
      toast.success("Profile setup complete! Welcome to JobHunter AI.");
      router.push("/overview");
    } catch (error) {
      toast.error(extractApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  const stepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Full Name *</Label>
                <Input
                  placeholder="John Smith"
                  value={personalData.full_name}
                  onChange={e => setPersonalData(p => ({ ...p, full_name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Phone Number</Label>
                <Input
                  placeholder="+1 (555) 000-0000"
                  value={personalData.phone}
                  onChange={e => setPersonalData(p => ({ ...p, phone: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Current Location</Label>
                <Input
                  placeholder="New York, USA"
                  value={personalData.current_location}
                  onChange={e => setPersonalData(p => ({ ...p, current_location: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Preferred Locations</Label>
                <Input
                  placeholder="New York, San Francisco, Remote"
                  value={personalData.preferred_locations}
                  onChange={e => setPersonalData(p => ({ ...p, preferred_locations: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>LinkedIn Profile</Label>
                <Input
                  placeholder="https://linkedin.com/in/yourprofile"
                  value={personalData.linkedin_url}
                  onChange={e => setPersonalData(p => ({ ...p, linkedin_url: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Portfolio / GitHub</Label>
                <Input
                  placeholder="https://github.com/yourprofile"
                  value={personalData.portfolio_url}
                  onChange={e => setPersonalData(p => ({ ...p, portfolio_url: e.target.value }))}
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Current Job Title</Label>
                <Input
                  placeholder="Senior Software Engineer"
                  value={professionalData.current_title}
                  onChange={e => setProfessionalData(p => ({ ...p, current_title: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Current Company</Label>
                <Input
                  placeholder="Acme Corp"
                  value={professionalData.current_company}
                  onChange={e => setProfessionalData(p => ({ ...p, current_company: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Total Experience (years)</Label>
                <Input
                  type="number"
                  placeholder="5"
                  value={professionalData.total_experience_years}
                  onChange={e => setProfessionalData(p => ({ ...p, total_experience_years: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Industries</Label>
                <Input
                  placeholder="Technology, Finance, Healthcare"
                  value={professionalData.industries}
                  onChange={e => setProfessionalData(p => ({ ...p, industries: e.target.value }))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Professional Summary</Label>
              <Textarea
                placeholder="Brief summary of your professional background and expertise..."
                rows={3}
                value={professionalData.professional_summary}
                onChange={e => setProfessionalData(p => ({ ...p, professional_summary: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label>Technical Skills</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add skill..."
                  value={skillInput}
                  onChange={e => setSkillInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addSkill("technical"))}
                />
                <Button type="button" onClick={() => addSkill("technical")}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {SKILL_SUGGESTIONS.filter(s => !professionalData.technical_skills.includes(s)).slice(0, 10).map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setProfessionalData(p => ({ ...p, technical_skills: [...p.technical_skills, s] }))}
                    className="text-xs px-2 py-1 rounded-full border border-dashed border-muted-foreground text-muted-foreground hover:border-primary hover:text-primary"
                  >
                    + {s}
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {professionalData.technical_skills.map(skill => (
                  <Badge key={skill} variant="secondary" className="cursor-pointer" onClick={() => removeSkill(skill, "technical")}>
                    {skill} ×
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Soft Skills</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add soft skill..."
                  value={softSkillInput}
                  onChange={e => setSoftSkillInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addSkill("soft"))}
                />
                <Button type="button" onClick={() => addSkill("soft")}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {professionalData.soft_skills.map(skill => (
                  <Badge key={skill} variant="outline" className="cursor-pointer" onClick={() => removeSkill(skill, "soft")}>
                    {skill} ×
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Preferred Job Titles</Label>
                <Input
                  placeholder="Software Engineer, Full Stack Dev, Tech Lead"
                  value={preferencesData.preferred_titles}
                  onChange={e => setPreferencesData(p => ({ ...p, preferred_titles: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Preferred Industries</Label>
                <Input
                  placeholder="Technology, SaaS, Fintech"
                  value={preferencesData.preferred_industries}
                  onChange={e => setPreferencesData(p => ({ ...p, preferred_industries: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Preferred Countries</Label>
                <Input
                  placeholder="USA, UK, Canada"
                  value={preferencesData.preferred_countries}
                  onChange={e => setPreferencesData(p => ({ ...p, preferred_countries: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Preferred Cities</Label>
                <Input
                  placeholder="New York, San Francisco, London"
                  value={preferencesData.preferred_cities}
                  onChange={e => setPreferencesData(p => ({ ...p, preferred_cities: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Expected Salary (annual)</Label>
                <Input
                  type="number"
                  placeholder="120000"
                  value={preferencesData.expected_salary}
                  onChange={e => setPreferencesData(p => ({ ...p, expected_salary: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Minimum Acceptable Salary</Label>
                <Input
                  type="number"
                  placeholder="90000"
                  value={preferencesData.min_salary}
                  onChange={e => setPreferencesData(p => ({ ...p, min_salary: e.target.value }))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Employment Type</Label>
              <div className="flex flex-wrap gap-2">
                {EMPLOYMENT_TYPES.map(type => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => toggleEmployment(type)}
                    className={cn(
                      "px-4 py-2 rounded-full text-sm border transition-colors",
                      preferencesData.employment_types.includes(type)
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background border-input hover:border-primary"
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Work Mode</Label>
              <div className="flex flex-wrap gap-2">
                {WORK_MODES.map(mode => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => toggleWorkMode(mode)}
                    className={cn(
                      "px-4 py-2 rounded-full text-sm border transition-colors",
                      preferencesData.work_modes.includes(mode)
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background border-input hover:border-primary"
                    )}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Notice Period</Label>
              <Input
                placeholder="2 weeks, 1 month, Immediate"
                value={preferencesData.notice_period}
                onChange={e => setPreferencesData(p => ({ ...p, notice_period: e.target.value }))}
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Career Objective</Label>
              <Textarea
                placeholder="Describe your target career direction and what you're looking for in your next role..."
                rows={3}
                value={objectiveData.career_objective}
                onChange={e => setObjectiveData(p => ({ ...p, career_objective: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Desired Responsibilities</Label>
              <Textarea
                placeholder="What responsibilities are you eager to take on in your next role?"
                rows={3}
                value={objectiveData.desired_responsibilities}
                onChange={e => setObjectiveData(p => ({ ...p, desired_responsibilities: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Short-term Goals (1–2 years)</Label>
              <Textarea
                placeholder="What do you aim to achieve in the next 1-2 years professionally?"
                rows={2}
                value={objectiveData.short_term_goals}
                onChange={e => setObjectiveData(p => ({ ...p, short_term_goals: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Long-term Goals (5+ years)</Label>
              <Textarea
                placeholder="Where do you see yourself in 5+ years?"
                rows={2}
                value={objectiveData.long_term_goals}
                onChange={e => setObjectiveData(p => ({ ...p, long_term_goals: e.target.value }))}
              />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-blue-950/5 flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 p-6 border-b border-border">
        <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold">JobHunter AI</span>
        <span className="ml-auto text-sm text-muted-foreground">Setup your profile</span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-2xl">
          {/* Steps indicator */}
          <div className="flex items-center justify-between mb-8">
            {STEPS.map((s, i) => (
              <React.Fragment key={s.id}>
                <div className="flex flex-col items-center gap-1">
                  <div className={cn(
                    "w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors",
                    s.id < step ? "bg-green-500 text-white" :
                    s.id === step ? "gradient-brand text-white" :
                    "bg-muted text-muted-foreground"
                  )}>
                    {s.id < step ? <Check className="h-4 w-4" /> : s.id}
                  </div>
                  <span className={cn(
                    "text-xs font-medium hidden sm:block",
                    s.id === step ? "text-foreground" : "text-muted-foreground"
                  )}>
                    {s.title}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={cn(
                    "flex-1 h-0.5 mx-2",
                    s.id < step ? "bg-green-500" : "bg-muted"
                  )} />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Card */}
          <Card className="shadow-xl">
            <CardContent className="p-6">
              <div className="mb-6">
                <h2 className="text-xl font-bold">{STEPS[step - 1].title}</h2>
                <p className="text-muted-foreground text-sm mt-1">{STEPS[step - 1].description}</p>
              </div>

              {stepContent()}

              <div className="flex items-center justify-between mt-8 pt-4 border-t border-border">
                <Button
                  variant="outline"
                  onClick={() => setStep(s => Math.max(1, s - 1))}
                  disabled={step === 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" /> Back
                </Button>

                {step < 4 ? (
                  <Button onClick={() => setStep(s => s + 1)} variant="gradient">
                    Continue <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                ) : (
                  <Button onClick={handleSubmit} variant="gradient" loading={isSubmitting}>
                    {isSubmitting ? "Saving..." : "Complete Setup"}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <p className="text-center text-xs text-muted-foreground mt-4">
            Step {step} of {STEPS.length} · You can edit all details later in your profile
          </p>
        </div>
      </div>
    </div>
  );
}
