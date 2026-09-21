import { useEffect } from 'react';
import { usesFirebaseAuth } from '../api/mode';
import { cloudLoad, cloudSync, onCloudDataLoaded } from '../api/sync';
import { useApplicationsStore } from '../store/applications';
import { useAuthStore } from '../store/auth';
import { useCompaniesStore } from '../store/companies';
import { useJobsStore } from '../store/jobs';
import { usePreferencesStore } from '../store/preferences';
import { SYNC_KEYS } from '../utils/constants';

export function useCloudSync() {
  const user = useAuthStore((state) => state.user);
  const setHiddenIds = useJobsStore((state) => state.setHiddenIds);
  const setFavJobIds = useJobsStore((state) => state.setFavJobIds);
  const loadApplications = useApplicationsStore((state) => state.loadApplications);
  const refreshCompanies = useCompaniesStore((state) => state.refreshFromStorage);

  useEffect(() => {
    if (!usesFirebaseAuth() || !user) return;

    // Load from Firestore cloud when user signs in
    cloudLoad().then(() => {
      loadApplications();
    });

    // Listen for cloud load events and rehydrate zustand stores
    const unsubscribe = onCloudDataLoaded(() => {
      try {
        const rawHidden = localStorage.getItem(SYNC_KEYS.hidden);
        if (rawHidden) setHiddenIds(JSON.parse(rawHidden) as string[]);

        const rawFav = localStorage.getItem(SYNC_KEYS.favJobs);
        if (rawFav) setFavJobIds(JSON.parse(rawFav) as string[]);

        const rawCols = localStorage.getItem(SYNC_KEYS.visibleColumns);
        if (rawCols) {
          const parsed = JSON.parse(rawCols);
          usePreferencesStore.setState((prev) => ({
            columns: { ...prev.columns, ...parsed },
          }));
        }

        const rawSavedFilters = localStorage.getItem(SYNC_KEYS.savedFilters);
        if (rawSavedFilters) {
          usePreferencesStore.setState({
            savedFilters: JSON.parse(rawSavedFilters),
          });
        }

        const rawScanFilters = localStorage.getItem(SYNC_KEYS.scanFilters);
        if (rawScanFilters) {
          usePreferencesStore.setState((prev) => ({
            scanFilters: { ...prev.scanFilters, ...JSON.parse(rawScanFilters) },
          }));
        }

        const rawPrefs = localStorage.getItem(SYNC_KEYS.prefs);
        if (rawPrefs) {
          usePreferencesStore.setState((prev) => ({
            userPrefs: { ...prev.userPrefs, ...JSON.parse(rawPrefs) },
          }));
        }

        refreshCompanies();
        loadApplications();
      } catch (err) {
        console.warn('Error rehydrating stores from cloud load:', err);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [user, setHiddenIds, setFavJobIds, loadApplications, refreshCompanies]);

  return {
    syncNow: (immediate = true) => cloudSync(immediate),
    reloadCloud: () => cloudLoad(),
  };
}
