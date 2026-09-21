import { create } from 'zustand';
import { cloudSync } from '../api/sync';
import type { CompanyEntry } from '../api/types';
import { SYNC_KEYS } from '../utils/constants';

interface CompaniesState {
  favEmployers: string[];
  hiddenCompanies: string[];
  addedCompanies: CompanyEntry[];
  renamedCompanies: Record<string, string>;
  removedCompanies: string[];

  toggleFavEmployer: (name: string) => void;
  hideCompany: (name: string) => void;
  unhideCompany: (name: string) => void;
  addCompany: (entry: CompanyEntry) => void;
  removeCompany: (name: string) => void;
  renameCompany: (oldName: string, newName: string) => void;
  resetCompanyOverrides: () => void;
  refreshFromStorage: () => void;
}

function loadInitialFavEmployers(): string[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.favEmployers);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function loadInitialHiddenCompanies(): string[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.hiddenCompanies);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function loadInitialAddedCompanies(): CompanyEntry[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.addedCompanies);
    return raw ? (JSON.parse(raw) as CompanyEntry[]) : [];
  } catch {
    return [];
  }
}

function loadInitialRenamedCompanies(): Record<string, string> {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.renamedCompanies);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

function loadInitialRemovedCompanies(): string[] {
  try {
    const raw = localStorage.getItem(SYNC_KEYS.removedCompanies);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export const useCompaniesStore = create<CompaniesState>((set, get) => ({
  favEmployers: loadInitialFavEmployers(),
  hiddenCompanies: loadInitialHiddenCompanies(),
  addedCompanies: loadInitialAddedCompanies(),
  renamedCompanies: loadInitialRenamedCompanies(),
  removedCompanies: loadInitialRemovedCompanies(),

  toggleFavEmployer: (name: string) => {
    const current = new Set(get().favEmployers);
    if (current.has(name)) {
      current.delete(name);
    } else {
      current.add(name);
    }
    const next = [...current];
    localStorage.setItem(SYNC_KEYS.favEmployers, JSON.stringify(next));
    cloudSync();
    set({ favEmployers: next });
  },

  hideCompany: (name: string) => {
    const current = new Set(get().hiddenCompanies);
    current.add(name);
    const next = [...current];
    localStorage.setItem(SYNC_KEYS.hiddenCompanies, JSON.stringify(next));
    cloudSync();
    set({ hiddenCompanies: next });
  },

  unhideCompany: (name: string) => {
    const current = new Set(get().hiddenCompanies);
    current.delete(name);
    const next = [...current];
    localStorage.setItem(SYNC_KEYS.hiddenCompanies, JSON.stringify(next));
    cloudSync();
    set({ hiddenCompanies: next });
  },

  addCompany: (entry: CompanyEntry) => {
    const current = get().addedCompanies;
    const next = [...current, entry];
    localStorage.setItem(SYNC_KEYS.addedCompanies, JSON.stringify(next));
    cloudSync();
    set({ addedCompanies: next });
  },

  removeCompany: (name: string) => {
    const current = new Set(get().removedCompanies);
    current.add(name);
    const next = [...current];
    localStorage.setItem(SYNC_KEYS.removedCompanies, JSON.stringify(next));
    cloudSync();
    set({ removedCompanies: next });
  },

  renameCompany: (oldName: string, newName: string) => {
    const current = { ...get().renamedCompanies, [oldName]: newName };
    localStorage.setItem(SYNC_KEYS.renamedCompanies, JSON.stringify(current));
    cloudSync();
    set({ renamedCompanies: current });
  },

  resetCompanyOverrides: () => {
    localStorage.setItem(SYNC_KEYS.hiddenCompanies, JSON.stringify([]));
    localStorage.setItem(SYNC_KEYS.addedCompanies, JSON.stringify([]));
    localStorage.setItem(SYNC_KEYS.renamedCompanies, JSON.stringify({}));
    localStorage.setItem(SYNC_KEYS.removedCompanies, JSON.stringify([]));
    cloudSync();
    set({
      hiddenCompanies: [],
      addedCompanies: [],
      renamedCompanies: {},
      removedCompanies: [],
    });
  },

  refreshFromStorage: () => {
    set({
      favEmployers: loadInitialFavEmployers(),
      hiddenCompanies: loadInitialHiddenCompanies(),
      addedCompanies: loadInitialAddedCompanies(),
      renamedCompanies: loadInitialRenamedCompanies(),
      removedCompanies: loadInitialRemovedCompanies(),
    });
  },
}));
