import type { CompanyEntry, Job } from '../types';

interface RecruiteeOffer {
  id: string | number;
  title?: string;
  location?: string;
  careers_url?: string;
  careers_apply_url?: string;
}

interface RecruiteeResponse {
  offers?: RecruiteeOffer[];
}

export async function fetchRecruitee(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const response = await fetch(`https://${encodeURIComponent(slug)}.recruitee.com/api/offers/`);
  if (!response.ok) {
    throw new Error(`Recruitee API error: ${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as RecruiteeResponse;
  const offers = data.offers || [];

  return offers.map((j) => ({
    id: `rc:${slug}:${j.id}`,
    title: j.title || '',
    location: j.location || '',
    url: j.careers_url || j.careers_apply_url || '',
    company: entry.name,
    source: 'recruitee',
    pay: '',
  }));
}
