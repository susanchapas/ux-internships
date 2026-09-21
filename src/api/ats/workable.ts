import type { CompanyEntry, Job } from '../types';

interface WorkableJob {
  shortcode: string;
  title?: string;
  city?: string;
  state?: string;
  country?: string;
  url?: string;
  application_url?: string;
}

interface WorkableResponse {
  jobs?: WorkableJob[];
}

export async function fetchWorkable(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const response = await fetch(
    `https://apply.workable.com/api/v1/widget/accounts/${encodeURIComponent(slug)}?details=true`
  );
  if (!response.ok) {
    throw new Error(`Workable API error: ${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as WorkableResponse;
  const jobs = data.jobs || [];

  return jobs.map((j) => {
    const loc = [j.city, j.state || j.country].filter(Boolean).join(', ');
    return {
      id: `wk:${slug}:${j.shortcode}`,
      title: j.title || '',
      location: loc,
      url: j.url || j.application_url || '',
      company: entry.name,
      source: 'workable',
      pay: '',
    };
  });
}
