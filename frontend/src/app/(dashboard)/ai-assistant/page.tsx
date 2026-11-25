"use client";

import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bot, Sparkles, FileText, Mail, MessageSquare, Download, Edit3, CheckCircle } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { aiApi, jobsApi, extractApiError } from "@/services/api";

export default function AIAssistantPage() {
  const [selectedJobId, setSelectedJobId] = useState("");
  const [coverLetterStyle, setCoverLetterStyle] = useState("professional");
  const [coverLetter, setCoverLetter] = useState<any>(null);
  const [customizedResume, setCustomizedResume] = useState<any>(null);
  const [appQuestions, setAppQuestions] = useState("");
  const [appAnswers, setAppAnswers] = useState<any[]>([]);

  const { data: jobsData } = useQuery({
    queryKey: ["jobs-short"],
    queryFn: () => jobsApi.list({ per_page: 50 }).then(r => r.data),
  });

  const coverLetterMutation = useMutation({
    mutationFn: () => aiApi.generateCoverLetter({ job_id: selectedJobId, style: coverLetterStyle }),
    onSuccess: (res) => { setCoverLetter(res.data); toast.success("Cover letter generated!"); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const resumeMutation = useMutation({
    mutationFn: () => aiApi.customizeResume({ job_id: selectedJobId }),
    onSuccess: (res) => { setCustomizedResume(res.data); toast.success("Resume customized!"); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const answersMutation = useMutation({
    mutationFn: () => aiApi.generateApplicationAnswers({
      job_id: selectedJobId,
      questions: appQuestions.split("\n").filter(q => q.trim()),
    }),
    onSuccess: (res) => { setAppAnswers(res.data?.answers || []); toast.success("Answers generated!"); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const jobs = jobsData?.items || [];

  return (
    <DashboardLayout title="AI Application Assistant" subtitle="Let Groq AI prepare your complete application package">
      <div className="max-w-4xl">
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex gap-3">
              <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Select a job to prepare for..." />
                </SelectTrigger>
                <SelectContent>
                  {jobs.map((j: any) => (
                    <SelectItem key={j.id} value={j.id}>{j.title} — {j.company}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {!selectedJobId && (
              <p className="text-xs text-muted-foreground mt-2">Select a job from Discover Jobs or Recommended Jobs</p>
            )}
          </CardContent>
        </Card>

        <Tabs defaultValue="cover-letter">
          <TabsList className="mb-6">
            <TabsTrigger value="cover-letter" className="gap-1.5"><FileText className="h-3.5 w-3.5" /> Cover Letter</TabsTrigger>
            <TabsTrigger value="resume" className="gap-1.5"><Edit3 className="h-3.5 w-3.5" /> Custom Resume</TabsTrigger>
            <TabsTrigger value="answers" className="gap-1.5"><MessageSquare className="h-3.5 w-3.5" /> App Questions</TabsTrigger>
          </TabsList>

          <TabsContent value="cover-letter">
            <div className="space-y-4">
              <div className="flex gap-3">
                <Select value={coverLetterStyle} onValueChange={setCoverLetterStyle}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="conversational">Conversational</SelectItem>
                    <SelectItem value="concise">Concise</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="gradient" className="gap-2" loading={coverLetterMutation.isPending}
                  disabled={!selectedJobId} onClick={() => coverLetterMutation.mutate()}>
                  <Sparkles className="h-4 w-4" /> Generate Cover Letter
                </Button>
              </div>

              {coverLetter && (
                <Card className="animate-fade-in">
                  <CardContent className="p-4">
                    <p className="text-xs font-semibold text-muted-foreground mb-1">SUBJECT</p>
                    <p className="font-medium mb-3">{coverLetter.subject_line}</p>
                    <p className="text-xs font-semibold text-muted-foreground mb-1">COVER LETTER</p>
                    <Textarea rows={12} value={coverLetter.cover_letter} className="text-sm font-mono" readOnly />
                    <div className="flex gap-2 mt-3">
                      <Button size="sm" variant="outline" onClick={() => navigator.clipboard.writeText(coverLetter.cover_letter).then(() => toast.success("Copied!"))}>Copy</Button>
                      <Button size="sm" variant="outline" onClick={() => coverLetterMutation.mutate()} loading={coverLetterMutation.isPending}>Regenerate</Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="resume">
            <div className="space-y-4">
              <Button variant="gradient" className="gap-2" loading={resumeMutation.isPending}
                disabled={!selectedJobId} onClick={() => resumeMutation.mutate()}>
                <Sparkles className="h-4 w-4" /> Customize Resume for This Job
              </Button>

              {customizedResume && (
                <Card className="animate-fade-in">
                  <CardContent className="p-4 space-y-4">
                    {customizedResume.optimized_summary && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">OPTIMIZED SUMMARY</p>
                        <p className="text-sm bg-muted/40 p-3 rounded">{customizedResume.optimized_summary}</p>
                      </div>
                    )}
                    {customizedResume.keywords_incorporated?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-2">KEYWORDS INCORPORATED</p>
                        <div className="flex flex-wrap gap-1.5">
                          {customizedResume.keywords_incorporated.map((k: string) => (
                            <Badge key={k} variant="success" className="text-xs">{k}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {customizedResume.changes_made?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-2">CHANGES MADE</p>
                        <ul className="space-y-1">
                          {customizedResume.changes_made.map((c: string, i: number) => (
                            <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                              <CheckCircle className="h-3 w-3 text-green-500 mt-0.5" /> {c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="answers">
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Paste application questions (one per line)</p>
                <Textarea rows={6} value={appQuestions}
                  onChange={e => setAppQuestions(e.target.value)}
                  placeholder={"Why do you want to work here?\nWhat is your greatest achievement?\nDescribe a challenging project..."}
                  className="font-mono text-sm"
                />
              </div>
              <Button variant="gradient" className="gap-2" loading={answersMutation.isPending}
                disabled={!selectedJobId || !appQuestions.trim()} onClick={() => answersMutation.mutate()}>
                <Bot className="h-4 w-4" /> Generate Answers
              </Button>

              {appAnswers.length > 0 && (
                <div className="space-y-3 animate-fade-in">
                  {appAnswers.map((item: any, i: number) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <p className="text-sm font-semibold mb-2 text-primary">Q: {item.question}</p>
                        <p className="text-sm text-muted-foreground leading-relaxed">{item.answer}</p>
                        <p className="text-xs text-muted-foreground/60 mt-2">{item.word_count} words</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
