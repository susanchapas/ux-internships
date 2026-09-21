import { SYNC_KEYS } from '../utils/constants';
import {
  addApplicationServer,
  addApplicationStatic,
  deleteApplicationServer,
  deleteApplicationStatic,
  getApplicationsServer,
  getApplicationsStatic,
  updateApplicationServer,
  updateApplicationStatic,
} from './applications';
import { scanServer, scanStatic } from './jobs';
import { isStaticMode } from './mode';
import { cloudSync } from './sync';
import type { Application, DataSource, Job, ScanEvent } from './types';

export class ServerDataSource implements DataSource {
  async scan(onProgress?: (event: ScanEvent) => void, signal?: AbortSignal): Promise<Job[]> {
    return scanServer(onProgress, signal);
  }

  async getApplications(): Promise<Application[]> {
    return getApplicationsServer();
  }

  async addApplication(app: Omit<Application, 'id'>): Promise<string | number> {
    return addApplicationServer(app);
  }

  async updateApplication(id: string | number, patch: Partial<Application>): Promise<void> {
    return updateApplicationServer(id, patch);
  }

  async deleteApplication(id: string | number): Promise<void> {
    return deleteApplicationServer(id);
  }

  async hideJob(id: string): Promise<void> {
    const response = await fetch(`/api/hidden/${encodeURIComponent(id)}`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to hide job ${id}`);
    }
  }

  async unhideJob(id: string): Promise<void> {
    const response = await fetch(`/api/hidden/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to unhide job ${id}`);
    }
  }

  async getHiddenIds(): Promise<string[]> {
    const response = await fetch('/api/hidden');
    if (!response.ok) {
      throw new Error('Failed to get hidden job IDs');
    }
    return (await response.json()) as string[];
  }
}

export class StaticDataSource implements DataSource {
  private _getHiddenSet(): Set<string> {
    try {
      const raw = localStorage.getItem(SYNC_KEYS.hidden);
      return new Set(raw ? (JSON.parse(raw) as string[]) : []);
    } catch {
      return new Set();
    }
  }

  private _saveHiddenSet(set: Set<string>): void {
    localStorage.setItem(SYNC_KEYS.hidden, JSON.stringify([...set]));
    cloudSync();
  }

  async scan(onProgress?: (event: ScanEvent) => void, signal?: AbortSignal): Promise<Job[]> {
    return scanStatic(onProgress, signal);
  }

  async getApplications(): Promise<Application[]> {
    return getApplicationsStatic();
  }

  async addApplication(app: Omit<Application, 'id'>): Promise<string | number> {
    return addApplicationStatic(app);
  }

  async updateApplication(id: string | number, patch: Partial<Application>): Promise<void> {
    return updateApplicationStatic(id, patch);
  }

  async deleteApplication(id: string | number): Promise<void> {
    return deleteApplicationStatic(id);
  }

  async hideJob(id: string): Promise<void> {
    const set = this._getHiddenSet();
    set.add(id);
    this._saveHiddenSet(set);
  }

  async unhideJob(id: string): Promise<void> {
    const set = this._getHiddenSet();
    set.delete(id);
    this._saveHiddenSet(set);
  }

  async getHiddenIds(): Promise<string[]> {
    return [...this._getHiddenSet()];
  }
}

export const serverDataSource = new ServerDataSource();
export const staticDataSource = new StaticDataSource();

export function getDataSource(): DataSource {
  return isStaticMode() ? staticDataSource : serverDataSource;
}
