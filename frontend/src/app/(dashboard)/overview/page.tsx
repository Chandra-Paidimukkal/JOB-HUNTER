"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase, FileText, Mail, TrendingUp, Zap, ArrowRight,
  Search, Star, Bell, BarChart3, Clock, CheckCircle2,
  Target, MessageSquare, Building2, AlertCircle, Sparkles
} from "lucide-react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { analyticsApi, jobsApi, applicationsApi, notificationsApi } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/utils/cn";

const STAT_CARDS = [
  { key: "total_jobs_discovered", label: "Jobs Discovered", icon: Search, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-950/30" },
  { key: "high_match_jobs", label: "High Match Jobs", icon: Zap, color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-950/30" },
  { key: "applications_submitted", label: "Applications Sent", icon: Briefcase, color: "text-green-500", bg: "bg-green-50 dark:bg-green-950/30" },
  { key: "outreach_sent", label: "Outreach Emails", icon: Mail, color: "text-orange-500", bg: "bg-orange-50 dark:bg-orange-950/30" },
  { key: "interviews_scheduled", label: "Interviews", icon: MessageSquare, color: "text-pink-500", bg: "bg-pink-50 dark:bg-pink-950/30" },
  { key: "recruiter_responses", label: "Responses", icon: CheckCircle2, color: "text-teal-500", bg: "bg-teal-50 dark:bg-teal-950/30" },
];

const QUICK_ACTIONS = [
  { label: "Search New Jobs", href: "/discover-jobs", icon: Search, color: "gradient-brand text-white" },
  { label: "AI Match Jobs", href: "/ai-matching", icon: Zap, color: "bg-purple-600 hover:bg-purple-700 text-white" },
  { label: "Upload Resume", href: "/resume-manager", icon: FileText, color: "bg-green-600 hover:bg-green-700 text-white" },
  { label: "Generate Outreach", href: "/outreach-studio", icon: Sparkles, color: "bg-orange-600 hover:bg-orange-700 text-white" },
  { label: "Track Applications", href: "/applications", icon: Briefcase, color: "bg-blue-600 hover:bg-blue-700 text-white" },
  { label: "Interview Prep", href: "/interview-prep", icon: MessageSquare, color: "bg-pink-600 hover:bg-pink-700 text-white" },
];

const STATUS_COLORS: Record<string, string> = {
  applied: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  interview_scheduled: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100",
  offer_received: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  rejected: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
  under_review: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
  saved: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

export default function OverviewPage() {
  const { user } = useAuth();

  const { data: analyticsData } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsApi.overview().then(r => r.data),
  });

  const { data: recentApplications } = useQuery({
    queryKey: ["recent-applications"],
    queryFn: () => applicationsApi.list({ limit: 5, sort: "-created_at" }).then(r => r.data?.items || []),
  });

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list().then(r => r.data?.items || []),
  });

  const stats = analyticsData || {};
  const greeting = new Date().getHours() < 12 ? "Good morning" : new Date().getHours() < 17 ? "Good afternoon" : "Good evening";

  const profileStrength = (() => {
    let score = 0;
    if (user?.full_name) score += 20;
    if (stats.total_jobs_discovered > 0) score += 20;
    if (stats.applications_submitted > 0) score += 20;
    if (stats.outreach_sent > 0) score += 20;
    if (stats.emails_generated > 0) score += 20;
    return score;
  })();

  return (
    <DashboardLayout
      title={`${greeting}, ${user?.full_name?.split(" ")[0] || "there"} 👋`}
      subtitle="Here's your job search summary for today"
    >
      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {STAT_CARDS.map((card) => {
          const Icon = card.icon;
          const value = (stats as Record<string, number>)[card.key] ?? 0;
          return (
            <Card key={card.key} className="relative overflow-hidden">
              <CardContent className="p-4">
                <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center mb-3", card.bg)}>
                  <Icon className={cn("h-4 w-4", card.color)} />
                </div>
                <p className="text-2xl font-bold">{value.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{card.label}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick actions */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Quick Actions</CardTitle>
              <CardDescription>Jump directly into key workflows</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {QUICK_ACTIONS.map((action) => {
                  const Icon = action.icon;
                  return (
                    <Link key={action.href} href={action.href}>
                      <div className={cn(
                        "flex flex-col items-center gap-2 p-4 rounded-lg cursor-pointer transition-all hover:scale-105 hover:shadow-md",
                        action.color
                      )}>
                        <Icon className="h-6 w-6" />
                        <span className="text-xs font-medium text-center">{action.label}</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Recent applications */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Recent Applications</CardTitle>
                <CardDescription>Your latest job applications</CardDescription>
              </div>
              <Link href="/applications">
                <Button variant="ghost" size="sm" className="gap-1 text-xs">
                  View all <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {recentApplications?.length === 0 || !recentApplications ? (
                <div className="flex flex-col items-center py-8 text-center">
                  <Briefcase className="h-10 w-10 text-muted-foreground/40 mb-3" />
                  <p className="text-sm font-medium">No applications yet</p>
                  <p className="text-xs text-muted-foreground mt-1">Discover and apply to jobs to see them here</p>
                  <Link href="/discover-jobs" className="mt-3">
                    <Button size="sm" variant="outline">Discover Jobs</Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentApplications.map((app: any) => (
                    <div key={app.id} className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors">
                      <div className="w-8 h-8 rounded-md bg-muted flex items-center justify-center shrink-0">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{app.job?.title}</p>
                        <p className="text-xs text-muted-foreground truncate">{app.job?.company}</p>
                      </div>
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium shrink-0",
                        STATUS_COLORS[app.status] || STATUS_COLORS.saved)}>
                        {app.status?.replace(/_/g, " ")}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Profile strength */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Profile Strength</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Completion</span>
                <span className="font-semibold">{profileStrength}%</span>
              </div>
              <Progress value={profileStrength} className="h-2" />
              <div className="space-y-2 mt-3">
                {[
                  { label: "Profile filled", done: !!user?.full_name, href: "/profile" },
                  { label: "Resume uploaded", done: false, href: "/resume-manager" },
                  { label: "Job preferences set", done: false, href: "/profile" },
                  { label: "First application", done: stats.applications_submitted > 0, href: "/discover-jobs" },
                  { label: "Outreach sent", done: stats.outreach_sent > 0, href: "/outreach-studio" },
                ].map((item) => (
                  <Link key={item.label} href={item.href}>
                    <div className="flex items-center gap-2 text-xs py-1 hover:text-primary transition-colors">
                      <div className={cn("w-4 h-4 rounded-full flex items-center justify-center shrink-0",
                        item.done ? "bg-green-500" : "bg-muted border border-border")}>
                        {item.done && <CheckMark className="h-2.5 w-2.5 text-white" />}
                      </div>
                      <span className={item.done ? "line-through text-muted-foreground" : ""}>{item.label}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-base">Notifications</CardTitle>
              <Link href="/notifications">
                <Button variant="ghost" size="sm" className="gap-1 text-xs">
                  All <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {!notifications?.length ? (
                <div className="flex flex-col items-center py-6 text-center">
                  <Bell className="h-8 w-8 text-muted-foreground/40 mb-2" />
                  <p className="text-xs text-muted-foreground">No new notifications</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {notifications.slice(0, 4).map((notif: any) => (
                    <div key={notif.id} className={cn("p-3 rounded-lg text-xs border",
                      notif.is_read ? "border-border bg-transparent" : "border-primary/20 bg-primary/5")}>
                      <p className="font-medium">{notif.title}</p>
                      <p className="text-muted-foreground mt-0.5 line-clamp-2">{notif.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Tips */}
          <Card className="bg-gradient-to-br from-blue-950 to-blue-900 text-white border-0">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-blue-300" />
                <span className="text-sm font-semibold text-blue-100">AI Tip</span>
              </div>
              <p className="text-sm text-blue-100 leading-relaxed">
                Companies with active hiring in your area: upload your resume and let AI match you to the best opportunities automatically.
              </p>
              <Link href="/ai-matching" className="mt-3 block">
                <Button size="sm" className="bg-white/10 hover:bg-white/20 text-white border border-white/20 w-full">
                  Run AI Matching <Zap className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

function CheckMark({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
