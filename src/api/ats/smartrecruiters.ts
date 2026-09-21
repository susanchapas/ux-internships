import type { CompanyEntry, Job } from '../types';

interface SRPostingResponse {
  id: string;
  name?: string;
  location?: { city?: string; region?: string };
  compensation?: { min?: number; max?: number };
  releasedDate?: string;
  jobAd?: string;
  jobAdText?: string;
  description?: string;
}

interface SRPageResponse {
  content?: SRPostingResponse[];
  totalFound?: number;
}

export async function fetchSmartRecruiters(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const out: Job[] = [];
  let offset = 0;
  const limit = 100;

  while (true) {
    const response = await fetch(
      `https://api.smartrecruiters.com/v1/companies/${encodeURIComponent(slug)}/postings?limit=${limit}&offset=${offset}`
    );
    if (!response.ok) {
      throw new Error(`SmartRecruiters API error: ${response.status} ${response.statusText}`);
    }
    const data = (await response.json()) as SRPageResponse;
    const items = data.content || [];

    for (const j of items) {
      const loc = j.location || {};
      const comp = j.compensation || {};
      let pay = '';
      if (comp.min || comp.max) {
        const parts: string[] = [];
        if (comp.min) parts.push(`$${Number(comp.min).toLocaleString()}`);
        if (comp.max) parts.push(`$${Number(comp.max).toLocaleString()}`);
        pay = parts.join(' - ');
      }

      out.push({
        id: `sr:${slug}:${j.id}`,
        title: j.name || '',
        location: [loc.city, loc.region].filter(Boolean).join(', '),
        url: `https://jobs.smartrecruiters.com/${slug}/${j.id}`,
        company: entry.name,
        source: 'smartrecruiters',
        pay,
        description: [j.jobAd, j.jobAdText, j.description].filter(Boolean).join(' '),
        posted_at: j.releasedDate || '',
      });
    }

    offset += limit;
    if (offset >= (data.totalFound || 0) || items.length === 0) {
      break;
    }
  }

  return out;
}
