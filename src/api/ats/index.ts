import type { CompanyEntry, Job } from '../types';
import { fetchAshby, fetchAshbyJob } from './ashby';
import { fetchBambooHR } from './bamboohr';
import { fetchEightfold } from './eightfold';
import { fetchGreenhouse, fetchGreenhouseJob } from './greenhouse';
import { fetchHydrationJobs } from './hydration';
import { fetchJsonLd } from './jsonld';
import { fetchLever, fetchLeverJob } from './lever';
import { fetchRecruitee } from './recruitee';
import { fetchSmartRecruiters } from './smartrecruiters';
import { fetchUSAJobs } from './usajobs';
import { fetchWorkable } from './workable';
import { fetchWorkday } from './workday';

export {
  fetchGreenhouse,
  fetchGreenhouseJob,
  fetchLever,
  fetchLeverJob,
  fetchAshby,
  fetchAshbyJob,
  fetchSmartRecruiters,
  fetchWorkday,
  fetchUSAJobs,
  fetchWorkable,
  fetchBambooHR,
  fetchRecruitee,
  fetchEightfold,
  fetchJsonLd,
  fetchHydrationJobs,
};

export const BOARD_FETCHERS: Record<string, (entry: CompanyEntry) => Promise<Job[]>> = {
  greenhouse: fetchGreenhouse,
  lever: fetchLever,
  ashby: fetchAshby,
  smartrecruiters: fetchSmartRecruiters,
  workday: fetchWorkday,
  usajobs: fetchUSAJobs,
  workable: fetchWorkable,
  bamboohr: fetchBambooHR,
  recruitee: fetchRecruitee,
  eightfold: fetchEightfold,
  jsonld: async (entry) => {
    const jobs = await fetchJsonLd(entry);
    if (jobs.length > 0) return jobs;
    return fetchHydrationJobs(entry);
  },
  hydration: fetchHydrationJobs,
};

export async function fetchCompanyJobs(entry: CompanyEntry): Promise<Job[]> {
  const fetcher = BOARD_FETCHERS[entry.board];
  if (!fetcher) return [];
  return fetcher(entry);
}

export interface ParsedJobUrl {
  board: 'greenhouse' | 'lever' | 'ashby';
  slug: string;
  jobId: string;
}

export function parseJobUrl(url: string): ParsedJobUrl | null {
  try {
    const u = new URL(url);
    const host = u.hostname;
    const path = u.pathname.replace(/\/$/, '');
    if (host.endsWith('greenhouse.io')) {
      const m = path.match(/\/([^/]+)\/jobs\/(\d+)/);
      if (m && m[1] && m[2]) return { board: 'greenhouse', slug: m[1], jobId: m[2] };
    }
    if (host === 'jobs.lever.co') {
      const segs = path.split('/').filter(Boolean);
      if (segs.length >= 2 && segs[0] && segs[1]) return { board: 'lever', slug: segs[0], jobId: segs[1] };
    }
    if (host === 'jobs.ashbyhq.com') {
      const segs = path.split('/').filter(Boolean);
      if (segs.length >= 2 && segs[0] && segs[1]) return { board: 'ashby', slug: segs[0], jobId: segs[1] };
    }
    return null;
  } catch {
    return null;
  }
}

export function resolveCompanyName(board: string, slug: string, companies?: CompanyEntry[]): string {
  if (companies) {
    const entry = companies.find(
      (c) => c.board === board && (c.slug === slug || c.tenant === slug)
    );
    if (entry) return entry.name;
  }
  return slug.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export async function fetchSingleJobFromUrl(
  url: string,
  companies?: CompanyEntry[]
): Promise<Partial<Job>> {
  const parsed = parseJobUrl(url);
  if (!parsed) {
    throw new Error('Unsupported or unrecognized job URL');
  }

  const company = resolveCompanyName(parsed.board, parsed.slug, companies);

  if (parsed.board === 'greenhouse') {
    const job = await fetchGreenhouseJob(parsed.slug, parsed.jobId);
    return { ...job, company };
  }
  if (parsed.board === 'lever') {
    const job = await fetchLeverJob(parsed.slug, parsed.jobId);
    return { ...job, company };
  }
  if (parsed.board === 'ashby') {
    const job = await fetchAshbyJob(parsed.slug, parsed.jobId);
    return { ...job, company };
  }

  throw new Error(`Auto-fill not supported for board: ${parsed.board}`);
}
