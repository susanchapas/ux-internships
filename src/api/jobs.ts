import { classifyJob } from '../utils/classify';
import { compileFilterConfig, matchJob } from '../utils/filters';
import { BOARD_FETCHERS, fetchCompanyJobs } from './ats';
import { getStaticConfig, getStaticData, isStaticMode } from './mode';
import type { Job, ScanConfig, ScanEvent } from './types';

export { isStaticMode };

export function staticJobs(): Job[] {
  const data = getStaticData();
  return (data?.jobs ?? []).map((job) => ({ ...job }));
}

/** Subscribe to the unchanged Python SSE endpoint. The returned function closes it. */
export function startServerScan(
  onEvent: (event: ScanEvent) => void,
  onConnectionError: () => void
): () => void {
  const source = new EventSource('/api/scan');
  const eventTypes: ScanEvent['type'][] = ['progress', 'matches', 'scan_error', 'done', 'error'];
  eventTypes.forEach((type) =>
    source.addEventListener(type, (event) => {
      try {
        onEvent({
          type,
          ...JSON.parse((event as MessageEvent<string>).data),
        } as ScanEvent);
      } catch {
        /* ignore malformed events */
      }
    })
  );
  source.onerror = () => onConnectionError();
  return () => source.close();
}

export async function persistHidden(id: string, hidden: boolean): Promise<void> {
  if (isStaticMode()) return;
  await fetch(`/api/hidden/${encodeURIComponent(id)}`, {
    method: hidden ? 'POST' : 'DELETE',
  });
}

export async function scanServer(
  onProgress?: (event: ScanEvent) => void,
  signal?: AbortSignal
): Promise<Job[]> {
  return new Promise<Job[]>((resolve, reject) => {
    const allMatches: Job[] = [];
    let closeSource: (() => void) | null = null;

    const cleanup = () => {
      if (closeSource) {
        closeSource();
        closeSource = null;
      }
      if (signal) {
        signal.removeEventListener('abort', onAbort);
      }
    };

    const onAbort = () => {
      cleanup();
      reject(new DOMException('Scan aborted', 'AbortError'));
    };

    if (signal) {
      if (signal.aborted) {
        onAbort();
        return;
      }
      signal.addEventListener('abort', onAbort);
    }

    closeSource = startServerScan(
      (event) => {
        if (event.type === 'matches') {
          allMatches.push(...event.jobs);
        } else if (event.type === 'done') {
          cleanup();
          onProgress?.(event);
          resolve(allMatches);
          return;
        }
        onProgress?.(event);
      },
      () => {
        cleanup();
        onProgress?.({
          type: 'error',
          error: 'Connection to scan stream failed',
        });
        if (allMatches.length > 0) {
          resolve(allMatches);
        } else {
          reject(new Error('Connection to scan stream failed'));
        }
      }
    );
  });
}

export async function scanStatic(
  onProgress?: (event: ScanEvent) => void,
  signal?: AbortSignal
): Promise<Job[]> {
  const staticData = getStaticData();
  const staticConfig = getStaticConfig();

  const cfg: ScanConfig = staticConfig || {
    title_include: ['intern', 'fellow', 'apprentice', 'co-op', 'design', 'ux', 'product design'],
    location_include: ['united states', 'remote', 'new york', 'ny', 'san francisco', 'ca'],
    companies: [],
  };

  const compiled = compileFilterConfig(cfg);
  const allMatches: Job[] = [];
  const seenIds = new Set<string>();

  // 1. Load prebaked jobs from static data
  if (staticData?.jobs) {
    const prebaked = staticData.jobs.filter((j) => !BOARD_FETCHERS[j.source]);
    for (const job of prebaked) {
      job.is_new = false;
      classifyJob(job);
      if (!seenIds.has(job.id)) {
        seenIds.add(job.id);
        allMatches.push(job);
      }
    }
    if (prebaked.length > 0) {
      onProgress?.({
        type: 'matches',
        company: 'Pre-baked Listings',
        jobs: prebaked,
        matched: prebaked.length,
      });
    }
  }

  const companies = cfg.companies || [];
  let errorCount = (staticData?.errors || []).length;

  // Report pre-existing errors
  for (const err of staticData?.errors || []) {
    onProgress?.({
      type: 'scan_error',
      company: err.company,
      error: err.error,
    });
  }

  // 2. Scan live boards for companies
  for (let i = 0; i < companies.length; i++) {
    if (signal?.aborted) {
      throw new DOMException('Scan aborted', 'AbortError');
    }

    const entry = companies[i];
    const companyName = entry.name || entry.slug || entry.board;

    onProgress?.({
      type: 'progress',
      company: companyName,
      index: i + 1,
      total: companies.length,
    });

    if (!BOARD_FETCHERS[entry.board]) {
      continue;
    }

    try {
      const jobs = await fetchCompanyJobs(entry);
      const hits: Job[] = [];

      for (const j of jobs) {
        if (matchJob(j, compiled)) {
          j.is_new = !seenIds.has(j.id);
          classifyJob(j);
          hits.push(j);
          seenIds.add(j.id);
        }
      }

      if (hits.length > 0) {
        allMatches.push(...hits);
        onProgress?.({
          type: 'matches',
          company: companyName,
          jobs: hits,
          total_open: jobs.length,
          matched: hits.length,
        });
      }
    } catch (e: unknown) {
      errorCount++;
      const msg = e instanceof Error ? e.message : String(e);
      onProgress?.({
        type: 'scan_error',
        company: companyName,
        error: msg,
      });
    }
  }

  onProgress?.({
    type: 'done',
    total_matches: allMatches.length,
    companies_scanned: companies.length,
    errors: errorCount,
  });

  return allMatches;
}

export async function scanJobs(
  onProgress?: (event: ScanEvent) => void,
  signal?: AbortSignal
): Promise<Job[]> {
  return isStaticMode() ? scanStatic(onProgress, signal) : scanServer(onProgress, signal);
}
