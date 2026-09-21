import type { CompanyEntry, Job } from '../types';

interface BambooJob {
  id: string | number;
  jobOpeningName?: string;
  location?: { city?: string; state?: string } | string;
}

interface BambooResponse {
  result?: BambooJob[];
}

export async function fetchBambooHR(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const response = await fetch(`https://${encodeURIComponent(slug)}.bamboohr.com/careers/list`);
  if (!response.ok) {
    throw new Error(`BambooHR API error: ${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as BambooResponse;
  const jobs = data.result || [];

  return jobs.map((j) => {
    let loc = '';
    if (typeof j.location === 'object' && j.location !== null) {
      loc = [j.location.city, j.location.state].filter(Boolean).join(', ');
    } else if (typeof j.location === 'string') {
      loc = j.location;
    }

    return {
      id: `bh:${slug}:${j.id}`,
      title: (j.jobOpeningName || '').trim(),
      location: loc,
      url: `https://${slug}.bamboohr.com/careers/${j.id}`,
      company: entry.name,
      source: 'bamboohr',
      pay: '',
    };
  });
}
