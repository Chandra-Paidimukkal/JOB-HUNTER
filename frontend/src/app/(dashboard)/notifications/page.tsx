"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, Trash2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { notificationsApi, extractApiError } from "@/services/api";
import { Notification } from "@/types";
import { cn } from "@/utils/cn";
import { formatDistanceToNow } from "date-fns";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list().then(r => r.data),
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      toast.success("All marked as read");
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const readMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const notifications: Notification[] = data?.items || [];
  const unreadCount = data?.unread_count || 0;

  return (
    <DashboardLayout title="Notifications" subtitle={`${unreadCount} unread`}>
      <div className="max-w-2xl">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">{notifications.length} notifications</p>
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" className="gap-1.5"
              onClick={() => markAllMutation.mutate()} loading={markAllMutation.isPending}>
              <CheckCheck className="h-3.5 w-3.5" /> Mark all read
            </Button>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />)}
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center py-20 text-center">
            <Bell className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <h3 className="text-lg font-semibold">No notifications yet</h3>
            <p className="text-muted-foreground text-sm mt-2">
              You'll see job alerts, application updates, and follow-up reminders here.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.map((n) => (
              <div
                key={n.id}
                className={cn(
                  "p-4 rounded-lg border cursor-pointer transition-colors",
                  n.is_read ? "border-border bg-transparent" : "border-primary/20 bg-primary/5"
                )}
                onClick={() => !n.is_read && readMutation.mutate(n.id)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    {!n.is_read && <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />}
                    <div>
                      <p className={cn("text-sm font-medium", !n.is_read && "font-semibold")}>{n.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                      <p className="text-xs text-muted-foreground/60 mt-1">
                        {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                  {n.link && (
                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0 shrink-0" asChild>
                      <a href={n.link}><ExternalLink className="h-3.5 w-3.5" /></a>
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
