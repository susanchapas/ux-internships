import { extractPay } from '../../utils/classify';
import type { CompanyEntry, Job } from '../types';

interface GreenhouseJobResponse {
  id: number | string;
  title?: string;
  location?: { name?: string };
  absolute_url?: string;
  content?: string;
  updated_at?: string;
}

export async function fetchGreenhouse(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const response = await fetch(
    `https://boards-api.greenhouse.io/v1/boards/${encodeURIComponent(slug)}/jobs?content=true`
  );
  if (!response.ok) {
    throw new Error(`Greenhouse API error: ${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { jobs?: GreenhouseJobResponse[] };
  const jobs = data.jobs || [];

  return jobs.map((j) => ({
    id: `gh:${slug}:${j.id}`,
    title: j.title || '',
    location: j.location?.name || '',
    url: j.absolute_url || '',
    company: entry.name,
    source: 'greenhouse',
    pay: extractPay(j.content || ''),
    description: j.content || '',
    posted_at: j.updated_at || '',
  }));
}

export async function fetchGreenhouseJob(slug: string, jobId: string): Promise<Partial<Job>> {
  const response = await fetch(
    `https://boards-api.greenhouse.io/v1/boards/${encodeURIComponent(slug)}/jobs/${encodeURIComponent(jobId)}?content=true`
  );
  if (!response.ok) {
    throw new Error('Job not found on Greenhouse');
  }
  const j = (await response.json()) as GreenhouseJobResponse;
  return {
    title: j.title || '',
    location: j.location?.name || '',
    pay: extractPay(j.content || ''),
    url: j.absolute_url || '',
  };
}
