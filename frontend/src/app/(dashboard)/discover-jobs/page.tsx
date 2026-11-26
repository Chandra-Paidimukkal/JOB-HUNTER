"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Search, MapPin, Building2, Clock, DollarSign,
  Bookmark, BookmarkCheck, Zap, ExternalLink, RefreshCw,
  Briefcase, Globe, Wifi, Loader2, Sparkles, ChevronDown,
  CheckCircle, TrendingUp, Star
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

const SOURCE_COLORS: Record<string, string> = {
  "LinkedIn": "bg-blue-100 text-blue-800",
  "Indeed": "bg-purple-100 text-purple-800",
  "Glassdoor": "bg-green-100 text-green-800",
  "Naukri": "bg-orange-100 text-orange-800",
  "Greenhouse": "bg-teal-100 text-teal-800",
  "Lever": "bg-pink-100 text-pink-800",
  "Wellfound": "bg-indigo-100 text-indigo-800",
  "WeWorkRemotely": "bg-cyan-100 text-cyan-800",
  "Remotive": "bg-violet-100 text-violet-800",
  "ZipRecruiter": "bg-yellow-100 text-yellow-800",
  "Company Careers": "bg-emerald-100 text-emerald-800",
};

const ALL_SOURCES = [
  "LinkedIn", "Indeed", "Glassdoor", "Google Jobs", "ZipRecruiter",
  "Naukri", "Greenhouse", "Lever", "Wellfound", "WeWorkRemotely",
  "Remotive", "Adzuna", "Company Careers"
];

const SORT_OPTIONS = [
  { value: "-posted_at", label: "Latest First" },
  { value: "-created_at", label: "Recently Added" },
  { value: "-salary_max", label: "Highest Salary" },
  { value: "title", label: "Job Title A-Z" },
  { value: "company", label: "Company A-Z" },
];

