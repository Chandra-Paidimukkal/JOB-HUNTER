"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Sparkles, Copy, Edit3, RefreshCw, Save, Send, CheckCircle,
  Building2, User, Briefcase, Mail, MessageSquare, ChevronDown,
  Linkedin, FileText, Settings2, Zap, Info
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { aiApi, outreachApi, extractApiError } from "@/services/api";
import { cn } from "@/utils/cn";

const EMAIL_TYPES = [
  { value: "job_application", label: "Job Application Email", icon: Briefcase },
  { value: "hr_outreach", label: "HR Outreach Email", icon: User },
  { value: "hiring_manager", label: "Hiring Manager Email", icon: Building2 },
  { value: "cold_outreach", label: "Cold Outreach Email", icon: Mail },
  { value: "referral_request", label: "Referral Request", icon: User },
  { value: "recruiter_introduction", label: "Recruiter Introduction", icon: User },
  { value: "post_application_followup", label: "Post-Application Follow-up", icon: RefreshCw },
  { value: "interview_thankyou", label: "Interview Thank-You", icon: CheckCircle },
  { value: "linkedin_connection", label: "LinkedIn Connection", icon: Linkedin },
  { value: "linkedin_followup", label: "LinkedIn Follow-up", icon: Linkedin },
  { value: "networking", label: "Networking Outreach", icon: MessageSquare },
];

const TONES = ["professional", "friendly", "formal", "confident", "conversational", "concise"];
const EMAIL_LENGTHS = ["short", "medium", "detailed"];

interface GeneratedResult {
  subject_lines: string[];
  short_version: string;
  medium_version: string;
  detailed_version: string;
  reasoning: string;
  suggestions: string[];
}

