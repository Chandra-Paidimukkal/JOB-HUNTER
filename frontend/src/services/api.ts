import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Axios instance ──────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

// Request interceptor — attach JWT
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — handle 401
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      Cookies.remove("access_token");
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Auth ────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  logout: () => api.post("/auth/logout"),
  forgotPassword: (email: string) =>
    api.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, password: string) =>
    api.post("/auth/reset-password", { token, password }),
  verifyEmail: (token: string) => api.post("/auth/verify-email", { token }),
  me: () => api.get("/auth/me"),
  googleLogin: (token: string) => api.post("/auth/google", { token }),
};

// ── Profile ─────────────────────────────────────────────────
export const profileApi = {
  get: () => api.get("/profile"),
  update: (data: unknown) => api.put("/profile", data),
  getPreferences: () => api.get("/profile/preferences"),
  updatePreferences: (data: unknown) => api.put("/profile/preferences", data),
  completeOnboarding: (data: unknown) => api.post("/profile/onboarding", data),
};

// ── Resumes ─────────────────────────────────────────────────
export const resumeApi = {
  upload: (file: File, versionName?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (versionName) form.append("version_name", versionName);
    return api.post("/resumes/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: () => api.get("/resumes"),
  get: (id: string) => api.get(`/resumes/${id}`),
  delete: (id: string) => api.delete(`/resumes/${id}`),
  setPrimary: (id: string) => api.put(`/resumes/${id}/primary`),
  analyze: (id: string) => api.post(`/resumes/${id}/analyze`),
  customize: (id: string, jobId: string) =>
    api.post(`/resumes/${id}/customize`, { job_id: jobId }),
};

// ── Jobs ─────────────────────────────────────────────────────
export const jobsApi = {
  list: (params?: Record<string, unknown>) => api.get("/jobs", { params }),
  search: (data: unknown) => api.post("/jobs/search", data),
  get: (id: string) => api.get(`/jobs/${id}`),
  save: (id: string) => api.post(`/jobs/${id}/save`),
  unsave: (id: string) => api.delete(`/jobs/${id}/save`),
  match: (id: string) => api.post(`/jobs/${id}/match`),
  getMatches: (params?: Record<string, unknown>) =>
    api.get("/jobs/matches", { params }),
  getSaved: () => api.get("/jobs/saved"),
  triggerDiscovery: () => api.post("/jobs/discover"),
  getDiscoveryStatus: (taskId: string) =>
    api.get(`/jobs/discover/${taskId}/status`),
};

// ── Applications ─────────────────────────────────────────────
export const applicationsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/applications", { params }),
  create: (data: unknown) => api.post("/applications", data),
  get: (id: string) => api.get(`/applications/${id}`),
  update: (id: string, data: unknown) => api.put(`/applications/${id}`, data),
  delete: (id: string) => api.delete(`/applications/${id}`),
};

// ── AI ───────────────────────────────────────────────────────
export const aiApi = {
  analyzeResume: (resumeId: string) =>
    api.post("/ai/analyze-resume", { resume_id: resumeId }),
  jobMatch: (jobId: string, resumeId: string) =>
    api.post("/ai/job-match", { job_id: jobId, resume_id: resumeId }),
  generateCoverLetter: (data: {
    job_id: string;
    resume_id?: string;
    style?: string;
  }) => api.post("/ai/generate-cover-letter", data),
  generateEmail: (data: unknown) => api.post("/ai/generate-email", data),
  generateLinkedInMessage: (data: unknown) =>
    api.post("/ai/generate-linkedin-message", data),
  researchCompany: (data: { company_name: string; website?: string }) =>
    api.post("/ai/research-company", data),
  interviewPrep: (data: { job_id: string; resume_id?: string }) =>
    api.post("/ai/interview-preparation", data),
  customizeResume: (data: { job_id: string; resume_id?: string }) =>
    api.post("/ai/customize-resume", data),
  generateApplicationAnswers: (data: unknown) =>
    api.post("/ai/generate-application-answers", data),
  analyzeInterviewAnswer: (data: { question: string; answer: string; job_context?: string }) =>
    api.post("/ai/analyze-interview-answer", data),
};

// ── Outreach ─────────────────────────────────────────────────
export const outreachApi = {
  list: (params?: Record<string, unknown>) => api.get("/outreach", { params }),
  create: (data: unknown) => api.post("/outreach", data),
  get: (id: string) => api.get(`/outreach/${id}`),
  update: (id: string, data: unknown) => api.put(`/outreach/${id}`, data),
  createFollowUp: (id: string, data: unknown) =>
    api.post(`/outreach/${id}/followup`, data),
  delete: (id: string) => api.delete(`/outreach/${id}`),
};

// ── Email (Gmail) ─────────────────────────────────────────────
export const emailApi = {
  connect: (code: string) => api.post("/email/connect", { code }),
  disconnect: () => api.delete("/email/connect"),
  status: () => api.get("/email/status"),
  createDraft: (data: unknown) => api.post("/email/draft", data),
  send: (data: unknown) => api.post("/email/send", data),
  history: (params?: Record<string, unknown>) =>
    api.get("/email/history", { params }),
};

// ── Analytics ─────────────────────────────────────────────────
export const analyticsApi = {
  overview: (params?: { start_date?: string; end_date?: string }) =>
    api.get("/analytics/overview", { params }),
  applications: (params?: Record<string, unknown>) =>
    api.get("/analytics/applications", { params }),
  outreach: (params?: Record<string, unknown>) =>
    api.get("/analytics/outreach", { params }),
  jobMatches: (params?: Record<string, unknown>) =>
    api.get("/analytics/job-matches", { params }),
};

// ── Notifications ─────────────────────────────────────────────
export const notificationsApi = {
  list: () => api.get("/notifications"),
  markRead: (id: string) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put("/notifications/read-all"),
  delete: (id: string) => api.delete(`/notifications/${id}`),
};

// ── Companies ─────────────────────────────────────────────────
export const companiesApi = {
  research: (data: { company_name: string; website?: string }) =>
    api.post("/companies/research", data),
  get: (id: string) => api.get(`/companies/${id}`),
  list: () => api.get("/companies"),
};

// ── Utility ───────────────────────────────────────────────────
export function extractApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail))
      return data.detail.map((d: { msg: string }) => d.msg).join(", ");
    if (data?.message) return data.message;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}
