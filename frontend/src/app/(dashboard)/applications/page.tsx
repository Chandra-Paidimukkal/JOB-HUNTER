"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Briefcase, Building2, MapPin, Calendar, ExternalLink,
  MoreHorizontal, Edit, Trash2, ChevronDown, Filter, LayoutGrid, List,
  Plus, Clock, CheckCircle, XCircle, MessageSquare, TrendingUp
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { applicationsApi, extractApiError } from "@/services/api";
import { Application, ApplicationStatus } from "@/types";
import { cn } from "@/utils/cn";
import { formatDistanceToNow } from "date-fns";

const STATUS_CONFIG: Record<ApplicationStatus, { label: string; color: string; icon: any }> = {
  saved: { label: "Saved", color: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300", icon: Briefcase },
  recommended: { label: "Recommended", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100", icon: TrendingUp },
  ready_to_apply: { label: "Ready to Apply", color: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-100", icon: CheckCircle },
  applied: { label: "Applied", color: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-100", icon: Briefcase },
  under_review: { label: "Under Review", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100", icon: Clock },
  recruiter_contacted: { label: "Recruiter Contacted", color: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100", icon: MessageSquare },
  interview_scheduled: { label: "Interview Scheduled", color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100", icon: Calendar },
  interview_completed: { label: "Interview Done", color: "bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-100", icon: CheckCircle },
  assessment_pending: { label: "Assessment Pending", color: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100", icon: Clock },
  offer_received: { label: "Offer Received", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100", icon: CheckCircle },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100", icon: XCircle },
  withdrawn: { label: "Withdrawn", color: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300", icon: XCircle },
};

const KANBAN_COLUMNS: ApplicationStatus[] = [
  "saved", "applied", "under_review", "interview_scheduled", "offer_received", "rejected"
];

export default function ApplicationsPage() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<"table" | "kanban">("table");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["applications", statusFilter],
    queryFn: () => applicationsApi.list({ status: statusFilter || undefined }).then(r => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      applicationsApi.update(id, { status }),
    onSuccess: () => {
      toast.success("Application updated");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => applicationsApi.delete(id),
    onSuccess: () => {
      toast.success("Application removed");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const applications: Application[] = data?.items || [];
  const total = data?.total || 0;

  // Status counts for summary
  const statusCounts = applications.reduce((acc, app) => {
    acc[app.status] = (acc[app.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <DashboardLayout
      title="My Applications"
      subtitle={`${total} total applications tracked`}
    >
      {/* Summary row */}
      <div className="flex flex-wrap gap-2 mb-6">
        {(["applied", "under_review", "interview_scheduled", "offer_received", "rejected"] as ApplicationStatus[]).map(s => {
          const cfg = STATUS_CONFIG[s];
          return (
            <button
              key={s}
              onClick={() => setStatusFilter(statusFilter === s ? "" : s)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors",
                statusFilter === s ? cfg.color + " border-transparent" : "border-border hover:border-primary/50"
              )}
            >
              {cfg.label}
              <span className="ml-1 bg-background/40 px-1.5 py-0.5 rounded-full">
                {statusCounts[s] || 0}
              </span>
            </button>
          );
        })}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <Button
            variant={view === "table" ? "default" : "outline"}
            size="sm"
            onClick={() => setView("table")}
            className="gap-1.5"
          >
            <List className="h-3.5 w-3.5" /> Table
          </Button>
          <Button
            variant={view === "kanban" ? "default" : "outline"}
            size="sm"
            onClick={() => setView("kanban")}
            className="gap-1.5"
          >
            <LayoutGrid className="h-3.5 w-3.5" /> Kanban
          </Button>
        </div>
        <Button variant="outline" size="sm" onClick={() => setStatusFilter("")}>
          {statusFilter ? "Clear Filter" : "All Applications"}
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      ) : applications.length === 0 ? (
        <div className="flex flex-col items-center py-20 text-center">
          <Briefcase className="h-12 w-12 text-muted-foreground/30 mb-4" />
          <h3 className="text-lg font-semibold">No applications yet</h3>
          <p className="text-muted-foreground text-sm mt-2">
            Discover and apply to jobs to track them here.
          </p>
          <Button className="mt-4" variant="gradient" asChild>
            <a href="/discover-jobs">Discover Jobs</a>
          </Button>
        </div>
      ) : view === "table" ? (
        <TableView
          applications={applications}
          onStatusChange={(id, status) => updateMutation.mutate({ id, status })}
          onDelete={(id) => deleteMutation.mutate(id)}
        />
      ) : (
        <KanbanView
          applications={applications}
          onStatusChange={(id, status) => updateMutation.mutate({ id, status })}
        />
      )}
    </DashboardLayout>
  );
}

function TableView({ applications, onStatusChange, onDelete }: {
  applications: Application[];
  onStatusChange: (id: string, status: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Job</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Company</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Applied</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Score</th>
              <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {applications.map((app) => {
              const cfg = STATUS_CONFIG[app.status];
              return (
                <tr key={app.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-medium line-clamp-1">{app.job?.title}</p>
                    <p className="text-xs text-muted-foreground">{app.job?.location}</p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded bg-muted flex items-center justify-center shrink-0">
                        <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                      </div>
                      <span className="font-medium">{app.job?.company}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Select value={app.status} onValueChange={(v) => onStatusChange(app.id, v)}>
                      <SelectTrigger className="h-7 w-44 text-xs">
                        <div className={cn("flex items-center gap-1.5 px-1.5 py-0.5 rounded-full text-xs font-medium", cfg.color)}>
                          {cfg.label}
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(STATUS_CONFIG).map(([value, { label }]) => (
                          <SelectItem key={value} value={value}>{label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {app.applied_date
                      ? formatDistanceToNow(new Date(app.applied_date), { addSuffix: true })
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {app.match_score ? (
                      <span className={cn(
                        "text-xs font-semibold",
                        app.match_score >= 80 ? "text-green-600" :
                        app.match_score >= 60 ? "text-yellow-600" : "text-red-500"
                      )}>
                        {app.match_score.toFixed(0)}%
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {app.job?.apply_url && (
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0" asChild>
                          <a href={app.job.apply_url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                        onClick={() => onDelete(app.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KanbanView({ applications, onStatusChange }: {
  applications: Application[];
  onStatusChange: (id: string, status: string) => void;
}) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {KANBAN_COLUMNS.map((status) => {
        const cfg = STATUS_CONFIG[status];
        const colApps = applications.filter(a => a.status === status);
        return (
          <div key={status} className="flex-shrink-0 w-64">
            <div className="flex items-center gap-2 mb-3">
              <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", cfg.color)}>
                {cfg.label}
              </span>
              <span className="text-xs text-muted-foreground">({colApps.length})</span>
            </div>
            <div className="space-y-2">
              {colApps.map(app => (
                <div key={app.id} className="bg-card border border-border rounded-lg p-3 cursor-pointer hover:border-primary/40 transition-colors">
                  <p className="font-medium text-sm line-clamp-2">{app.job?.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{app.job?.company}</p>
                  {app.match_score && (
                    <div className="mt-2">
                      <span className={cn(
                        "text-xs font-semibold",
                        app.match_score >= 80 ? "text-green-600" : app.match_score >= 60 ? "text-yellow-600" : "text-muted-foreground"
                      )}>
                        {app.match_score.toFixed(0)}% match
                      </span>
                    </div>
                  )}
                </div>
              ))}
              {colApps.length === 0 && (
                <div className="border border-dashed border-border rounded-lg p-4 text-center">
                  <p className="text-xs text-muted-foreground">No applications</p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
