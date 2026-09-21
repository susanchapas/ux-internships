import { create } from 'zustand';
import { getDataSource } from '../api/datasource';
import { isStaticMode } from '../api/mode';
import { cloudSync } from '../api/sync';
import type { Job } from '../api/types';
import { SYNC_KEYS } from '../utils/constants';

interface ScanState {
  isScanning: boolean;
  progressPercent: number;
  currentCompany: string;
  companiesScanned: number;
  totalCompanies: number;
  scanErrors: Array<{ company: string; error: string }>;
  statusMessage?: string;
}

interface JobsState {
  allJobs: Job[];
  hiddenIds: string[];
  favJobIds: string[];
  scanState: ScanState;

  setAllJobs: (jobs: Job[]) => void;
  addJobs: (jobs: Job[]) => void;
  toggleFavJob: (id: string) => void;
  toggleHideJob: (id: string) => Promise<void>;
  setHiddenIds: (ids: string[]) => void;
  setFavJobIds: (ids: string[]) => void;
  loadHiddenIds: () => Promise<void>;

  startScan: (totalCompanies?: number) => void;
  updateScanProgress: (company: string, index: number, total: number) => void;
  addScanError: (company: string, error: string) => void;
  finishScan: (totalMatches?: number, companiesScanned?: number, errors?: number) => void;
  cancelScan: () => void;
  resetScan: () => void;
}

function loadInitialHidden(): string[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.hidden);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function loadInitialFavJobs(): string[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.favJobs);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

const initialScanState: ScanState = {
  isScanning: false,
  progressPercent: 0,
  currentCompany: '',
  companiesScanned: 0,
  totalCompanies: 0,
  scanErrors: [],
  statusMessage: '',
};

export const useJobsStore = create<JobsState>((set, get) => ({
  allJobs: [],
  hiddenIds: loadInitialHidden(),
  favJobIds: loadInitialFavJobs(),
  scanState: initialScanState,

  setAllJobs: (jobs) => set({ allJobs: jobs }),

  addJobs: (newJobs) => {
    const current = get().allJobs;
    const existingIds = new Set(current.map((j) => j.id));
    const toAdd = newJobs.filter((j) => !existingIds.has(j.id));
    if (toAdd.length > 0) {
      set({ allJobs: [...current, ...toAdd] });
    }
  },

  toggleFavJob: (id: string) => {
    const current = new Set(get().favJobIds);
    if (current.has(id)) {
      current.delete(id);
    } else {
      current.add(id);
    }
    const nextArr = [...current];
    localStorage.setItem(SYNC_KEYS.favJobs, JSON.stringify(nextArr));
    cloudSync();
    set({ favJobIds: nextArr });
  },

  toggleHideJob: async (id: string) => {
    const current = new Set(get().hiddenIds);
    const isCurrentlyHidden = current.has(id);

    if (isCurrentlyHidden) {
      current.delete(id);
    } else {
      current.add(id);
    }

    const nextArr = [...current];
    localStorage.setItem(SYNC_KEYS.hidden, JSON.stringify(nextArr));
    cloudSync();
    set({ hiddenIds: nextArr });

    if (!isStaticMode()) {
      try {
        const ds = getDataSource();
        if (isCurrentlyHidden) {
          await ds.unhideJob(id);
        } else {
          await ds.hideJob(id);
        }
      } catch (err) {
        console.warn('Failed to persist hide on server:', err);
      }
    }
  },

  setHiddenIds: (ids: string[]) => {
    localStorage.setItem(SYNC_KEYS.hidden, JSON.stringify(ids));
    set({ hiddenIds: ids });
  },

  setFavJobIds: (ids: string[]) => {
    localStorage.setItem(SYNC_KEYS.favJobs, JSON.stringify(ids));
    set({ favJobIds: ids });
  },

  loadHiddenIds: async () => {
    try {
      const ids = await getDataSource().getHiddenIds();
      localStorage.setItem(SYNC_KEYS.hidden, JSON.stringify(ids));
      set({ hiddenIds: ids });
    } catch (err) {
      // Keep the migrated local value available if the server is offline.
      console.warn('Failed to load hidden jobs from data source:', err);
    }
  },

  startScan: (totalCompanies = 0) =>
    set({
      scanState: {
        isScanning: true,
        progressPercent: 0,
        currentCompany: '',
        companiesScanned: 0,
        totalCompanies,
        scanErrors: [],
        statusMessage: 'Starting scan…',
      },
      allJobs: [],
    }),

  updateScanProgress: (company, index, total) => {
    const pct = total > 0 ? Math.round((index / total) * 100) : 0;
    set((state) => ({
      scanState: {
        ...state.scanState,
        progressPercent: pct,
        currentCompany: company,
        companiesScanned: index,
        totalCompanies: total,
        statusMessage: `Scanning ${company}… (${index}/${total})`,
      },
    }));
  },

  addScanError: (company, error) =>
    set((state) => ({
      scanState: {
        ...state.scanState,
        scanErrors: [...state.scanState.scanErrors, { company, error }],
      },
    })),

  finishScan: (totalMatches, companiesScanned, errors) =>
    set((state) => ({
      scanState: {
        ...state.scanState,
        isScanning: false,
        progressPercent: 100,
        statusMessage: `Done — ${totalMatches ?? state.allJobs.length} matches across ${companiesScanned ?? state.scanState.companiesScanned} companies`,
        companiesScanned: companiesScanned ?? state.scanState.companiesScanned,
        scanErrors:
          errors !== undefined && errors === 0
            ? []
            : state.scanState.scanErrors,
      },
    })),

  cancelScan: () =>
    set((state) => ({
      scanState: {
        ...state.scanState,
        isScanning: false,
        statusMessage: 'Scan cancelled',
      },
    })),

  resetScan: () =>
    set({
      scanState: initialScanState,
    }),
}));
