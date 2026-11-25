"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { User, Briefcase, Settings, Save } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { profileApi, extractApiError } from "@/services/api";
import { cn } from "@/utils/cn";

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [skillInput, setSkillInput] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get().then(r => r.data),
  });

  const [profile, setProfile] = useState<any>({});
  const [prefs, setPrefs] = useState<any>({});

  React.useEffect(() => {
    if (data) {
      setProfile(data.profile || {});
      setPrefs(data.preferences || {});
    }
  }, [data]);

  const updateProfileMutation = useMutation({
    mutationFn: () => profileApi.update(profile),
    onSuccess: () => { toast.success("Profile saved!"); queryClient.invalidateQueries({ queryKey: ["profile"] }); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const updatePrefsMutation = useMutation({
    mutationFn: () => profileApi.updatePreferences(prefs),
    onSuccess: () => { toast.success("Preferences saved!"); queryClient.invalidateQueries({ queryKey: ["profile"] }); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const addSkill = (type: "technical" | "soft") => {
    if (!skillInput.trim()) return;
    const key = type === "technical" ? "technical_skills" : "soft_skills";
    const existing = profile[key] || [];
    if (!existing.includes(skillInput.trim())) {
      setProfile((p: any) => ({ ...p, [key]: [...existing, skillInput.trim()] }));
    }
    setSkillInput("");
  };

  const removeSkill = (skill: string, type: "technical" | "soft") => {
    const key = type === "technical" ? "technical_skills" : "soft_skills";
    setProfile((p: any) => ({ ...p, [key]: (p[key] || []).filter((s: string) => s !== skill) }));
  };

  if (isLoading) return <DashboardLayout title="Profile"><div className="animate-pulse space-y-4">{Array.from({length:4}).map((_,i)=><div key={i} className="h-24 bg-muted rounded-lg"/>)}</div></DashboardLayout>;

  return (
    <DashboardLayout title="Profile & Preferences" subtitle="Your professional profile used by AI for matching and outreach">
      <div className="max-w-3xl">
        <Tabs defaultValue="personal">
          <TabsList className="mb-6">
            <TabsTrigger value="personal">Personal Info</TabsTrigger>
            <TabsTrigger value="professional">Professional</TabsTrigger>
            <TabsTrigger value="preferences">Job Preferences</TabsTrigger>
            <TabsTrigger value="career">Career Goals</TabsTrigger>
          </TabsList>

          <TabsContent value="personal">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: "phone", label: "Phone" },
                    { key: "current_location", label: "Current Location" },
                    { key: "linkedin_url", label: "LinkedIn URL" },
                    { key: "portfolio_url", label: "Portfolio / GitHub" },
                    { key: "website_url", label: "Personal Website" },
                    { key: "notice_period", label: "Notice Period" },
                  ].map(({ key, label }) => (
                    <div key={key} className="space-y-1.5">
                      <Label>{label}</Label>
                      <Input
                        value={profile[key] || ""}
                        onChange={e => setProfile((p: any) => ({ ...p, [key]: e.target.value }))}
                      />
                    </div>
                  ))}
                </div>
                <Button loading={updateProfileMutation.isPending} onClick={() => updateProfileMutation.mutate()} className="gap-2">
                  <Save className="h-4 w-4" /> Save Changes
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="professional">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: "current_title", label: "Current Title" },
                    { key: "current_company", label: "Current Company" },
                    { key: "total_experience_years", label: "Total Experience (years)", type: "number" },
                  ].map(({ key, label, type }) => (
                    <div key={key} className="space-y-1.5">
                      <Label>{label}</Label>
                      <Input
                        type={type || "text"}
                        value={profile[key] || ""}
                        onChange={e => setProfile((p: any) => ({ ...p, [key]: e.target.value }))}
                      />
                    </div>
                  ))}
                </div>

                <div className="space-y-1.5">
                  <Label>Professional Summary</Label>
                  <Textarea
                    rows={4}
                    value={profile.professional_summary || ""}
                    onChange={e => setProfile((p: any) => ({ ...p, professional_summary: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Technical Skills</Label>
                  <div className="flex gap-2">
                    <Input placeholder="Add skill..." value={skillInput} onChange={e => setSkillInput(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addSkill("technical"))} />
                    <Button type="button" onClick={() => addSkill("technical")}>Add</Button>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {(profile.technical_skills || []).map((s: string) => (
                      <Badge key={s} variant="secondary" className="cursor-pointer" onClick={() => removeSkill(s, "technical")}>{s} ×</Badge>
                    ))}
                  </div>
                </div>

                <Button loading={updateProfileMutation.isPending} onClick={() => updateProfileMutation.mutate()} className="gap-2">
                  <Save className="h-4 w-4" /> Save Changes
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="preferences">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: "expected_salary", label: "Expected Salary", type: "number" },
                    { key: "min_salary", label: "Minimum Salary", type: "number" },
                  ].map(({ key, label, type }) => (
                    <div key={key} className="space-y-1.5">
                      <Label>{label}</Label>
                      <Input type={type} value={prefs[key] || ""} onChange={e => setPrefs((p: any) => ({ ...p, [key]: e.target.value }))} />
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  <Label>Work Modes</Label>
                  <div className="flex gap-2 flex-wrap">
                    {[{ k: "remote_ok", l: "Remote" }, { k: "hybrid_ok", l: "Hybrid" }, { k: "onsite_ok", l: "On-site" }].map(({ k, l }) => (
                      <button key={k} onClick={() => setPrefs((p: any) => ({ ...p, [k]: !p[k] }))}
                        className={cn("px-3 py-1.5 rounded-full text-sm border",
                          prefs[k] ? "bg-primary text-primary-foreground border-primary" : "border-input")}>
                        {l}
                      </button>
                    ))}
                  </div>
                </div>
                <Button loading={updatePrefsMutation.isPending} onClick={() => updatePrefsMutation.mutate()} className="gap-2">
                  <Save className="h-4 w-4" /> Save Preferences
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="career">
            <Card>
              <CardContent className="p-6 space-y-4">
                {[
                  { key: "career_objective", label: "Career Objective" },
                  { key: "short_term_goals", label: "Short-term Goals (1-2 years)" },
                  { key: "long_term_goals", label: "Long-term Goals (5+ years)" },
                  { key: "desired_responsibilities", label: "Desired Responsibilities" },
                ].map(({ key, label }) => (
                  <div key={key} className="space-y-1.5">
                    <Label>{label}</Label>
                    <Textarea rows={3} value={prefs[key] || ""}
                      onChange={e => setPrefs((p: any) => ({ ...p, [key]: e.target.value }))} />
                  </div>
                ))}
                <Button loading={updatePrefsMutation.isPending} onClick={() => updatePrefsMutation.mutate()} className="gap-2">
                  <Save className="h-4 w-4" /> Save Goals
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
