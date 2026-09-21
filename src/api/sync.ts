import { doc, getDoc, setDoc } from 'firebase/firestore';
import { SYNC_KEYS } from '../utils/constants';
import { firebaseAuth, firestore } from './auth-firebase';
import { usesFirebaseAuth } from './mode';

let syncTimer: ReturnType<typeof setTimeout> | null = null;
const syncListeners = new Set<() => void>();

export function onCloudDataLoaded(listener: () => void): () => void {
  syncListeners.add(listener);
  return () => {
    syncListeners.delete(listener);
  };
}

function notifyLoaded() {
  for (const listener of syncListeners) {
    listener();
  }
}

function getUserDocRef() {
  const user = firebaseAuth.currentUser;
  if (!user) return null;
  return doc(firestore, 'users', user.uid);
}

export function cloudSync(immediate = false): void {
  if (!usesFirebaseAuth()) return;

  if (syncTimer) {
    clearTimeout(syncTimer);
    syncTimer = null;
  }

  const run = async () => {
    try {
      const ref = getUserDocRef();
      if (!ref) return;

      const data: Record<string, string> = {};
      for (const [k, lsKey] of Object.entries(SYNC_KEYS)) {
        const defaultVal =
          lsKey.includes('renamed') ||
          lsKey.includes('prefs') ||
          lsKey.includes('scan-filters') ||
          lsKey.includes('visible-columns')
            ? '{}'
            : '[]';
        data[k] = localStorage.getItem(lsKey) || defaultVal;
      }
      await setDoc(ref, data, { merge: true });
    } catch (err) {
      console.warn('cloudSync error:', err);
    }
  };

  if (immediate) {
    run();
  } else {
    syncTimer = setTimeout(run, 1500);
  }
}

export async function cloudLoad(): Promise<boolean> {
  if (!usesFirebaseAuth()) return false;

  const ref = getUserDocRef();
  if (!ref) return false;

  try {
    const snap = await getDoc(ref);
    if (!snap.exists()) {
      cloudSync(true);
      return false;
    }

    const d = snap.data() as Record<string, string | undefined>;
    for (const [k, lsKey] of Object.entries(SYNC_KEYS)) {
      const val = d[k];
      if (val !== undefined && val !== null) {
        localStorage.setItem(lsKey, typeof val === 'string' ? val : JSON.stringify(val));
      }
    }
    notifyLoaded();
    return true;
  } catch (err) {
    console.warn('cloudLoad error:', err);
    return false;
  }
}
