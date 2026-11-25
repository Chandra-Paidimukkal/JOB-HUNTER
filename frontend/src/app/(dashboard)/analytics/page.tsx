"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import {
  Briefcase, Mail, MessageSquare, TrendingUp, Target, Award,
  Search, Zap, Users, ChevronUp
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { analyticsApi } from "@/services/api";
import { cn } from "@/utils/cn";

const PIE_COLORS = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4", "#84cc16"];
const APP_STATUS_COLORS: Record<string, string> = {
  applied: "#3b82f6",
  interview_scheduled: "#8b5cf6",
  offer_received: "#10b981",
  rejected: "#ef4444",
  under_review: "#f59e0b",
  saved: "#6b7280",
  withdrawn: "#9ca3af",
};

export default function AnalyticsPage() {
  const { data: overview, isLoading: ovLoading } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsApi.overview().then(r => r.data),
  });

  const { data: appAnalytics } = useQuery({
    queryKey: ["analytics-applications"],
    queryFn: () => analyticsApi.applications().then(r => r.data),
  });

  const { data: outreachAnalytics } = useQuery({
    queryKey: ["analytics-outreach"],
    queryFn: () => analyticsApi.outreach().then(r => r.data),
  });

  const { data: matchAnalytics } = useQuery({
    queryKey: ["analytics-matches"],
    queryFn: () => analyticsApi.jobMatches().then(r => r.data),
  });

  const stats = overview || {};

  const topStats = [
    { label: "Jobs Discovered", value: stats.total_jobs_discovered ?? 0, icon: Search, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-950/30", change: "+12%" },
    { label: "Applications Sent", value: stats.applications_submitted ?? 0, icon: Briefcase, color: "text-green-500", bg: "bg-green-50 dark:bg-green-950/30", change: "+5%" },
    { label: "Outreach Emails", value: stats.outreach_sent ?? 0, icon: Mail, color: "text-orange-500", bg: "bg-orange-50 dark:bg-orange-950/30", change: "+8%" },
    { label: "Interviews", value: stats.interviews_scheduled ?? 0, icon: MessageSquare, color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-950/30", change: "+2%" },
    { label: "Responses", value: stats.recruiter_responses ?? 0, icon: Users, color: "text-teal-500", bg: "bg-teal-50 dark:bg-teal-950/30", change: "+3%" },
    { label: "Offers", value: stats.offers_received ?? 0, icon: Award, color: "text-yellow-500", bg: "bg-yellow-50 dark:bg-yellow-950/30", change: "🎉" },
  ];

  // Funnel data
  const funnelData = [
    { name: "Discovered", value: stats.total_jobs_discovered ?? 0 },
    { name: "High Match", value: stats.high_match_jobs ?? 0 },
    { name: "Saved", value: stats.saved_jobs ?? 0 },
    { name: "Applied", value: stats.applications_submitted ?? 0 },
    { name: "Interviews", value: stats.interviews_scheduled ?? 0 },
    { name: "Offers", value: stats.offers_received ?? 0 },
  ];

  return (
    <DashboardLayout
      title="Analytics"
      subtitle="Track your job search performance and optimize your strategy"
    >
      {/* Top stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {topStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="p-4">
                <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center mb-2", stat.bg)}>
                  <Icon className={cn("h-4 w-4", stat.color)} />
                </div>
                <p className="text-2xl font-bold">{stat.value.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-xs text-green-500 font-medium mt-0.5">{stat.change}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Application funnel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Application Funnel</CardTitle>
            <CardDescription>Job search pipeline from discovery to offer</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={funnelData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={70} />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                  {funnelData.map((_, i) => (
                    <Cell key={i} fill={`hsl(${221 - i * 15}, 83%, ${53 + i * 5}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Applications over time */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Applications Over Time</CardTitle>
            <CardDescription>Last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            {appAnalytics?.daily_applications?.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={appAnalytics.daily_applications}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart message="No application data yet. Start applying to see trends." />
            )}
          </CardContent>
        </Card>

        {/* Application status breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Application Status Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {appAnalytics?.status_breakdown?.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={appAnalytics.status_breakdown}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ status, percent }) =>
                      `${status?.replace(/_/g, " ")} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {appAnalytics.status_breakdown.map((entry: any, i: number) => (
                      <Cell
                        key={i}
                        fill={APP_STATUS_COLORS[entry.status] || PIE_COLORS[i % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart message="Apply to jobs to see status distribution." />
            )}
          </CardContent>
        </Card>

        {/* Job match distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Job Match Distribution</CardTitle>
            <CardDescription>
              Average score: {matchAnalytics?.average_match_score ?? 0}%
            </CardDescription>
          </CardHeader>
          <CardContent>
            {matchAnalytics?.by_category?.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={matchAnalytics.by_category}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                    {matchAnalytics.by_category.map((entry: any, i: number) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart message="Run AI matching on jobs to see distribution." />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Outreach stats + top companies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outreach */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Outreach Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center mb-4">
              <div>
                <p className="text-2xl font-bold">{outreachAnalytics?.emails_sent ?? 0}</p>
                <p className="text-xs text-muted-foreground">Emails Sent</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{outreachAnalytics?.responses_received ?? 0}</p>
                <p className="text-xs text-muted-foreground">Responses</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-500">
                  {outreachAnalytics?.response_rate ?? 0}%
                </p>
                <p className="text-xs text-muted-foreground">Response Rate</p>
              </div>
            </div>
            {outreachAnalytics?.by_email_type?.length > 0 && (
              <div className="space-y-2">
                {outreachAnalytics.by_email_type.slice(0, 5).map((item: any) => (
                  <div key={item.type} className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground w-32 capitalize truncate">
                      {item.type?.replace(/_/g, " ")}
                    </span>
                    <div className="flex-1 bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{
                          width: `${Math.min(100, (item.count / (outreachAnalytics?.total_contacts || 1)) * 100)}%`
                        }}
                      />
                    </div>
                    <span className="text-xs font-medium w-6 text-right">{item.count}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top companies */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Top Companies Applied To</CardTitle>
          </CardHeader>
          <CardContent>
            {appAnalytics?.top_companies?.length > 0 ? (
              <div className="space-y-2">
                {appAnalytics.top_companies.map((item: any, i: number) => (
                  <div key={item.company} className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                    <span className="flex-1 text-sm font-medium truncate">{item.company}</span>
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                      {item.count} app{item.count !== 1 ? "s" : ""}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyChart message="Apply to jobs to see your top companies." />
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-center">
      <TrendingUp className="h-8 w-8 text-muted-foreground/30 mb-2" />
      <p className="text-sm text-muted-foreground max-w-xs">{message}</p>
    </div>
  );
}
