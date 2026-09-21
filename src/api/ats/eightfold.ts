import type { CompanyEntry, Job } from '../types';

interface EightfoldPosition {
  id: string | number;
  name?: string;
  locations?: string[];
  location?: string;
  canonicalPositionUrl?: string;
}

interface EightfoldResponse {
  positions?: EightfoldPosition[];
}

export async function fetchEightfold(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const domain = entry.domain || `${slug}.com`;
  const url = `https://${encodeURIComponent(slug)}.eightfold.ai/api/apply/v2/jobs?domain=${encodeURIComponent(domain)}&start=0&num=100&sort_by=relevance`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Eightfold API error: ${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as EightfoldResponse;
  const positions = data.positions || [];

  return positions.map((j) => {
    const locs = j.locations || [j.location || ''];
    return {
      id: `ef:${slug}:${j.id}`,
      title: j.name || '',
      location: locs.filter(Boolean).join('; '),
      url: j.canonicalPositionUrl || '',
      company: entry.name,
      source: 'eightfold',
      pay: '',
    };
  });
}
