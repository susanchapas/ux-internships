import { SYNC_KEYS } from '../utils/constants';
import { isStaticMode } from './mode';
import { cloudSync } from './sync';
import type { Application } from './types';

const LS_KEY = SYNC_KEYS.tracker;

function loadFromLocalStorage(): Application[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? (JSON.parse(raw) as Application[]) : [];
  } catch {
    return [];
  }
}

function saveToLocalStorage(apps: Application[]): void {
  localStorage.setItem(LS_KEY, JSON.stringify(apps));
  cloudSync();
}

export async function getApplicationsServer(): Promise<Application[]> {
  const response = await fetch('/api/applications');
  if (!response.ok) {
    throw new Error(`Failed to load applications: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as Application[];
}

export async function addApplicationServer(app: Omit<Application, 'id'>): Promise<string | number> {
  const response = await fetch('/api/applications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(app),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to add application');
  }
  const data = (await response.json()) as { id: string | number };
  return data.id;
}

export async function updateApplicationServer(
  id: string | number,
  patch: Partial<Application>
): Promise<void> {
  const response = await fetch(`/api/applications/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
  if (!response.ok) {
    throw new Error(`Failed to update application ${id}`);
  }
}

export async function deleteApplicationServer(id: string | number): Promise<void> {
  const response = await fetch(`/api/applications/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete application ${id}`);
  }
}

export async function getApplicationsStatic(): Promise<Application[]> {
  return loadFromLocalStorage();
}

export async function addApplicationStatic(app: Omit<Application, 'id'>): Promise<string | number> {
  const apps = loadFromLocalStorage();
  const id = Date.now();
  const newApp: Application = { ...app, id };
  apps.push(newApp);
  saveToLocalStorage(apps);
  return id;
}

export async function updateApplicationStatic(
  id: string | number,
  patch: Partial<Application>
): Promise<void> {
  const apps = loadFromLocalStorage();
  const idx = apps.findIndex((a) => String(a.id) === String(id));
  if (idx !== -1) {
    apps[idx] = { ...apps[idx], ...patch };
    saveToLocalStorage(apps);
  }
}

export async function deleteApplicationStatic(id: string | number): Promise<void> {
  const apps = loadFromLocalStorage();
  const filtered = apps.filter((a) => String(a.id) !== String(id));
  saveToLocalStorage(filtered);
}

export async function getApplications(): Promise<Application[]> {
  return isStaticMode() ? getApplicationsStatic() : getApplicationsServer();
}

export async function addApplication(app: Omit<Application, 'id'>): Promise<string | number> {
  return isStaticMode() ? addApplicationStatic(app) : addApplicationServer(app);
}

export async function updateApplication(
  id: string | number,
  patch: Partial<Application>
): Promise<void> {
  return isStaticMode() ? updateApplicationStatic(id, patch) : updateApplicationServer(id, patch);
}

export async function deleteApplication(id: string | number): Promise<void> {
  return isStaticMode() ? deleteApplicationStatic(id) : deleteApplicationServer(id);
}
