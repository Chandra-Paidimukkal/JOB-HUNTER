"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Linkedin, Sparkles, Copy, CheckCircle, User, Building2 } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { aiApi, extractApiError } from "@/services/api";

const MESSAGE_TYPES = [
  { value: "connection_request", label: "Connection Request (300 chars)" },
  { value: "recruiter_message", label: "Recruiter Introduction" },
  { value: "hiring_manager", label: "Hiring Manager Message" },
  { value: "followup", label: "Follow-up After Connection" },
  { value: "networking", label: "Professional Networking" },
  { value: "referral", label: "Referral Request" },
];

export default function LinkedInOutreachPage() {
  const [form, setForm] = useState({ message_type: "connection_request", recipient_name: "", recipient_title: "", company_name: "" });
  const [result, setResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const generateMutation = useMutation({
    mutationFn: () => aiApi.generateLinkedInMessage(form),
    onSuccess: (res) => { setResult(res.data); toast.success("Message generated!"); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copied!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <DashboardLayout title="LinkedIn Outreach" subtitle="Generate personalized LinkedIn connection and follow-up messages">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-4xl">
        <Card>
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><Linkedin className="h-4 w-4 text-blue-600" /> Message Details</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Message Type</Label>
              <Select value={form.message_type} onValueChange={v => setForm(f => ({ ...f, message_type: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{MESSAGE_TYPES.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            {[{ k: "recipient_name", l: "Recipient Name", p: "Jane Smith" }, { k: "recipient_title", l: "Recipient Title", p: "Engineering Manager" }, { k: "company_name", l: "Company", p: "Google" }].map(({ k, l, p }) => (
              <div key={k} className="space-y-1.5">
                <Label>{l}</Label>
                <Input placeholder={p} value={(form as any)[k]} onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} />
              </div>
            ))}
            <Button className="w-full gap-2" variant="gradient" loading={generateMutation.isPending}
              onClick={() => generateMutation.mutate()}>
              <Sparkles className="h-4 w-4" /> Generate Message
            </Button>
          </CardContent>
        </Card>

        <div>
          {!result ? (
            <div className="flex flex-col items-center justify-center h-full border-2 border-dashed border-border rounded-xl text-center p-8">
              <Linkedin className="h-12 w-12 text-blue-400/50 mb-3" />
              <p className="font-medium">Fill in the details to generate a personalized message</p>
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-muted-foreground">GENERATED MESSAGE</p>
                    <span className={`text-xs ${(result.character_count || 0) > 300 ? "text-red-500" : "text-green-500"}`}>
                      {result.character_count || result.message?.length || 0} chars
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed bg-muted/40 p-3 rounded-lg">{result.message}</p>
                  <div className="flex gap-2 mt-3">
                    <Button size="sm" variant="outline" className="gap-1.5" onClick={() => handleCopy(result.message)}>
                      {copied ? <CheckCircle className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />} Copy
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => generateMutation.mutate()} loading={generateMutation.isPending}>
                      Regenerate
                    </Button>
                  </div>
                </CardContent>
              </Card>
              {result.alternative_message && (
                <Card>
                  <CardContent className="p-4">
                    <p className="text-xs font-semibold text-muted-foreground mb-2">SHORTER ALTERNATIVE</p>
                    <p className="text-sm leading-relaxed bg-muted/40 p-3 rounded-lg">{result.alternative_message}</p>
                    <Button size="sm" variant="outline" className="gap-1.5 mt-2" onClick={() => handleCopy(result.alternative_message)}>
                      <Copy className="h-3.5 w-3.5" /> Copy
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
