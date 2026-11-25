"use client";

import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { MessageSquare, Sparkles, ChevronDown, ChevronRight, CheckCircle, Star } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { aiApi, jobsApi, extractApiError } from "@/services/api";
import { cn } from "@/utils/cn";

export default function InterviewPrepPage() {
  const [selectedJobId, setSelectedJobId] = useState("");
  const [prepData, setPrepData] = useState<any>(null);
  const [expandedQ, setExpandedQ] = useState<number | null>(null);
  const [userAnswer, setUserAnswer] = useState("");
  const [feedback, setFeedback] = useState<any>(null);
  const [evaluatingIdx, setEvaluatingIdx] = useState<number | null>(null);

  const { data: jobsData } = useQuery({
    queryKey: ["jobs-short"],
    queryFn: () => jobsApi.list({ per_page: 50 }).then(r => r.data),
  });

  const generateMutation = useMutation({
    mutationFn: () => aiApi.interviewPrep({ job_id: selectedJobId }),
    onSuccess: (res) => {
      setPrepData(res.data);
      toast.success("Interview prep generated!");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const evaluateMutation = useMutation({
    mutationFn: ({ question, answer, context }: any) =>
      aiApi.analyzeInterviewAnswer({ question, answer, job_context: context }),
    onSuccess: (res) => {
      setFeedback(res.data);
      toast.success("Answer evaluated!");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const jobs = jobsData?.items || [];

  const renderQuestions = (questions: any[], category: string) => (
    <div className="space-y-3">
      {questions?.map((q: any, i: number) => (
        <div key={i} className="border border-border rounded-lg overflow-hidden">
          <button
            className="w-full text-left p-4 flex items-center justify-between hover:bg-muted/30 transition-colors"
            onClick={() => setExpandedQ(expandedQ === i ? null : i)}
          >
            <div className="flex items-center gap-3">
              <span className={cn("px-2 py-0.5 rounded text-xs font-medium",
                q.difficulty === "hard" ? "bg-red-100 text-red-700" :
                q.difficulty === "medium" ? "bg-yellow-100 text-yellow-700" :
                "bg-green-100 text-green-700"
              )}>
                {q.difficulty || "medium"}
              </span>
              <span className="font-medium text-sm">{q.question}</span>
            </div>
            {expandedQ === i ? <ChevronDown className="h-4 w-4 shrink-0" /> : <ChevronRight className="h-4 w-4 shrink-0" />}
          </button>

          {expandedQ === i && (
            <div className="p-4 border-t border-border bg-muted/20 space-y-3">
              {q.suggested_answer && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1">Suggested Answer</p>
                  <p className="text-sm leading-relaxed">{q.suggested_answer}</p>
                </div>
              )}
              {q.star_answer && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground">STAR Framework</p>
                  {Object.entries(q.star_answer).map(([key, val]) => (
                    <div key={key}>
                      <span className="text-xs font-bold uppercase text-primary">{key}: </span>
                      <span className="text-xs text-muted-foreground">{val as string}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Practice */}
              <div className="border-t border-border pt-3">
                <p className="text-xs font-semibold mb-2">Practice Your Answer</p>
                <Textarea
                  rows={3}
                  placeholder="Type your answer here for AI feedback..."
                  value={userAnswer}
                  onChange={e => setUserAnswer(e.target.value)}
                  className="text-sm"
                />
                <Button
                  size="sm" className="mt-2 gap-1.5"
                  variant="outline"
                  loading={evaluateMutation.isPending && evaluatingIdx === i}
                  onClick={() => {
                    setEvaluatingIdx(i);
                    setFeedback(null);
                    evaluateMutation.mutate({
                      question: q.question,
                      answer: userAnswer,
                      context: `Job: ${jobs.find((j: any) => j.id === selectedJobId)?.title}`,
                    });
                  }}
                  disabled={!userAnswer.trim()}
                >
                  <Sparkles className="h-3.5 w-3.5" /> Get AI Feedback
                </Button>

                {feedback && evaluatingIdx === i && (
                  <div className="mt-3 p-3 bg-primary/5 rounded-lg border border-primary/20 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold">Score:</span>
                      {Array.from({ length: 10 }).map((_, idx) => (
                        <Star key={idx} className={cn("h-3.5 w-3.5",
                          idx < (feedback.score || 0) ? "text-yellow-500 fill-yellow-500" : "text-muted"
                        )} />
                      ))}
                      <span className="text-sm font-bold">{feedback.score}/10</span>
                    </div>
                    {feedback.better_answer && (
                      <div>
                        <p className="text-xs font-semibold text-green-600 mb-1">Improved Answer</p>
                        <p className="text-xs text-muted-foreground">{feedback.better_answer}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  return (
    <DashboardLayout
      title="Interview Preparation"
      subtitle="AI-generated questions and suggested answers tailored to each job"
    >
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <Select value={selectedJobId} onValueChange={setSelectedJobId}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select a job for interview prep..." />
              </SelectTrigger>
              <SelectContent>
                {jobs.map((j: any) => (
                  <SelectItem key={j.id} value={j.id}>
                    {j.title} — {j.company}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="gradient"
              className="gap-2"
              loading={generateMutation.isPending}
              disabled={!selectedJobId}
              onClick={() => generateMutation.mutate()}
            >
              <Sparkles className="h-4 w-4" /> Generate Prep
            </Button>
          </div>
        </CardContent>
      </Card>

      {!prepData ? (
        <div className="flex flex-col items-center py-20 text-center">
          <MessageSquare className="h-12 w-12 text-muted-foreground/30 mb-4" />
          <h3 className="text-lg font-semibold">Select a job to prepare for</h3>
          <p className="text-muted-foreground text-sm mt-2 max-w-sm">
            AI will generate technical, behavioral, and company-specific questions based on the job description.
          </p>
        </div>
      ) : (
        <div className="animate-fade-in">
          <Tabs defaultValue="technical">
            <TabsList className="mb-4">
              <TabsTrigger value="technical">Technical</TabsTrigger>
              <TabsTrigger value="behavioral">Behavioral</TabsTrigger>
              <TabsTrigger value="hr">HR Questions</TabsTrigger>
              <TabsTrigger value="company">Company Specific</TabsTrigger>
            </TabsList>

            <TabsContent value="technical">
              {renderQuestions(prepData.technical_questions || [], "technical")}
            </TabsContent>
            <TabsContent value="behavioral">
              {renderQuestions(prepData.behavioral_questions || [], "behavioral")}
            </TabsContent>
            <TabsContent value="hr">
              {renderQuestions(prepData.hr_questions || [], "hr")}
            </TabsContent>
            <TabsContent value="company">
              {renderQuestions(prepData.company_specific_questions || [], "company")}
              {prepData.questions_to_ask_interviewer?.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold text-sm mb-3">Questions You Should Ask the Interviewer</h3>
                  <div className="space-y-2">
                    {prepData.questions_to_ask_interviewer.map((q: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 p-3 bg-muted/40 rounded-lg">
                        <CheckCircle className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm">{q}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      )}
    </DashboardLayout>
  );
}