export default function OutreachStudioPage() {
  const [form, setForm] = useState({
    email_type: "hr_outreach",
    company_name: "",
    company_website: "",
    company_industry: "",
    contact_name: "",
    contact_designation: "",
    contact_email: "",
    department: "",
    job_title: "",
    job_description: "",
    tone: "professional",
    additional_instructions: "",
  });

  const [result, setResult] = useState<GeneratedResult | null>(null);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedLength, setSelectedLength] = useState("medium");
  const [editedBody, setEditedBody] = useState("");
  const [copied, setCopied] = useState(false);
  const [savedToOutreach, setSavedToOutreach] = useState(false);

  const generateMutation = useMutation({
    mutationFn: () => aiApi.generateEmail(form),
    onSuccess: (res) => {
      const data = res.data as GeneratedResult;
      setResult(data);
      setSelectedSubject(data.subject_lines?.[0] || "");
      setEditedBody(data.medium_version || "");
      toast.success("Email generated!");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const saveToOutreachMutation = useMutation({
    mutationFn: () =>
      outreachApi.create({
        company_name: form.company_name,
        company_website: form.company_website,
        company_industry: form.company_industry,
        contact_name: form.contact_name,
        contact_designation: form.contact_designation,
        contact_email: form.contact_email,
        department: form.department,
        email_type: form.email_type,
        email_subject: selectedSubject,
        generated_email: editedBody,
        status: "email_generated",
      }),
    onSuccess: () => {
      setSavedToOutreach(true);
      toast.success("Saved to Email Campaigns!");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const selectedBody = (() => {
    if (!result) return "";
    if (selectedLength === "short") return result.short_version;
    if (selectedLength === "detailed") return result.detailed_version;
    return result.medium_version;
  })();

  React.useEffect(() => {
    if (selectedBody) setEditedBody(selectedBody);
  }, [selectedLength]);

  const updateForm = (key: string, value: string) => {
    setForm(f => ({ ...f, [key]: value }));
  };

  return (
    <DashboardLayout
      title="AI Outreach Studio"
      subtitle="Generate personalized professional emails and messages powered by Groq AI"
    >
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Input form */}
        <div className="xl:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Settings2 className="h-4 w-4 text-primary" />
                Email Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Email Type */}
              <div className="space-y-1.5">
                <Label className="text-xs">Email Type *</Label>
                <Select value={form.email_type} onValueChange={v => updateForm("email_type", v)}>
                  <SelectTrigger className="h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EMAIL_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Company */}
              <div className="space-y-1.5">
                <Label className="text-xs">Company Name *</Label>
                <Input
                  className="h-9 text-sm"
                  placeholder="Google, Microsoft, Startup..."
                  value={form.company_name}
                  onChange={e => updateForm("company_name", e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <Label className="text-xs">Website</Label>
                  <Input
                    className="h-9 text-sm"
                    placeholder="company.com"
                    value={form.company_website}
                    onChange={e => updateForm("company_website", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Industry</Label>
                  <Input
                    className="h-9 text-sm"
                    placeholder="Technology"
                    value={form.company_industry}
                    onChange={e => updateForm("company_industry", e.target.value)}
                  />
                </div>
              </div>

              {/* Recipient */}
              <div className="border-t border-border pt-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Recipient</p>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Name</Label>
                    <Input
                      className="h-9 text-sm"
                      placeholder="Jane Smith"
                      value={form.contact_name}
                      onChange={e => updateForm("contact_name", e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Designation</Label>
                    <Input
                      className="h-9 text-sm"
                      placeholder="HR Manager"
                      value={form.contact_designation}
                      onChange={e => updateForm("contact_designation", e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Email</Label>
                    <Input
                      className="h-9 text-sm"
                      placeholder="jane@company.com"
                      value={form.contact_email}
                      onChange={e => updateForm("contact_email", e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Department</Label>
                    <Input
                      className="h-9 text-sm"
                      placeholder="Engineering"
                      value={form.department}
                      onChange={e => updateForm("department", e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Job */}
              <div className="border-t border-border pt-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Job (Optional)</p>
                <div className="space-y-1.5">
                  <Label className="text-xs">Job Title</Label>
                  <Input
                    className="h-9 text-sm"
                    placeholder="Senior Software Engineer"
                    value={form.job_title}
                    onChange={e => updateForm("job_title", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Job Description (paste key requirements)</Label>
                  <Textarea
                    className="text-sm"
                    rows={3}
                    placeholder="Paste relevant job requirements..."
                    value={form.job_description}
                    onChange={e => updateForm("job_description", e.target.value)}
                  />
                </div>
              </div>

              {/* Style */}
              <div className="border-t border-border pt-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Style</p>
                <div className="space-y-1.5">
                  <Label className="text-xs">Tone</Label>
                  <div className="flex flex-wrap gap-1.5">
                    {TONES.map(tone => (
                      <button
                        key={tone}
                        onClick={() => updateForm("tone", tone)}
                        className={cn(
                          "text-xs px-2.5 py-1 rounded-full border capitalize transition-colors",
                          form.tone === tone
                            ? "bg-primary text-primary-foreground border-primary"
                            : "border-input hover:border-primary"
                        )}
                      >
                        {tone}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Additional Instructions</Label>
                  <Textarea
                    className="text-sm"
                    rows={2}
                    placeholder="Mention my Python expertise, focus on leadership experience..."
                    value={form.additional_instructions}
                    onChange={e => updateForm("additional_instructions", e.target.value)}
                  />
                </div>
              </div>

              <Button
                className="w-full gap-2"
                variant="gradient"
                size="lg"
                loading={generateMutation.isPending}
                disabled={!form.company_name}
                onClick={() => generateMutation.mutate()}
              >
                <Sparkles className="h-4 w-4" />
                {generateMutation.isPending ? "Generating..." : "Generate Email"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Output */}
        <div className="xl:col-span-3 space-y-4">
          {!result ? (
            <div className="flex flex-col items-center justify-center h-80 border-2 border-dashed border-border rounded-xl">
              <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <Sparkles className="h-7 w-7 text-primary" />
              </div>
              <h3 className="font-semibold text-lg">AI Email Generator</h3>
              <p className="text-muted-foreground text-sm mt-2 text-center max-w-xs">
                Fill in the details on the left and click Generate Email. AI will create personalized, professional outreach using your resume and profile.
              </p>
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {/* Subject lines */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Subject Line Options</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {result.subject_lines?.map((subject, i) => (
                    <div
                      key={i}
                      onClick={() => setSelectedSubject(subject)}
                      className={cn(
                        "p-3 rounded-lg border cursor-pointer transition-colors text-sm",
                        selectedSubject === subject
                          ? "border-primary bg-primary/5 font-medium"
                          : "border-border hover:border-primary/50"
                      )}
                    >
                      {selectedSubject === subject && (
                        <CheckCircle className="h-3.5 w-3.5 text-primary inline mr-2" />
                      )}
                      {subject}
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Email body */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">Email Body</CardTitle>
                    <div className="flex gap-1">
                      {EMAIL_LENGTHS.map(len => (
                        <button
                          key={len}
                          onClick={() => setSelectedLength(len)}
                          className={cn(
                            "text-xs px-2.5 py-1 rounded-full capitalize border transition-colors",
                            selectedLength === len
                              ? "bg-primary text-primary-foreground border-primary"
                              : "border-input hover:border-primary"
                          )}
                        >
                          {len}
                        </button>
                      ))}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Textarea
                    rows={12}
                    value={editedBody}
                    onChange={e => setEditedBody(e.target.value)}
                    className="text-sm font-mono leading-relaxed"
                  />

                  <div className="flex flex-wrap gap-2 mt-3">
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5"
                      onClick={() => handleCopy(editedBody)}
                    >
                      {copied ? <CheckCircle className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                      Copy
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5"
                      onClick={() => generateMutation.mutate()}
                      loading={generateMutation.isPending}
                    >
                      <RefreshCw className="h-3.5 w-3.5" /> Regenerate
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5"
                      onClick={() => saveToOutreachMutation.mutate()}
                      loading={saveToOutreachMutation.isPending}
                      disabled={savedToOutreach}
                    >
                      {savedToOutreach ? (
                        <><CheckCircle className="h-3.5 w-3.5 text-green-500" /> Saved</>
                      ) : (
                        <><Save className="h-3.5 w-3.5" /> Save to Campaigns</>
                      )}
                    </Button>
                    {form.contact_email && (
                      <Button size="sm" variant="gradient" className="gap-1.5" asChild>
                        <a href="/email-campaigns">
                          <Send className="h-3.5 w-3.5" /> Send via Gmail
                        </a>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* AI reasoning */}
              {result.reasoning && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                        <Zap className="h-3.5 w-3.5 text-primary" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-primary mb-1">AI Reasoning</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">{result.reasoning}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Suggestions */}
              {result.suggestions?.length > 0 && (
                <Card>
                  <CardContent className="p-4">
                    <p className="text-xs font-semibold mb-2 flex items-center gap-1.5">
                      <Info className="h-3.5 w-3.5 text-blue-500" /> Suggestions
                    </p>
                    <ul className="space-y-1">
                      {result.suggestions.map((s, i) => (
                        <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                          <span className="text-blue-500 mt-0.5">→</span> {s}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
