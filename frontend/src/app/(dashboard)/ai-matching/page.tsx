"use client";

import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Zap, Building2, MapPin, Briefcase, DollarSign, ExternalLink,
  CheckCircle, XCircle, AlertCircle, Sparkles, RefreshCw, Filter
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { jobsApi, extractApiError } from "@/services/api";
import { JobMatch } from "@/types";
import { cn } from "@/utils/cn";

const CATEGORY_CONFIG = {
  excellent: { label: "Excellent Match", color: "bg-emerald-100 text-emerald-800", barColor: "bg-emerald-500", min: 90 },
  strong: { label: "Strong Match", color: "bg-blue-100 text-blue-800", barColor: "bg-blue-500", min: 80 },
  good: { label: "Good Match", color: "bg-indigo-100 text-indigo-800", barColor: "bg-indigo-500", min: 70 },
  moderate: { label: "Moderate Match", color: "bg-orange-100 text-orange-800", barColor: "bg-orange-500", min: 50 },
  low: { label: "Low Match", color: "bg-gray-100 text-gray-700", barColor: "bg-gray-400", min: 0 },
};

export default function AIMatchingPage() {
  const [selectedMatch, setSelectedMatch] = useState<JobMatch | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("all");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["job-matches"],
    queryFn: () => jobsApi.getMatches({ per_page: 50 }).then(r => r.data),
  });

  const matchMutation = useMutation({
    mutationFn: (jobId: string) => jobsApi.match(jobId),
    onSuccess: () => { toast.success("Job matched!"); refetch(); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const matches: JobMatch[] = data?.items || [];
  const filtered = categoryFilter === "all"
    ? matches
    : matches.filter(m => m.match_category === categoryFilter);

  return (
    <DashboardLayout
      title="AI Job Matching"
      subtitle="Groq AI evaluates every job against your profile and resume"
    >
      {/* Category filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategoryFilter("all")}
          className={cn("px-3 py-1.5 rounded-full text-xs font-medium border",
            categoryFilter === "all" ? "bg-primary text-primary-foreground border-primary" : "border-input hover:border-primary")}
        >
          All Matches ({matches.length})
        </button>
        {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => {
          const count = matches.filter(m => m.match_category === key).length;
          return (
            <button
              key={key}
              onClick={() => setCategoryFilter(key)}
              className={cn("px-3 py-1.5 rounded-full text-xs font-medium border capitalize",
                categoryFilter === key ? cfg.color + " border-transparent" : "border-input hover:border-primary")}
            >
              {cfg.label} ({count})
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Match list */}
        <div className="lg:col-span-2 space-y-3">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-muted animate-pulse rounded-lg" />
            ))
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-center border-2 border-dashed border-border rounded-xl">
              <Zap className="h-10 w-10 text-muted-foreground/30 mb-3" />
              <p className="font-medium">No matches yet</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                Go to Discover Jobs and click "Match" on any job to run AI analysis.
              </p>
            </div>
          ) : (
            filtered.map((match) => {
              const cfg = CATEGORY_CONFIG[match.match_category] || CATEGORY_CONFIG.low;
              return (
                <div
                  key={match.id}
                  onClick={() => setSelectedMatch(match)}
                  className={cn(
                    "p-4 rounded-lg border cursor-pointer transition-all hover:shadow-sm",
                    selectedMatch?.id === match.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm truncate">{match.job?.title}</p>
                      <p className="text-xs text-muted-foreground">{match.job?.company}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={cn("text-lg font-bold",
                        match.match_score >= 80 ? "text-green-600" :
                        match.match_score >= 60 ? "text-yellow-600" : "text-red-500"
                      )}>
                        {match.match_score.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-medium", cfg.color)}>
                        {cfg.label}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5">
                      <div
                        className={cn("h-1.5 rounded-full", cfg.barColor)}
                        style={{ width: `${match.match_score}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {match.matching_skills?.slice(0, 3).map(s => (
                      <span key={s} className="text-[10px] px-1.5 py-0.5 bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300 rounded">{s}</span>
                    ))}
                    {match.missing_skills?.slice(0, 2).map(s => (
                      <span key={s} className="text-[10px] px-1.5 py-0.5 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 rounded">-{s}</span>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Match detail */}
        <div className="lg:col-span-3">
          {!selectedMatch ? (
            <div className="flex flex-col items-center justify-center h-80 border-2 border-dashed border-border rounded-xl">
              <Sparkles className="h-12 w-12 text-muted-foreground/30 mb-3" />
              <p className="font-medium">Select a match to view full analysis</p>
            </div>
          ) : (
            <Card className="animate-fade-in">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">{selectedMatch.job?.title}</CardTitle>
                    <p className="text-sm text-muted-foreground">{selectedMatch.job?.company} · {selectedMatch.job?.location}</p>
                  </div>
                  <div className="text-right">
                    <span className={cn("text-3xl font-bold",
                      selectedMatch.match_score >= 80 ? "text-green-600" :
                      selectedMatch.match_score >= 60 ? "text-yellow-600" : "text-red-500"
                    )}>
                      {selectedMatch.match_score.toFixed(0)}%
                    </span>
                    <p className="text-xs text-muted-foreground">match score</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="breakdown">
                  <TabsList className="mb-4">
                    <TabsTrigger value="breakdown">Score Breakdown</TabsTrigger>
                    <TabsTrigger value="skills">Skills Analysis</TabsTrigger>
                    <TabsTrigger value="recommendation">AI Analysis</TabsTrigger>
                  </TabsList>

                  <TabsContent value="breakdown">
                    <div className="space-y-3">
                      {[
                        { label: "Skills Match", value: selectedMatch.skills_match, weight: "30%" },
                        { label: "Experience Match", value: selectedMatch.experience_match, weight: "25%" },
                        { label: "Responsibility Match", value: selectedMatch.responsibility_match, weight: "20%" },
                        { label: "Education Match", value: selectedMatch.education_match, weight: "10%" },
                        { label: "Industry Match", value: selectedMatch.industry_match, weight: "10%" },
                        { label: "Location Match", value: selectedMatch.location_match, weight: "5%" },
                      ].map(item => (
                        <div key={item.label}>
                          <div className="flex justify-between text-sm mb-1">
                            <span>{item.label} <span className="text-muted-foreground text-xs">({item.weight})</span></span>
                            <span className="font-semibold">{(item.value || 0).toFixed(0)}%</span>
                          </div>
                          <Progress value={item.value || 0} className="h-2" />
                        </div>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="skills">
                    <div className="space-y-4">
                      {selectedMatch.matching_skills?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
                            <CheckCircle className="h-4 w-4 text-green-500" /> Matching Skills
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {selectedMatch.matching_skills.map(s => (
                              <Badge key={s} variant="success">{s}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {selectedMatch.missing_skills?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
                            <XCircle className="h-4 w-4 text-red-500" /> Skills to Develop
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {selectedMatch.missing_skills.map(s => (
                              <Badge key={s} variant="destructive">{s}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {selectedMatch.concerns?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
                            <AlertCircle className="h-4 w-4 text-yellow-500" /> Considerations
                          </h4>
                          <ul className="space-y-1">
                            {selectedMatch.concerns.map((c, i) => (
                              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-yellow-500 mt-0.5">•</span> {c}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="recommendation">
                    <div className="space-y-4">
                      {selectedMatch.ai_recommendation && (
                        <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                          <p className="text-xs font-semibold text-primary mb-2 flex items-center gap-1.5">
                            <Sparkles className="h-3.5 w-3.5" /> AI Recommendation
                          </p>
                          <p className="text-sm leading-relaxed">{selectedMatch.ai_recommendation}</p>
                        </div>
                      )}
                      {selectedMatch.reasons_to_apply?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold mb-2">Reasons to Apply</h4>
                          <ul className="space-y-1">
                            {selectedMatch.reasons_to_apply.map((r, i) => (
                              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                <CheckCircle className="h-4 w-4 text-green-500 shrink-0 mt-0.5" /> {r}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>

                <div className="flex gap-2 mt-4 pt-4 border-t border-border">
                  {selectedMatch.job?.apply_url && (
                    <Button variant="gradient" size="sm" className="gap-1.5" asChild>
                      <a href={selectedMatch.job.apply_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-3.5 w-3.5" /> Apply Now
                      </a>
                    </Button>
                  )}
                  <Button variant="outline" size="sm" className="gap-1.5" asChild>
                    <a href="/outreach-studio">
                      <Sparkles className="h-3.5 w-3.5" /> Generate Outreach
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
