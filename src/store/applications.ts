import { create } from 'zustand';
import { getDataSource } from '../api/datasource';
import type { Application, Job } from '../api/types';

interface ApplicationsState {
  items: Application[];
  isLoading: boolean;
  error: string | null;

  loadApplications: () => Promise<void>;
  addApplication: (app: Omit<Application, 'id'>) => Promise<string | number>;
  updateApplication: (
    id: string | number,
    fieldOrPatch: keyof Application | Partial<Application>,
    value?: unknown
  ) => Promise<void>;
  deleteApplication: (id: string | number) => Promise<void>;
  trackJob: (job: Job) => Promise<string | number>;
  isJobTracked: (jobId: string) => boolean;
  setItems: (items: Application[]) => void;
}

export const useApplicationsStore = create<ApplicationsState>((set, get) => ({
  items: [],
  isLoading: false,
  error: null,

  loadApplications: async () => {
    set({ isLoading: true, error: null });
    try {
      const items = await getDataSource().getApplications();
      set({ items, isLoading: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load applications';
      set({ error: msg, isLoading: false });
    }
  },

  addApplication: async (app) => {
    const ds = getDataSource();
    const id = await ds.addApplication(app);
    const newApp: Application = { ...app, id };
    set((state) => ({ items: [...state.items, newApp] }));
    return id;
  },

  updateApplication: async (id, fieldOrPatch, value) => {
    const patch: Partial<Application> =
      typeof fieldOrPatch === 'string'
        ? ({ [fieldOrPatch]: value } as Partial<Application>)
        : fieldOrPatch;

    // Optimistic update
    set((state) => ({
      items: state.items.map((item) =>
        String(item.id) === String(id) ? { ...item, ...patch } : item
      ),
    }));

    try {
      await getDataSource().updateApplication(id, patch);
    } catch (err) {
      console.warn('Failed to update application on data source:', err);
      // reload on failure
      get().loadApplications();
    }
  },

  deleteApplication: async (id) => {
    // Optimistic update
    set((state) => ({
      items: state.items.filter((item) => String(item.id) !== String(id)),
    }));

    try {
      await getDataSource().deleteApplication(id);
    } catch (err) {
      console.warn('Failed to delete application on data source:', err);
      get().loadApplications();
    }
  },

  trackJob: async (job) => {
    const app: Omit<Application, 'id'> = {
      job_id: job.id,
      company: job.company,
      title: job.title,
      url: job.url || '',
      location: job.location || '',
      pay: job.pay || '',
      status: 'saved',
      applied_at: '',
      deadline: '',
      reminder_interval: 'daily',
      notes: '',
    };
    return get().addApplication(app);
  },

  isJobTracked: (jobId: string) => {
    return get().items.some((item) => item.job_id === jobId);
  },

  setItems: (items) => set({ items }),
}));
