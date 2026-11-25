"use client";

import React, { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useDropzone } from "react-dropzone";
import {
  Upload, FileText, Star, Trash2, Eye, Zap, Download,
  CheckCircle, AlertCircle, Clock, BarChart2, Tag, Award
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { resumeApi, aiApi, extractApiError } from "@/services/api";
import { Resume } from "@/types";
import { cn } from "@/utils/cn";

export default function ResumeManagerPage() {
  const queryClient = useQueryClient();
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => resumeApi.list().then(r => r.data),
  });

  const resumes: Resume[] = data?.items || [];

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: () => {
      toast.success("Resume uploaded! AI analysis running...");
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => resumeApi.delete(id),
    onSuccess: () => {
      toast.success("Resume deleted");
      setSelectedResume(null);
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const setPrimaryMutation = useMutation({
    mutationFn: (id: string) => resumeApi.setPrimary(id),
    onSuccess: () => {
      toast.success("Primary resume updated");
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const analyzeMutation = useMutation({
    mutationFn: (id: string) => aiApi.analyzeResume(id),
    onSuccess: () => {
      toast.success("Re-analysis started!");
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["resumes"] }), 3000);
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const onDrop = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (file) uploadMutation.mutate(file);
    },
    [uploadMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const qualityColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  const extracted = selectedResume?.extracted_data;

  return (
    <DashboardLayout
      title="Resume Manager"
      subtitle="Upload, analyze, and manage multiple resume versions"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Upload + List */}
        <div className="space-y-4">
          {/* Upload zone */}
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all",
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-muted/30"
            )}
          >
            <input {...getInputProps()} />
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
              {uploadMutation.isPending ? (
                <span className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              ) : (
                <Upload className="h-6 w-6 text-primary" />
              )}
            </div>
            {uploadMutation.isPending ? (
              <p className="text-sm font-medium">Uploading and analyzing...</p>
            ) : (
              <>
                <p className="text-sm font-medium">Drop your resume here</p>
                <p className="text-xs text-muted-foreground mt-1">PDF or DOCX · Max 10MB</p>
                <Button size="sm" variant="outline" className="mt-3">Browse Files</Button>
              </>
            )}
          </div>

          {/* Resume list */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Your Resumes ({resumes.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 p-3">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
                ))
              ) : resumes.length === 0 ? (
                <div className="text-center py-6 text-sm text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  No resumes uploaded yet
                </div>
              ) : (
                resumes.map((resume) => (
                  <div
                    key={resume.id}
                    onClick={() => setSelectedResume(resume)}
                    className={cn(
                      "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                      selectedResume?.id === resume.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/30"
                    )}
                  >
                    <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center shrink-0">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{resume.version_name || resume.file_name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {resume.is_primary && (
                          <Badge variant="default" className="text-[10px] px-1 py-0 h-3.5">Primary</Badge>
                        )}
                        {resume.is_analyzed ? (
                          <span className="flex items-center gap-0.5 text-[10px] text-green-600">
                            <CheckCircle className="h-3 w-3" /> Analyzed
                          </span>
                        ) : (
                          <span className="flex items-center gap-0.5 text-[10px] text-yellow-600">
                            <Clock className="h-3 w-3" /> Pending
                          </span>
                        )}
                        {resume.quality_score && (
                          <span className={cn("text-[10px] font-medium", qualityColor(resume.quality_score))}>
                            {resume.quality_score}% quality
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Resume details */}
        <div className="lg:col-span-2">
          {!selectedResume ? (
            <div className="flex flex-col items-center justify-center h-80 border-2 border-dashed border-border rounded-xl">
              <FileText className="h-12 w-12 text-muted-foreground/30 mb-3" />
              <p className="font-medium">Select a resume to view details</p>
              <p className="text-sm text-muted-foreground mt-1">Or upload your first resume</p>
            </div>
          ) : (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">{selectedResume.version_name || selectedResume.file_name}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      {selectedResume.file_type.toUpperCase()} ·{" "}
                      {(selectedResume.file_size / 1024).toFixed(0)} KB
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {!selectedResume.is_primary && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5"
                        onClick={() => setPrimaryMutation.mutate(selectedResume.id)}
                        loading={setPrimaryMutation.isPending}
                      >
                        <Star className="h-3.5 w-3.5" /> Set Primary
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5"
                      onClick={() => analyzeMutation.mutate(selectedResume.id)}
                      loading={analyzeMutation.isPending}
                    >
                      <Zap className="h-3.5 w-3.5" /> Re-Analyze
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5 text-destructive hover:text-destructive"
                      onClick={() => deleteMutation.mutate(selectedResume.id)}
                      loading={deleteMutation.isPending}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {!selectedResume.is_analyzed ? (
                  <div className="flex flex-col items-center py-8 text-center">
                    <Clock className="h-10 w-10 text-yellow-500 mb-3" />
                    <p className="font-medium">Analysis in progress</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      AI is extracting your profile from this resume. This takes a few seconds.
                    </p>
                    <Button
                      className="mt-4" size="sm" variant="outline"
                      onClick={() => queryClient.invalidateQueries({ queryKey: ["resumes"] })}
                    >
                      Refresh Status
                    </Button>
                  </div>
                ) : !extracted ? (
                  <div className="flex flex-col items-center py-8 text-center">
                    <AlertCircle className="h-10 w-10 text-destructive mb-3" />
                    <p className="font-medium">Analysis failed</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Could not extract data. Try re-analyzing or upload a clearer version.
                    </p>
                    <Button className="mt-4" size="sm" onClick={() => analyzeMutation.mutate(selectedResume.id)}>
                      Retry Analysis
                    </Button>
                  </div>
                ) : (
                  <Tabs defaultValue="overview">
                    <TabsList className="mb-4">
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="skills">Skills</TabsTrigger>
                      <TabsTrigger value="experience">Experience</TabsTrigger>
                      <TabsTrigger value="keywords">Keywords</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview">
                      <div className="space-y-4">
                        {/* Quality score */}
                        <div className="p-4 rounded-lg bg-muted/50">
                          <div className="flex justify-between text-sm mb-2">
                            <span className="font-medium">Resume Quality Score</span>
                            <span className={cn("font-bold text-lg", qualityColor(selectedResume.quality_score || 0))}>
                              {selectedResume.quality_score || 0}/100
                            </span>
                          </div>
                          <Progress value={selectedResume.quality_score || 0} className="h-2" />
                        </div>

                        {/* Personal info */}
                        {extracted.personal_info && (
                          <div>
                            <h4 className="text-sm font-semibold mb-2">Extracted Contact Info</h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {Object.entries(extracted.personal_info).map(([k, v]) =>
                                v ? (
                                  <div key={k} className="bg-muted/40 rounded p-2">
                                    <span className="text-muted-foreground capitalize text-xs">{k.replace("_", " ")}:</span>
                                    <p className="font-medium text-xs mt-0.5 truncate">{v as string}</p>
                                  </div>
                                ) : null
                              )}
                            </div>
                          </div>
                        )}

                        {/* Summary */}
                        {extracted.professional_summary && (
                          <div>
                            <h4 className="text-sm font-semibold mb-1">Professional Summary</h4>
                            <p className="text-sm text-muted-foreground leading-relaxed bg-muted/40 p-3 rounded">
                              {extracted.professional_summary}
                            </p>
                          </div>
                        )}
                      </div>
                    </TabsContent>

                    <TabsContent value="skills">
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                            <Zap className="h-4 w-4 text-primary" /> Technical Skills ({extracted.skills?.technical?.length || 0})
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {extracted.skills?.technical?.map((skill: string) => (
                              <Badge key={skill} variant="secondary">{skill}</Badge>
                            ))}
                          </div>
                        </div>
                        {extracted.skills?.soft?.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold mb-2">Soft Skills</h4>
                            <div className="flex flex-wrap gap-1.5">
                              {extracted.skills.soft.map((skill: string) => (
                                <Badge key={skill} variant="outline">{skill}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </TabsContent>

                    <TabsContent value="experience">
                      <div className="space-y-3">
                        {extracted.experience?.map((exp: any, i: number) => (
                          <div key={i} className="border border-border rounded-lg p-3">
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="font-semibold text-sm">{exp.title}</p>
                                <p className="text-xs text-muted-foreground">{exp.company}</p>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                              </span>
                            </div>
                            {exp.achievements?.length > 0 && (
                              <ul className="mt-2 space-y-0.5">
                                {exp.achievements.slice(0, 3).map((a: string, j: number) => (
                                  <li key={j} className="text-xs text-muted-foreground flex items-start gap-1.5">
                                    <span className="text-primary mt-0.5">•</span> {a}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </TabsContent>

                    <TabsContent value="keywords">
                      <div>
                        <p className="text-sm text-muted-foreground mb-3">
                          These keywords were identified in your resume. They're used for ATS matching.
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {extracted.keywords?.map((kw: string) => (
                            <Badge key={kw} variant="outline" className="text-xs">
                              <Tag className="h-3 w-3 mr-1" /> {kw}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
