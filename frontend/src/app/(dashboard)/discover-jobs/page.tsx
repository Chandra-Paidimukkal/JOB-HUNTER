"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Search, Filter, MapPin, Building2, Clock, DollarSign,
  Bookmark, BookmarkCheck, Zap, ExternalLink, RefreshCw,
  Briefcase, Globe, Wifi, SlidersHorizontal, ChevronDown,
  Star, TrendingUp, ArrowUpDown, Loader2
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { jobsApi, extractApiError } from "@/services/api";
import { Job } from "@/types";
import { cn } from "@/utils/cn";
import { formatDistanceToNow } from "date-fns";

const EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship"];
const SOURCES = ["All Sources", "LinkedIn", "Greenhouse", "Lever", "Ashby", "Wellfound"];
const SORT_OPTIONS = [
  { value: "-posted_at", label: "Latest First" },
  { value: "posted_at", label: "Oldest First" },
  { value: "-match_score", label: "Highest Match" },
  { value: "-salary_max", label: "Highest Salary" },
];

export default function DiscoverJobsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [workMode, setWorkMode] = useState("");
  const [source, setSource] = useState("All Sources");
  const [sort, setSort] = useState("-posted_at");
  const [page, setPage] = useState(1);
  const [savedJobs, setSavedJobs] = useState<Set<string>>(new Set());

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["jobs", { search, location, experience, employmentType, workMode, source, sort, page }],
    queryFn: () => jobsApi.list({
      search, location, experience, employment_type: employmentType,
      work_mode: workMode, source: source !== "All Sources" ? source : undefined,
      sort, page, per_page: 20
    }).then(r => r.data),
    placeholderData: (prev) => prev,
  });

  const discoverMutation = useMutation({
    mutationFn: () => jobsApi.triggerDiscovery(),
    onSuccess: () => {
      toast.success("Job discovery started! New opportunities will appear shortly.");
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["jobs"] }), 5000);
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const saveMutation = useMutation({
    mutationFn: (jobId: string) =>
      savedJobs.has(jobId) ? jobsApi.unsave(jobId) : jobsApi.save(jobId),
    onSuccess: (_, jobId) => {
      setSavedJobs(prev => {
        const next = new Set(prev);
        if (next.has(jobId)) next.delete(jobId); else next.add(jobId);
        return next;
      });
      toast.success(savedJobs.has(jobId) ? "Job removed from saved" : "Job saved!");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const jobs: Job[] = data?.items || [];
  const total = data?.total || 0;

  return (
    <DashboardLayout
      title="Discover Jobs"
      subtitle="Search and filter real opportunities from multiple sources"
    >
      {/* Search bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Job title, skills, or keywords..."
                className="pl-10"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
            <div className="relative w-full md:w-56">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Location or Remote"
                className="pl-10"
                value={location}
                onChange={e => { setLocation(e.target.value); setPage(1); }}
              />
            </div>
            <Button
              variant="gradient"
              className="gap-2"
              onClick={() => queryClient.invalidateQueries({ queryKey: ["jobs"] })}
            >
              <Search className="h-4 w-4" /> Search
            </Button>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => discoverMutation.mutate()}
              loading={discoverMutation.isPending}
            >
              <RefreshCw className={cn("h-4 w-4", discoverMutation.isPending && "animate-spin")} />
              Discover New
            </Button>
          </div>

          {/* Filters row */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Select value={employmentType} onValueChange={v => { setEmploymentType(v === "all" ? "" : v); setPage(1); }}>
              <SelectTrigger className="w-36 h-8 text-xs">
                <SelectValue placeholder="Job Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {EMPLOYMENT_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select value={workMode} onValueChange={v => { setWorkMode(v === "all" ? "" : v); setPage(1); }}>
              <SelectTrigger className="w-32 h-8 text-xs">
                <SelectValue placeholder="Work Mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modes</SelectItem>
                <SelectItem value="remote">Remote</SelectItem>
                <SelectItem value="hybrid">Hybrid</SelectItem>
                <SelectItem value="onsite">On-site</SelectItem>
              </SelectContent>
            </Select>

            <Select value={source} onValueChange={v => { setSource(v); setPage(1); }}>
              <SelectTrigger className="w-36 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="w-40 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>

            <div className="ml-auto text-sm text-muted-foreground flex items-center gap-1">
              {isFetching && <Loader2 className="h-3 w-3 animate-spin" />}
              {total > 0 && <span>{total.toLocaleString()} jobs found</span>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Job listing */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-5">
                <div className="flex gap-3">
                  <div className="w-12 h-12 bg-muted rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-muted rounded w-3/4" />
                    <div className="h-3 bg-muted rounded w-1/2" />
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="h-3 bg-muted rounded w-full" />
                  <div className="h-3 bg-muted rounded w-5/6" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="flex flex-col items-center py-20 text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <Search className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <h3 className="text-lg font-semibold">No jobs found</h3>
          <p className="text-muted-foreground text-sm mt-2 max-w-sm">
            Try adjusting your filters or click "Discover New" to fetch fresh opportunities.
          </p>
          <Button
            className="mt-4"
            variant="gradient"
            onClick={() => discoverMutation.mutate()}
            loading={discoverMutation.isPending}
          >
            <Zap className="h-4 w-4 mr-2" /> Discover Jobs Now
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                isSaved={savedJobs.has(job.id)}
                onSave={() => saveMutation.mutate(job.id)}
              />
            ))}
          </div>

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {Math.ceil(total / 20)}
              </span>
              <Button variant="outline" size="sm" disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(p => p + 1)}>
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  );
}

