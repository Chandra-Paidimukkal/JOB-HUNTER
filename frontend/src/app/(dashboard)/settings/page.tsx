"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Mail, Shield, Bell, Zap, ExternalLink, CheckCircle, AlertCircle } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { emailApi, extractApiError } from "@/services/api";
import { useQuery } from "@tanstack/react-query";

export default function SettingsPage() {
  const { data: emailStatus } = useQuery({
    queryKey: ["email-status"],
    queryFn: () => emailApi.status().then(r => r.data),
  });

  const getAuthUrlMutation = useMutation({
    mutationFn: () => emailApi.status(), // placeholder
    onSuccess: () => toast.info("OAuth flow would redirect here"),
  });

  const disconnectMutation = useMutation({
    mutationFn: () => emailApi.disconnect(),
    onSuccess: () => toast.success("Gmail disconnected"),
  });

  return (
    <DashboardLayout title="Settings" subtitle="Configure integrations, notifications, and account settings">
      <div className="max-w-2xl">
        <Tabs defaultValue="integrations">
          <TabsList className="mb-6">
            <TabsTrigger value="integrations">Integrations</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="api">API Keys</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>

          <TabsContent value="integrations" className="space-y-4">
            {/* Gmail */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-red-50 dark:bg-red-950/30 flex items-center justify-center">
                      <Mail className="h-5 w-5 text-red-500" />
                    </div>
                    <div>
                      <CardTitle className="text-sm">Gmail Integration</CardTitle>
                      <CardDescription>Send outreach emails directly from the platform</CardDescription>
                    </div>
                  </div>
                  {emailStatus?.connected ? (
                    <span className="flex items-center gap-1.5 text-xs text-green-600">
                      <CheckCircle className="h-4 w-4" /> Connected
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <AlertCircle className="h-4 w-4" /> Not connected
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!emailStatus?.configured ? (
                  <div className="p-3 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg border border-yellow-200 text-sm">
                    <p className="font-medium text-yellow-700 dark:text-yellow-300">Setup required</p>
                    <p className="text-yellow-600 dark:text-yellow-400 text-xs mt-1">
                      Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in your backend .env file, then restart the server.
                    </p>
                  </div>
                ) : emailStatus?.connected ? (
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Connected as: <strong>{emailStatus.email}</strong></p>
                    <Button variant="outline" size="sm" onClick={() => disconnectMutation.mutate()}>Disconnect</Button>
                  </div>
                ) : (
                  <Button variant="gradient" size="sm" className="gap-2" asChild>
                    <a href="/api/v1/email/auth-url" target="_self">
                      <Mail className="h-4 w-4" /> Connect Gmail
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Job Sources */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Job Source Integrations</CardTitle>
                <CardDescription>Configure API keys to access more job sources</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { name: "Adzuna", desc: "Free tier API — register at developer.adzuna.com", key: "ADZUNA_APP_ID + ADZUNA_API_KEY", url: "https://developer.adzuna.com" },
                  { name: "JSearch (via RapidAPI)", desc: "Aggregates LinkedIn, Indeed, Glassdoor", key: "JSEARCH_API_KEY", url: "https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch" },
                  { name: "Remotive", desc: "Free remote jobs API — no key required", key: "No key needed ✓", url: "https://remotive.com/api" },
                ].map(src => (
                  <div key={src.name} className="flex items-start justify-between p-3 border border-border rounded-lg">
                    <div>
                      <p className="text-sm font-medium">{src.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{src.desc}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">Set in .env: <code className="bg-muted px-1 rounded">{src.key}</code></p>
                    </div>
                    <Button size="sm" variant="outline" className="gap-1 shrink-0" asChild>
                      <a href={src.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-3 w-3" /> Docs
                      </a>
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardContent className="p-6 space-y-4">
                <p className="text-sm text-muted-foreground">Configure which events trigger notifications.</p>
                {[
                  "New high-match jobs discovered",
                  "Application status changes",
                  "Follow-up reminders",
                  "Interview date reminders",
                  "Recruiter response detected",
                ].map(item => (
                  <div key={item} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <span className="text-sm">{item}</span>
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Enabled</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
                  <p className="text-sm font-medium text-blue-700 dark:text-blue-300">API keys are managed in the backend .env file</p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Never expose API keys in the frontend. All AI requests go through the backend server.
                  </p>
                </div>
                {[
                  { name: "GROQ_API_KEY", desc: "Required for all AI features", url: "https://console.groq.com" },
                  { name: "GOOGLE_CLIENT_ID", desc: "Required for Google OAuth login", url: "https://console.cloud.google.com" },
                  { name: "GMAIL_CLIENT_ID", desc: "Required for Gmail email sending", url: "https://console.cloud.google.com" },
                ].map(key => (
                  <div key={key.name} className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div>
                      <p className="text-sm font-mono font-medium">{key.name}</p>
                      <p className="text-xs text-muted-foreground">{key.desc}</p>
                    </div>
                    <Button size="sm" variant="outline" asChild>
                      <a href={key.url} target="_blank" rel="noopener noreferrer">Get Key</a>
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="account">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="space-y-2">
                  <Label>Change Password</Label>
                  <Input type="password" placeholder="Current password" />
                  <Input type="password" placeholder="New password" />
                  <Button size="sm">Update Password</Button>
                </div>
                <div className="pt-4 border-t border-border">
                  <p className="text-sm font-medium text-destructive mb-2">Danger Zone</p>
                  <Button variant="outline" size="sm" className="text-destructive border-destructive/40">
                    Delete Account & All Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
