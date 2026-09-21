import { create } from 'zustand';
import { cloudSync } from '../api/sync';
import type {
  FilterState,
  SavedFilter,
  ScanFilters,
  UserPreferences,
  VisibleColumns,
} from '../api/types';
import {
  COLUMN_DEFAULTS,
  SCAN_FILTER_DEFAULTS,
  SEARCH_DEFAULTS,
  SYNC_KEYS,
} from '../utils/constants';

interface SortConfig {
  column: string;
  direction: 1 | -1;
}

interface PreferencesState {
  filters: FilterState;
  columns: VisibleColumns;
  savedFilters: SavedFilter[];
  scanFilters: ScanFilters;
  userPrefs: UserPreferences;
  sort: SortConfig;

  setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void;
  resetFilters: () => void;
  setColumnVisibility: (view: 'scanner' | 'tracker', column: string, visible: boolean) => void;
  resetColumns: (view: 'scanner' | 'tracker') => void;
  saveFilterPreset: (name: string) => void;
  loadFilterPreset: (name: string) => void;
  deleteFilterPreset: (name: string) => void;
  setScanFilters: (patch: Partial<ScanFilters>) => void;
  setUserPrefs: (patch: Partial<UserPreferences>) => void;
  setSort: (column: string) => void;
}

const defaultFilterState: FilterState = {
  search: '',
  level: ['intern', 'fellow', 'apprentice', 'entry', 'mid', 'senior+', 'manager+'],
  payType: ['hourly', 'salary'],
  schedule: ['full-time', 'part-time', 'contract'],
  source: [],
  favOnly: false,
  showHidden: false,
};

function loadInitialColumns(): VisibleColumns {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.visibleColumns);
    if (!raw) return { scanner: [...COLUMN_DEFAULTS.scanner], tracker: [...COLUMN_DEFAULTS.tracker] };
    const parsed = JSON.parse(raw) as Partial<VisibleColumns>;
    return {
      scanner: parsed.scanner || [...COLUMN_DEFAULTS.scanner],
      tracker: parsed.tracker || [...COLUMN_DEFAULTS.tracker],
    };
  } catch {
    return { scanner: [...COLUMN_DEFAULTS.scanner], tracker: [...COLUMN_DEFAULTS.tracker] };
  }
}

function loadInitialSavedFilters(): SavedFilter[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.savedFilters);
    return raw ? (JSON.parse(raw) as SavedFilter[]) : [];
  } catch {
    return [];
  }
}

function loadInitialScanFilters(): ScanFilters {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.scanFilters);
    return raw
      ? { ...SCAN_FILTER_DEFAULTS, ...(JSON.parse(raw) as Partial<ScanFilters>) }
      : { ...SCAN_FILTER_DEFAULTS };
  } catch {
    return { ...SCAN_FILTER_DEFAULTS };
  }
}

function loadInitialUserPrefs(): UserPreferences {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.prefs);
    return raw
      ? { ...SEARCH_DEFAULTS, ...(JSON.parse(raw) as Record<string, unknown>) }
      : { ...SEARCH_DEFAULTS };
  } catch {
    return { ...SEARCH_DEFAULTS };
  }
}

export const usePreferencesStore = create<PreferencesState>((set, get) => ({
  filters: defaultFilterState,
  columns: loadInitialColumns(),
  savedFilters: loadInitialSavedFilters(),
  scanFilters: loadInitialScanFilters(),
  userPrefs: loadInitialUserPrefs(),
  sort: { column: 'company', direction: 1 },

  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    }));
  },

  resetFilters: () => {
    set({ filters: defaultFilterState });
  },

  setColumnVisibility: (view, column, visible) => {
    const current = new Set(get().columns[view]);
    if (visible) {
      current.add(column);
    } else {
      current.delete(column);
    }
    const nextColumns = {
      ...get().columns,
      [view]: [...current],
    };
    localStorage.setItem(SYNC_KEYS.visibleColumns, JSON.stringify(nextColumns));
    cloudSync();
    set({ columns: nextColumns });
  },

  resetColumns: (view) => {
    const nextColumns = {
      ...get().columns,
      [view]: [...COLUMN_DEFAULTS[view]],
    };
    localStorage.setItem(SYNC_KEYS.visibleColumns, JSON.stringify(nextColumns));
    cloudSync();
    set({ columns: nextColumns });
  },

  saveFilterPreset: (name: string) => {
    const current = get().savedFilters;
    const currentState = get().filters;
    const existingIdx = current.findIndex((f) => f.name === name);
    const updated = [...current];

    if (existingIdx >= 0) {
      updated[existingIdx] = { name, state: currentState };
    } else {
      updated.push({ name, state: currentState });
    }

    localStorage.setItem(SYNC_KEYS.savedFilters, JSON.stringify(updated));
    cloudSync();
    set({ savedFilters: updated });
  },

  loadFilterPreset: (name: string) => {
    const preset = get().savedFilters.find((f) => f.name === name);
    if (preset) {
      set({ filters: { ...preset.state } });
    }
  },

  deleteFilterPreset: (name: string) => {
    const updated = get().savedFilters.filter((f) => f.name !== name);
    localStorage.setItem(SYNC_KEYS.savedFilters, JSON.stringify(updated));
    cloudSync();
    set({ savedFilters: updated });
  },

  setScanFilters: (patch) => {
    const updated = { ...get().scanFilters, ...patch };
    localStorage.setItem(SYNC_KEYS.scanFilters, JSON.stringify(updated));
    cloudSync();
    set({ scanFilters: updated });
  },

  setUserPrefs: (patch) => {
    const updated = { ...get().userPrefs, ...patch };
    localStorage.setItem(SYNC_KEYS.prefs, JSON.stringify(updated));
    cloudSync();
    set({ userPrefs: updated });
  },

  setSort: (column: string) => {
    const current = get().sort;
    if (current.column === column) {
      set({ sort: { column, direction: current.direction === 1 ? -1 : 1 } });
    } else {
      set({ sort: { column, direction: 1 } });
    }
  },
}));
