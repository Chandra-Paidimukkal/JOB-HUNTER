"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Mail, Send, Clock, CheckCircle, Building2, Plus, Filter } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { outreachApi, emailApi, extractApiError } from "@/services/api";
import { OutreachContact } from "@/types";
import { cn } from "@/utils/cn";
import { formatDistanceToNow } from "date-fns";

const STATUS_COLORS: Record<string, string> = {
  new_prospect: "bg-gray-100 text-gray-700",
  research_completed: "bg-blue-100 text-blue-800",
  email_generated: "bg-indigo-100 text-indigo-800",
  ready_to_send: "bg-cyan-100 text-cyan-800",
  sent: "bg-green-100 text-green-800",
  follow_up_due: "bg-orange-100 text-orange-800",
  response_received: "bg-purple-100 text-purple-800",
  interested: "bg-emerald-100 text-emerald-800",
  not_interested: "bg-red-100 text-red-800",
};

export default function EmailCampaignsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedContact, setSelectedContact] = useState<OutreachContact | null>(null);
  const [sending, setSending] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["outreach", statusFilter],
    queryFn: () => outreachApi.list({ status: statusFilter || undefined }).then(r => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: any) => outreachApi.update(id, data),
    onSuccess: () => { toast.success("Updated!"); queryClient.invalidateQueries({ queryKey: ["outreach"] }); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const { data: emailStatus } = useQuery({
    queryKey: ["email-status"],
    queryFn: () => emailApi.status().then(r => r.data),
  });

  const contacts: OutreachContact[] = data?.items || [];

  const handleSend = async (contact: OutreachContact) => {
    if (!emailStatus?.connected) {
      toast.error("Connect Gmail first in Settings → Integrations");
      return;
    }
    if (!contact.contact_email) {
      toast.error("No recipient email address");
      return;
    }
    setSending(true);
    try {
      await emailApi.send({
        to_email: contact.contact_email,
        subject: contact.email_subject || "Job Inquiry",
        body: contact.generated_email || "",
        outreach_contact_id: contact.id,
      });
      updateMutation.mutate({ id: contact.id, data: { status: "sent", sent_date: new Date().toISOString() } });
      toast.success("Email sent successfully!");
    } catch (err) {
      toast.error(extractApiError(err));
    } finally {
      setSending(false);
    }
  };

  return (
    <DashboardLayout title="Email Campaign Manager" subtitle="Track and manage all your outreach contacts">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-6">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48 h-8 text-xs">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Statuses</SelectItem>
            {Object.keys(STATUS_COLORS).map(s => (
              <SelectItem key={s} value={s} className="capitalize">{s.replace(/_/g, " ")}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button size="sm" variant="gradient" className="gap-1.5" asChild>
          <a href="/outreach-studio"><Plus className="h-3.5 w-3.5" /> New Outreach</a>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* List */}
        <div className="lg:col-span-2 space-y-2">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-20 bg-muted animate-pulse rounded-lg" />)
          ) : contacts.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-center border-2 border-dashed border-border rounded-xl">
              <Mail className="h-10 w-10 text-muted-foreground/30 mb-3" />
              <p className="font-medium text-sm">No outreach contacts yet</p>
              <p className="text-xs text-muted-foreground mt-1">Generate emails in the AI Outreach Studio</p>
            </div>
          ) : (
            contacts.map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedContact(c)}
                className={cn("p-3 rounded-lg border cursor-pointer transition-colors",
                  selectedContact?.id === c.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/40")}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-sm">{c.company_name}</p>
                    <p className="text-xs text-muted-foreground">{c.contact_name || "No contact"} · {c.email_type?.replace(/_/g, " ")}</p>
                  </div>
                  <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full font-medium", STATUS_COLORS[c.status] || "bg-gray-100 text-gray-700")}>
                    {c.status?.replace(/_/g, " ")}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDistanceToNow(new Date(c.created_at), { addSuffix: true })}
                </p>
              </div>
            ))
          )}
        </div>

        {/* Detail */}
        <div className="lg:col-span-3">
          {!selectedContact ? (
            <div className="flex flex-col items-center justify-center h-80 border-2 border-dashed border-border rounded-xl text-center">
              <Mail className="h-12 w-12 text-muted-foreground/30 mb-3" />
              <p className="font-medium">Select a contact to view details</p>
            </div>
          ) : (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{selectedContact.company_name}</CardTitle>
                {selectedContact.contact_name && (
                  <p className="text-sm text-muted-foreground">{selectedContact.contact_name} · {selectedContact.contact_designation}</p>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedContact.email_subject && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-1">SUBJECT</p>
                    <p className="text-sm font-medium">{selectedContact.email_subject}</p>
                  </div>
                )}
                {selectedContact.generated_email && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-1">EMAIL BODY</p>
                    <div className="bg-muted/40 rounded-lg p-3 text-sm whitespace-pre-wrap max-h-64 overflow-y-auto">
                      {selectedContact.generated_email}
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  {selectedContact.status !== "sent" && selectedContact.generated_email && (
                    <Button
                      size="sm" variant="gradient" className="gap-1.5"
                      loading={sending}
                      onClick={() => handleSend(selectedContact)}
                    >
                      <Send className="h-3.5 w-3.5" />
                      {emailStatus?.connected ? "Send via Gmail" : "Connect Gmail First"}
                    </Button>
                  )}
                  <Select
                    value={selectedContact.status}
                    onValueChange={(v) => updateMutation.mutate({ id: selectedContact.id, data: { status: v } })}
                  >
                    <SelectTrigger className="w-44 h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.keys(STATUS_COLORS).map(s => (
                        <SelectItem key={s} value={s} className="capitalize">{s.replace(/_/g, " ")}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