export default function DiscoverJobsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [workMode, setWorkMode] = useState("");
  const [source, setSource] = useState("");
  const [sort, setSort] = useState("-posted_at");
  const [page, setPage] = useState(1);
  const [savedJobs, setSavedJobs] = useState<Set<string>>(new Set());
  const [companyUrl, setCompanyUrl] = useState("");
  const [showCompanyCrawl, setShowCompanyCrawl] = useState(false);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["jobs", { search, location, employmentType, workMode, source, sort, page }],
    queryFn: () => jobsApi.list({
      search, location, employment_type: employmentType,
      work_mode: workMode, source: source || undefined,
      sort, page, per_page: 20,
    }).then(r => r.data),
    placeholderData: (prev) => prev,
  });

  // Global multi-source discovery
  const discoverMutation = useMutation({
    mutationFn: () => jobsApi.triggerDiscovery(),
    onSuccess: (res) => {
      toast.success("🌐 Global search started! Scanning LinkedIn, Indeed, Glassdoor, Naukri, Greenhouse, Lever, and more...");
      // Refresh every 8s for up to 60s
      let count = 0;
      const interval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ["jobs"] });
        count++;
        if (count >= 8) clearInterval(interval);
      }, 8000);
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  // Company career page crawl
  const crawlMutation = useMutation({
    mutationFn: (url: string) => {
      const parsed = new URL(url.startsWith("http") ? url : `https://${url}`);
      const companyName = parsed.hostname.replace("www.", "").split(".")[0];
      return jobsApi.list({ source: "Company Careers", per_page: 1 }).then(() =>
        fetch(`/api/v1/jobs/discover/company/${encodeURIComponent(companyName)}?website=${encodeURIComponent(url)}`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${document.cookie.match(/access_token=([^;]+)/)?.[1] || ""}` },
        }).then(r => r.json())
      );
    },
    onSuccess: (data: any) => {
      toast.success(`Found ${data.jobs_found || 0} jobs from ${data.company || "company"} career page!`);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setCompanyUrl("");
      setShowCompanyCrawl(false);
    },
    onError: (err) => toast.error(extractApiError(err)),
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

  const jobs: Job[] = data?.items || [];
  const total = data?.total || 0;

  return (
    <DashboardLayout
      title="Discover Jobs"
      subtitle="Real jobs from LinkedIn, Indeed, Glassdoor, Naukri, company career pages, and more"
    >
      {/* Main search bar */}
      <Card className="mb-4 border-primary/20">
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Job title, skills, keywords... (e.g. Python Developer, React Engineer)"
                className="pl-10 h-11"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
            <div className="relative w-full md:w-64">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Location, Country, City or Remote"
                className="pl-10 h-11"
                value={location}
                onChange={e => { setLocation(e.target.value); setPage(1); }}
              />
            </div>
            <Button
              variant="gradient"
              size="lg"
              className="gap-2 h-11 px-6"
              loading={discoverMutation.isPending}
              onClick={() => discoverMutation.mutate()}
            >
              <Globe className="h-4 w-4" />
              {discoverMutation.isPending ? "Searching..." : "Global Search"}
            </Button>
          </div>

          {/* Source badges */}
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-xs text-muted-foreground font-medium">Sources:</span>
            {ALL_SOURCES.map(s => (
              <button
                key={s}
                onClick={() => { setSource(source === s ? "" : s); setPage(1); }}
                className={cn(
                  "text-[10px] px-2 py-0.5 rounded-full border transition-colors font-medium",
                  source === s
                    ? (SOURCE_COLORS[s] || "bg-primary text-primary-foreground") + " border-transparent"
                    : "border-border hover:border-primary/50"
                )}
              >
                {s}
              </button>
            ))}
            {source && (
              <button onClick={() => setSource("")} className="text-[10px] text-muted-foreground hover:text-primary ml-1">
                ✕ Clear
              </button>
            )}
          </div>

          {/* Filters row */}
          <div className="flex flex-wrap gap-2 items-center">
            <Select value={employmentType} onValueChange={v => { setEmploymentType(v === "all" ? "" : v); setPage(1); }}>
              <SelectTrigger className="w-32 h-8 text-xs">
                <SelectValue placeholder="Job Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="Full-time">Full-time</SelectItem>
                <SelectItem value="Part-time">Part-time</SelectItem>
                <SelectItem value="Contract">Contract</SelectItem>
                <SelectItem value="Internship">Internship</SelectItem>
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

            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="w-40 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs gap-1.5"
              onClick={() => setShowCompanyCrawl(!showCompanyCrawl)}
            >
              <Building2 className="h-3.5 w-3.5" />
              Crawl Company Page
            </Button>

            <div className="ml-auto text-xs text-muted-foreground flex items-center gap-1.5">
              {isFetching && <Loader2 className="h-3 w-3 animate-spin" />}
              <span className="font-medium">{total.toLocaleString()}</span> jobs found
            </div>
          </div>

          {/* Company crawl panel */}
          {showCompanyCrawl && (
            <div className="flex gap-2 p-3 bg-muted/40 rounded-lg border border-border animate-fade-in">
              <div className="relative flex-1">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Enter company website (e.g. https://microsoft.com)"
                  className="pl-10 h-9 text-sm"
                  value={companyUrl}
                  onChange={e => setCompanyUrl(e.target.value)}
                />
              </div>
              <Button
                size="sm"
                variant="gradient"
                className="gap-1.5"
                loading={crawlMutation.isPending}
                disabled={!companyUrl.trim()}
                onClick={() => crawlMutation.mutate(companyUrl)}
              >
                <Search className="h-3.5 w-3.5" /> Crawl Jobs
              </Button>
              <p className="text-xs text-muted-foreground self-center hidden lg:block">
                Fetches jobs directly from their career page
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Discovery status banner */}
      {discoverMutation.isPending && (
        <div className="mb-4 p-3 bg-primary/5 border border-primary/20 rounded-lg flex items-center gap-3 animate-fade-in">
          <Loader2 className="h-4 w-4 animate-spin text-primary shrink-0" />
          <div>
            <p className="text-sm font-medium">Searching globally...</p>
            <p className="text-xs text-muted-foreground">
              Scanning LinkedIn, Indeed, Glassdoor, Google Jobs, Naukri, Greenhouse, Lever, Wellfound, WeWorkRemotely, Remotive and more
            </p>
          </div>
        </div>
      )}

      {/* Job listing */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
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
          <div className="w-16 h-16 rounded-full gradient-brand flex items-center justify-center mb-4">
            <Globe className="h-8 w-8 text-white" />
          </div>
          <h3 className="text-xl font-semibold">Start your global job search</h3>
          <p className="text-muted-foreground text-sm mt-2 max-w-md">
            Click <strong>Global Search</strong> to fetch real jobs from LinkedIn, Indeed, Glassdoor,
            Naukri, Greenhouse, Lever, Wellfound, and more — all at once.
          </p>
          <Button
            className="mt-6 gap-2"
            variant="gradient"
            size="lg"
            onClick={() => discoverMutation.mutate()}
            loading={discoverMutation.isPending}
          >
            <Globe className="h-4 w-4" /> Launch Global Search
          </Button>
          <p className="text-xs text-muted-foreground mt-3">
            First run takes ~30 seconds. Results appear automatically.
          </p>
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

          {total > 20 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>
                ← Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {Math.ceil(total / 20)}
              </span>
              <Button variant="outline" size="sm" disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(p => p + 1)}>
                Next →
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

  const sourceColor = SOURCE_COLORS[job.source] || SOURCE_COLORS[job.source?.split("/")?.[1]] || "bg-gray-100 text-gray-700";

  return (
    <Card className="group hover:shadow-md transition-all hover:border-primary/30 flex flex-col">
      <CardContent className="p-5 flex-1">
        <div className="flex items-start gap-3">
          {/* Logo */}
          <div className="w-12 h-12 rounded-xl bg-muted border border-border flex items-center justify-center shrink-0 overflow-hidden">
            {job.company_logo ? (
              <img
                src={job.company_logo}
                alt={job.company}
                className="w-full h-full object-contain p-1"
                onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
              />
            ) : (
              <span className="text-sm font-bold text-muted-foreground">
                {job.company.substring(0, 2).toUpperCase()}
              </span>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-semibold text-sm leading-tight group-hover:text-primary transition-colors line-clamp-2">
                  {job.title}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5 font-medium">{job.company}</p>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 -mt-0.5" onClick={onSave}>
                {isSaved
                  ? <BookmarkCheck className="h-4 w-4 text-primary" />
                  : <Bookmark className="h-4 w-4" />}
              </Button>
            </div>

            {/* Meta */}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs text-muted-foreground">
              {job.location && (
                <span className="flex items-center gap-1 max-w-[140px] truncate">
                  <MapPin className="h-3 w-3 shrink-0" /> {job.location}
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

            {/* Tags */}
            <div className="flex flex-wrap gap-1 mt-2">
              {job.is_remote && <Badge variant="success" className="text-[10px] px-1.5 py-0 h-4">Remote</Badge>}
              {job.is_hybrid && <Badge variant="info" className="text-[10px] px-1.5 py-0 h-4">Hybrid</Badge>}
              {job.skills_required?.slice(0, 3).map(s => (
                <Badge key={s} variant="secondary" className="text-[10px] px-1.5 py-0 h-4">{s}</Badge>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
          <div className="flex items-center gap-2">
            <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-medium", sourceColor)}>
              {job.source}
            </span>
            {postedAgo && (
              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />{postedAgo}
              </span>
            )}
          </div>
          <div className="flex gap-1">
            <Button size="sm" variant="outline" className="h-7 text-xs gap-1" asChild>
              <a href={`/ai-matching?job=${job.id}`}>
                <Zap className="h-3 w-3" /> Match
              </a>
            </Button>
            <Button size="sm" variant="gradient" className="h-7 text-xs gap-1" asChild>
              <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3" /> Apply
              </a>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
