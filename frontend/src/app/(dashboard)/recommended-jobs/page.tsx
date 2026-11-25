"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Star, Zap, MapPin, Building2, DollarSign, ExternalLink, Bookmark, BookmarkCheck, Briefcase } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { jobsApi, extractApiError } from "@/services/api";
import { cn } from "@/utils/cn";

const CATEGORY_COLORS: Record<string, string> = {
  excellent: "bg-emerald-100 text-emerald-800",
  strong: "bg-blue-100 text-blue-800",
  good: "bg-indigo-100 text-indigo-800",
  moderate: "bg-orange-100 text-orange-800",
  low: "bg-gray-100 text-gray-700",
};

export default function RecommendedJobsPage() {
  const queryClient = useQueryClient();
  const [minScore, setMinScore] = useState("70");
  const [savedJobs, setSavedJobs] = useState<Set<string>>(new Set());

  const { data, isLoading } = useQuery({
    queryKey: ["recommended-jobs", minScore],
    queryFn: () => jobsApi.getMatches({ min_score: parseFloat(minScore), per_page: 50 }).then(r => r.data),
  });

  const saveMutation = useMutation({
    mutationFn: (jobId: string) =>
      savedJobs.has(jobId) ? jobsApi.unsave(jobId) : jobsApi.save(jobId),
    onSuccess: (_, jobId) => {
      setSavedJobs(prev => { const n = new Set(prev); n.has(jobId) ? n.delete(jobId) : n.add(jobId); return n; });
      toast.success(savedJobs.has(jobId) ? "Removed from saved" : "Job saved!");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const matches = data?.items || [];

  return (
    <DashboardLayout
      title="Recommended Jobs"
      subtitle="Jobs ranked by AI compatibility with your profile"
    >
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm text-muted-foreground">Minimum match score:</span>
        <Select value={minScore} onValueChange={setMinScore}>
          <SelectTrigger className="w-32 h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {["50", "60", "70", "80", "90"].map(v => (
              <SelectItem key={v} value={v}>{v}%+</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-sm text-muted-foreground">{matches.length} jobs found</span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      ) : matches.length === 0 ? (
        <div className="flex flex-col items-center py-20 text-center">
          <Star className="h-12 w-12 text-muted-foreground/30 mb-4" />
          <h3 className="text-lg font-semibold">No recommendations yet</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-sm">
            Discover jobs and run AI matching. High-scoring jobs appear here.
          </p>
          <Button className="mt-4" variant="gradient" asChild>
            <a href="/ai-matching">Run AI Matching</a>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matches.map((match: any) => (
            <Card key={match.id} className="hover:shadow-md transition-all hover:border-primary/30">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm">{match.job?.title}</h3>
                      <p className="text-xs text-muted-foreground">{match.job?.company}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={cn("text-xl font-bold",
                      match.match_score >= 80 ? "text-green-600" :
                      match.match_score >= 60 ? "text-yellow-600" : "text-muted-foreground"
                    )}>
                      {match.match_score?.toFixed(0)}%
                    </span>
                    <span className={cn("block text-[10px] px-1.5 py-0.5 rounded-full mt-0.5", CATEGORY_COLORS[match.match_category] || "")}>
                      {match.match_category}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-x-3 gap-y-1 mt-3 text-xs text-muted-foreground">
                  {match.job?.location && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{match.job.location}</span>}
                  {match.job?.employment_type && <span className="flex items-center gap-1"><Briefcase className="h-3 w-3" />{match.job.employment_type}</span>}
                  {match.job?.salary_max && <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />Up to ${(match.job.salary_max / 1000).toFixed(0)}k</span>}
                </div>

                <div className="flex flex-wrap gap-1 mt-2">
                  {match.matching_skills?.slice(0, 4).map((s: string) => (
                    <span key={s} className="text-[10px] px-1.5 py-0.5 bg-green-50 text-green-700 dark:bg-green-950/50 dark:text-green-300 rounded">{s}</span>
                  ))}
                </div>

                <div className="flex gap-2 mt-3 pt-3 border-t border-border">
                  <Button size="sm" variant="gradient" className="flex-1 gap-1" asChild>
                    <a href={match.job?.apply_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-3.5 w-3.5" /> Apply
                    </a>
                  </Button>
                  <Button size="sm" variant="outline" className="gap-1" onClick={() => saveMutation.mutate(match.job?.id)}>
                    {savedJobs.has(match.job?.id) ? <BookmarkCheck className="h-3.5 w-3.5 text-primary" /> : <Bookmark className="h-3.5 w-3.5" />}
                  </Button>
                  <Button size="sm" variant="outline" className="gap-1" asChild>
                    <a href="/outreach-studio"><Zap className="h-3.5 w-3.5" /> Outreach</a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
