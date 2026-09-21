import type { ApplicationStatus, ReminderInterval } from '../utils/constants';

export type { ApplicationStatus, ReminderInterval };

export interface Job {
  id: string;
  title: string;
  location: string;
  url: string;
  company: string;
  source: string;
  pay: string;
  pay_type?: 'hourly' | 'salary' | '' | string;
  level?: string;
  schedule?: 'full-time' | 'part-time' | 'contract' | '' | string;
  posted_at?: string;
  description?: string;
  is_new?: boolean;
  commitment?: string;
  employment_type?: string;
  match_lane?: string;
}

export interface Application {
  id: number | string;
  job_id?: string | null;
  company: string;
  title: string;
  url?: string;
  location?: string;
  pay?: string;
  status: ApplicationStatus;
  applied_at?: string;
  deadline?: string;
  reminder_interval?: ReminderInterval;
  notes?: string;
}

export interface CompanyEntry {
  name: string;
  board: string;
  slug?: string;
  url?: string;
  tenant?: string;
  site?: string;
  wd?: number;
  search?: string;
  search_terms?: string[];
  domain?: string;
  keyword?: string;
  locations?: string[];
}

export interface ScanConfig {
  title_include: string[];
  title_exclude?: string[];
  location_include: string[];
  location_exclude?: string[];
  allow_all_remote?: boolean;
  companies: CompanyEntry[];
  description_include?: string[];
  adjacent_include?: string[];
  early_career_include?: string[];
}

export interface ScanProgressEvent {
  type: 'progress';
  company: string;
  index: number;
  total: number;
}

export interface ScanMatchesEvent {
  type: 'matches';
  company: string;
  jobs: Job[];
  total_open?: number;
  matched?: number;
  new?: number;
}

export interface ScanErrorEvent {
  type: 'scan_error';
  company: string;
  error: string;
}

export interface ScanDoneEvent {
  type: 'done';
  total_matches: number;
  new?: number;
  companies_scanned: number;
  errors: number;
}

export interface ScanGeneralErrorEvent {
  type: 'error';
  company?: string;
  error: string;
}

export type ScanEvent =
  | ScanProgressEvent
  | ScanMatchesEvent
  | ScanErrorEvent
  | ScanDoneEvent
  | ScanGeneralErrorEvent;

export interface StaticData {
  jobs: Job[];
  errors: Array<{ company: string; error: string }>;
  companies_scanned: number;
  updated_at: string;
}

export interface User {
  id?: number | string;
  username: string;
  email: string;
  role?: 'admin' | 'user' | string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
}

export interface FilterState {
  search: string;
  level: string[];
  payType: string[];
  schedule: string[];
  source: string[];
  favOnly: boolean;
  showHidden: boolean;
}

export interface SavedFilter {
  name: string;
  state: FilterState;
}

export interface VisibleColumns {
  scanner: string[];
  tracker: string[];
}

export interface ScanFilters {
  levels: string[];
  schedules: string[];
  payListed: boolean;
  minHourly: string;
  minSalary: string;
  favoritesOnly: boolean;
  location: string;
}

export interface UserPreferences {
  theme?: 'dark' | 'light';
  autoscan?: boolean;
  showHiddenToggle?: boolean;
  defaultTracker?: boolean;
  autoClearDays?: string;
  level_intern?: boolean;
  level_fellow?: boolean;
  level_apprentice?: boolean;
  level_entry?: boolean;
  level_mid?: boolean;
  level_senior?: boolean;
  level_manager?: boolean;
  sched_fulltime?: boolean;
  sched_parttime?: boolean;
  sched_contract?: boolean;
  paid_only?: boolean;
  newAlertsOnly?: boolean;
  [key: string]: unknown;
}

export interface DataSource {
  scan(onProgress?: (event: ScanEvent) => void, signal?: AbortSignal): Promise<Job[]>;
  getApplications(): Promise<Application[]>;
  addApplication(app: Omit<Application, 'id'>): Promise<string | number>;
  updateApplication(id: string | number, patch: Partial<Application>): Promise<void>;
  deleteApplication(id: string | number): Promise<void>;
  hideJob(id: string): Promise<void>;
  unhideJob(id: string): Promise<void>;
  getHiddenIds(): Promise<string[]>;
}

export interface AuthSource {
  currentUser: User | null;
  login(credentials: LoginCredentials): Promise<User>;
  register(credentials: RegisterCredentials): Promise<User>;
  loginWithGoogle(): Promise<User>;
  logout(): Promise<void>;
  onAuthStateChanged(cb: (user: User | null) => void): () => void;
  getCurrentUser(): Promise<User | null>;
  updateUsername(name: string): Promise<void>;
  updateEmail(email: string): Promise<void>;
  updatePassword(current: string, next: string): Promise<void>;
}
