"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Building2, Globe, Search, Sparkles, AlertCircle, MapPin, Users, Briefcase, TrendingUp } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { aiApi, extractApiError } from "@/services/api";

export default function CompanyIntelligencePage() {
  const [companyName, setCompanyName] = useState("");
  const [website, setWebsite] = useState("");
  const [result, setResult] = useState<any>(null);

  const researchMutation = useMutation({
    mutationFn: () => aiApi.researchCompany({ company_name: companyName, website }),
    onSuccess: (res) => { setResult(res.data); toast.success("Company research complete!"); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  return (
    <DashboardLayout
      title="Company Intelligence"
      subtitle="AI-powered company research to personalize your outreach"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader><CardTitle className="text-sm">Research a Company</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Company Name *</Label>
              <Input placeholder="Google, Microsoft, Acme Corp..." value={companyName} onChange={e => setCompanyName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Website</Label>
              <Input placeholder="https://company.com" value={website} onChange={e => setWebsite(e.target.value)} />
            </div>
            <Button
              className="w-full gap-2" variant="gradient"
              loading={researchMutation.isPending}
              disabled={!companyName}
              onClick={() => researchMutation.mutate()}
            >
              <Sparkles className="h-4 w-4" /> Research Company
            </Button>
          </CardContent>
        </Card>

        <div className="lg:col-span-2">
          {!result ? (
            <div className="flex flex-col items-center justify-center h-80 border-2 border-dashed border-border rounded-xl text-center">
              <Building2 className="h-12 w-12 text-muted-foreground/30 mb-3" />
              <p className="font-medium">Enter a company name to begin research</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                AI will analyze the company and identify how your skills align with their needs.
              </p>
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-bold">{companyName}</h2>
                      <p className="text-muted-foreground">{result.industry}</p>
                    </div>
                    {result.confidence_score && (
                      <Badge variant="outline">
                        {result.confidence_score}% confidence
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed">{result.overview}</p>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.products_services?.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-sm mb-2">Products & Services</h4>
                      <ul className="space-y-1">
                        {result.products_services.map((p: string, i: number) => (
                          <li key={i} className="text-xs text-muted-foreground flex items-center gap-1.5">
                            <span className="text-primary">•</span> {p}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {result.tech_focus_areas?.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-sm mb-2">Tech Focus Areas</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {result.tech_focus_areas.map((t: string) => (
                          <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {result.potential_departments_hiring?.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-sm mb-2">Potential Hiring Departments</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {result.potential_departments_hiring.map((d: string) => (
                          <Badge key={d} variant="outline" className="text-xs">{d}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {result.notable_aspects?.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-sm mb-2">Notable Aspects</h4>
                      <ul className="space-y-1">
                        {result.notable_aspects.map((a: string, i: number) => (
                          <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                            <TrendingUp className="h-3 w-3 text-primary shrink-0 mt-0.5" /> {a}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>

              {result.disclaimer && (
                <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg border border-yellow-200 dark:border-yellow-800">
                  <AlertCircle className="h-4 w-4 text-yellow-600 shrink-0 mt-0.5" />
                  <p className="text-xs text-yellow-700 dark:text-yellow-300">{result.disclaimer}</p>
                </div>
              )}

              <Button variant="gradient" className="gap-2 w-full" asChild>
                <a href={`/outreach-studio?company=${encodeURIComponent(companyName)}&website=${encodeURIComponent(website)}`}>
                  <Sparkles className="h-4 w-4" /> Generate Outreach for {companyName}
                </a>
              </Button>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
