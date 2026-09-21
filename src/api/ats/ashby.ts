import { extractPay } from '../../utils/classify';
import type { CompanyEntry, Job } from '../types';

interface AshbyJobResponse {
  id: string;
  title?: string;
  location?: string;
  jobUrl?: string;
  descriptionHtml?: string;
  description?: string;
  compensationTierSummary?: string;
  publishedAt?: string;
  employmentType?: string;
}

export async function fetchAshby(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const response = await fetch(
    `https://api.ashbyhq.com/posting-api/job-board/${encodeURIComponent(slug)}`
  );
  if (!response.ok) {
    throw new Error(`Ashby API error: ${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { jobs?: AshbyJobResponse[] };
  const jobs = data.jobs || [];

  return jobs.map((j) => {
    const desc = j.descriptionHtml || j.description || '';
    const comp = j.compensationTierSummary || '';
    return {
      id: `ab:${slug}:${j.id}`,
      title: j.title || '',
      location: j.location || '',
      url: j.jobUrl || '',
      company: entry.name,
      source: 'ashby',
      pay: comp || extractPay(desc),
      description: desc,
      posted_at: j.publishedAt || '',
      employment_type: j.employmentType || '',
    };
  });
}

export async function fetchAshbyJob(slug: string, jobId: string): Promise<Partial<Job>> {
  const response = await fetch(
    `https://api.ashbyhq.com/posting-api/job-board/${encodeURIComponent(slug)}`
  );
  if (!response.ok) {
    throw new Error('Board not found on Ashby');
  }
  const data = (await response.json()) as { jobs?: AshbyJobResponse[] };
  const j = (data.jobs || []).find((job) => job.id === jobId);
  if (!j) {
    throw new Error('Job not found on Ashby board');
  }

  const desc = j.descriptionHtml || j.description || '';
  const comp = j.compensationTierSummary || '';
  return {
    title: j.title || '',
    location: j.location || '',
    pay: comp || extractPay(desc),
    url: j.jobUrl || '',
  };
}
