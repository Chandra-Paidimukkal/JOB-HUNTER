// ============================================================
// CORE TYPES — JobHunter AI
// ============================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  is_verified: boolean;
  created_at: string;
  onboarding_completed: boolean;
}

export interface UserProfile {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  phone?: string;
  current_location?: string;
  preferred_locations: string[];
  linkedin_url?: string;
  portfolio_url?: string;
  website_url?: string;
  current_title?: string;
  current_company?: string;
  total_experience_years?: number;
  professional_summary?: string;
  technical_skills: string[];
  soft_skills: string[];
  industries: string[];
  notice_period?: string;
  willing_to_relocate: boolean;
  updated_at: string;
}

export interface JobPreferences {
  id: string;
  user_id: string;
  preferred_titles: string[];
  preferred_industries: string[];
  preferred_companies: string[];
  preferred_countries: string[];
  preferred_cities: string[];
  remote_ok: boolean;
  hybrid_ok: boolean;
  onsite_ok: boolean;
  full_time: boolean;
  part_time: boolean;
  contract: boolean;
  internship: boolean;
  expected_salary?: number;
  min_salary?: number;
  currency: string;
  career_objective?: string;
  short_term_goals?: string;
  long_term_goals?: string;
  updated_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  file_name: string;
  file_url?: string;
  file_path?: string;
  file_type: "pdf" | "docx" | "doc" | string;
  file_size: number;
  is_primary: boolean;
  is_analyzed: boolean;
  version_name?: string;
  parsed_text?: string;
  extracted_data?: ExtractedResumeData;
  quality_score?: number;
  keyword_density?: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface ExtractedResumeData {
  personal_info: {
    name?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
    portfolio?: string;
  };
  professional_summary?: string;
  experience: WorkExperience[];
  education: Education[];
  skills: {
    technical: string[];
    soft: string[];
  };
  certifications: Certification[];
  projects: Project[];
  achievements: string[];
  keywords: string[];
}

export interface WorkExperience {
  id?: string;
  company: string;
  title: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  location?: string;
  description?: string;
  achievements: string[];
}

export interface Education {
  id?: string;
  institution: string;
  degree: string;
  field?: string;
  start_year?: number;
  end_year?: number;
  gpa?: string;
}

export interface Certification {
  id?: string;
  name: string;
  issuer?: string;
  issue_date?: string;
  expiry_date?: string;
  credential_id?: string;
}

export interface Project {
  id?: string;
  name: string;
  description?: string;
  technologies: string[];
  url?: string;
}

// ---- JOBS ----

export interface Job {
  id: string;
  title: string;
  company: string;
  company_logo?: string;
  location: string;
  country?: string;
  city?: string;
  is_remote: boolean;
  is_hybrid: boolean;
  employment_type: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  experience_min?: number;
  experience_max?: number;
  description: string;
  requirements: string[];
  skills_required: string[];
  skills_preferred: string[];
  apply_url: string;
  source: string;
  source_id?: string;
  posted_at?: string;
  deadline?: string;
  is_active: boolean;
  created_at: string;
}

export interface JobMatch {
  id: string;
  job_id: string;
  user_id: string;
  match_score: number;
  skills_match: number;
  experience_match: number;
  responsibility_match: number;
  education_match: number;
  industry_match: number;
  location_match: number;
  matching_skills: string[];
  missing_skills: string[];
  experience_alignment?: string;
  qualification_alignment?: string;
  concerns: string[];
  reasons_to_apply: string[];
  ai_recommendation?: string;
  match_category: "excellent" | "strong" | "good" | "moderate" | "low";
  job?: Job;
  created_at: string;
}

export interface SavedJob {
  id: string;
  user_id: string;
  job_id: string;
  status: ApplicationStatus;
  notes?: string;
  job?: Job;
  match?: JobMatch;
  created_at: string;
}

// ---- APPLICATIONS ----

export type ApplicationStatus =
  | "saved"
  | "recommended"
  | "ready_to_apply"
  | "applied"
  | "under_review"
  | "recruiter_contacted"
  | "interview_scheduled"
  | "interview_completed"
  | "assessment_pending"
  | "offer_received"
  | "rejected"
  | "withdrawn";

export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  status: ApplicationStatus;
  applied_date?: string;
  resume_id?: string;
  cover_letter?: string;
  recruiter_name?: string;
  recruiter_email?: string;
  recruiter_linkedin?: string;
  follow_up_date?: string;
  notes?: string;
  match_score?: number;
  job?: Job;
  resume?: Resume;
  created_at: string;
  updated_at: string;
}

// ---- OUTREACH ----

export type OutreachStatus =
  | "new_prospect"
  | "research_completed"
  | "email_generated"
  | "ready_to_send"
  | "sent"
  | "follow_up_due"
  | "response_received"
  | "interested"
  | "not_interested";

export type EmailType =
  | "job_application"
  | "hr_outreach"
  | "hiring_manager"
  | "cold_outreach"
  | "referral_request"
  | "recruiter_introduction"
  | "post_application_followup"
  | "interview_thankyou"
  | "recruiter_response"
  | "linkedin_connection"
  | "linkedin_followup"
  | "networking";

export interface OutreachContact {
  id: string;
  user_id: string;
  company_name: string;
  company_website?: string;
  company_industry?: string;
  contact_name?: string;
  contact_designation?: string;
  contact_email?: string;
  contact_linkedin?: string;
  department?: string;
  status: OutreachStatus;
  email_type?: EmailType;
  generated_email?: string;
  email_subject?: string;
  sent_date?: string;
  follow_up_date?: string;
  response_received: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface GeneratedEmail {
  id: string;
  subject_lines: string[];
  selected_subject: string;
  short_version: string;
  medium_version: string;
  detailed_version: string;
  selected_version: string;
  reasoning?: string;
  suggestions?: string[];
  tone: string;
  email_type: EmailType;
  created_at: string;
}

// ---- COMPANY ----

export interface Company {
  id: string;
  name: string;
  website?: string;
  linkedin_url?: string;
  industry?: string;
  description?: string;
  headquarters?: string;
  locations: string[];
  size?: string;
  founded_year?: number;
  products_services?: string[];
  recent_news?: string[];
  careers_url?: string;
  logo_url?: string;
  researched_at?: string;
}

// ---- INTERVIEW ----

export interface InterviewPrep {
  id: string;
  application_id: string;
  job_title: string;
  company: string;
  questions: InterviewQuestion[];
  created_at: string;
}

export interface InterviewQuestion {
  id: string;
  category: "technical" | "behavioral" | "hr" | "scenario" | "company";
  question: string;
  suggested_answer?: string;
  star_answer?: {
    situation: string;
    task: string;
    action: string;
    result: string;
  };
  difficulty: "easy" | "medium" | "hard";
}

// ---- NOTIFICATIONS ----

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  link?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

// ---- ANALYTICS ----

export interface AnalyticsOverview {
  total_jobs_discovered: number;
  relevant_jobs: number;
  high_match_jobs: number;
  saved_jobs: number;
  applications_prepared: number;
  applications_submitted: number;
  emails_generated: number;
  outreach_sent: number;
  recruiter_responses: number;
  interviews_scheduled: number;
  offers_received: number;
  rejections: number;
}

// ---- API RESPONSE TYPES ----

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// ---- BACKGROUND TASKS ----

export interface TaskStatus {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  result?: unknown;
  error?: string;
  created_at: string;
  updated_at: string;
}
