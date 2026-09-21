import { useCallback, useRef } from 'react';
import { scanJobs } from '../api/jobs';
import { useJobsStore } from '../store/jobs';

export function useSSE() {
  const abortControllerRef = useRef<AbortController | null>(null);

  const startScan = useJobsStore((state) => state.startScan);
  const updateScanProgress = useJobsStore((state) => state.updateScanProgress);
  const addJobs = useJobsStore((state) => state.addJobs);
  const addScanError = useJobsStore((state) => state.addScanError);
  const finishScan = useJobsStore((state) => state.finishScan);
  const cancelScan = useJobsStore((state) => state.cancelScan);
  const scanState = useJobsStore((state) => state.scanState);

  const start = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    startScan();

    try {
      await scanJobs((event) => {
        if (event.type === 'progress') {
          updateScanProgress(event.company, event.index, event.total);
        } else if (event.type === 'matches') {
          addJobs(event.jobs);
        } else if (event.type === 'scan_error') {
          addScanError(event.company, event.error);
        } else if (event.type === 'done') {
          finishScan(event.total_matches, event.companies_scanned, event.errors);
        } else if (event.type === 'error') {
          addScanError(event.company || 'Scanner', event.error);
        }
      }, controller.signal);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        cancelScan();
      } else {
        const msg = err instanceof Error ? err.message : String(err);
        addScanError('Scanner', msg);
        finishScan();
      }
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
  }, [addJobs, addScanError, cancelScan, finishScan, startScan, updateScanProgress]);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    cancelScan();
  }, [cancelScan]);

  return {
    start,
    abort,
    scanState,
    isScanning: scanState.isScanning,
  };
}