function JobCard({ job, isSaved, onSave }: { job: Job; isSaved: boolean; onSave: () => void }) {
  const postedAgo = job.posted_at
    ? formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })
    : null;

  return (
    <Card className="group hover:shadow-md transition-all hover:border-primary/30">
      <CardContent className="p-5">
        <div className="flex items-start gap-3">
          {/* Company logo */}
          <div className="w-11 h-11 rounded-lg bg-muted border border-border flex items-center justify-center shrink-0 overflow-hidden">
            {job.company_logo ? (
              <img src={job.company_logo} alt={job.company} className="w-full h-full object-contain p-1" />
            ) : (
              <Building2 className="h-5 w-5 text-muted-foreground" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-semibold text-sm leading-tight line-clamp-1 group-hover:text-primary transition-colors">
                  {job.title}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">{job.company}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0 -mt-0.5"
                onClick={onSave}
              >
                {isSaved ? (
                  <BookmarkCheck className="h-4 w-4 text-primary" />
                ) : (
                  <Bookmark className="h-4 w-4" />
                )}
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs text-muted-foreground">
              {job.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" /> {job.location}
                </span>
              )}
              {(job.salary_min || job.salary_max) && (
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  {job.salary_min && job.salary_max
                    ? `${(job.salary_min / 1000).toFixed(0)}k–${(job.salary_max / 1000).toFixed(0)}k`
                    : job.salary_max ? `Up to ${(job.salary_max / 1000).toFixed(0)}k`
                    : `From ${(job.salary_min! / 1000).toFixed(0)}k`}
                </span>
              )}
              {job.employment_type && (
                <span className="flex items-center gap-1">
                  <Briefcase className="h-3 w-3" /> {job.employment_type}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-1 mt-2">
              {job.is_remote && <Badge variant="success" className="text-[10px] px-1.5 py-0 h-4">Remote</Badge>}
              {job.is_hybrid && <Badge variant="info" className="text-[10px] px-1.5 py-0 h-4">Hybrid</Badge>}
              {job.skills_required?.slice(0, 3).map((s) => (
                <Badge key={s} variant="secondary" className="text-[10px] px-1.5 py-0 h-4">{s}</Badge>
              ))}
              {job.skills_required?.length > 3 && (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">+{job.skills_required.length - 3}</Badge>
              )}
            </div>

            <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{job.source}</span>
                {postedAgo && <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{postedAgo}</span>}
              </div>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" className="h-7 text-xs gap-1" asChild>
                  <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-3 w-3" /> Apply
                  </a>
                </Button>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1" asChild>
                  <a href={`/ai-matching?job=${job.id}`}>
                    <Zap className="h-3 w-3" /> Match
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
