import { extractPay } from '../../utils/classify';
import type { CompanyEntry, Job } from '../types';

interface LeverPostingResponse {
  id: string;
  text?: string;
  categories?: {
    location?: string;
    commitment?: string;
  };
  hostedUrl?: string;
  descriptionPlain?: string;
  additionalPlain?: string;
  openingPlain?: string;
  lists?: Array<{ content?: string }>;
  createdAt?: number;
}

export async function fetchLever(entry: CompanyEntry): Promise<Job[]> {
  const slug = entry.slug || entry.name.toLowerCase().replace(/\s+/g, '-');
  const response = await fetch(
    `https://api.lever.co/v0/postings/${encodeURIComponent(slug)}?mode=json`
  );
  if (!response.ok) {
    throw new Error(`Lever API error: ${response.status} ${response.statusText}`);
  }
  const postings = (await response.json()) as LeverPostingResponse[];

  return postings.map((j) => {
    const cats = j.categories || {};
    let textBlob = [j.descriptionPlain, j.additionalPlain, j.openingPlain]
      .filter(Boolean)
      .join(' ');
    (j.lists || []).forEach((s) => {
      if (typeof s.content === 'string') {
        textBlob += ' ' + s.content;
      }
    });

    return {
      id: `lv:${slug}:${j.id}`,
      title: j.text || '',
      location: cats.location || '',
      url: j.hostedUrl || '',
      company: entry.name,
      source: 'lever',
      pay: extractPay(textBlob),
      description: textBlob,
      posted_at: j.createdAt ? new Date(j.createdAt).toISOString() : '',
      commitment: cats.commitment || '',
    };
  });
}

export async function fetchLeverJob(slug: string, jobId: string): Promise<Partial<Job>> {
  const response = await fetch(
    `https://api.lever.co/v0/postings/${encodeURIComponent(slug)}/${encodeURIComponent(jobId)}`
  );
  if (!response.ok) {
    throw new Error('Job not found on Lever');
  }
  const j = (await response.json()) as LeverPostingResponse;
  const cats = j.categories || {};
  let textBlob = [j.descriptionPlain, j.additionalPlain, j.openingPlain]
    .filter(Boolean)
    .join(' ');
  (j.lists || []).forEach((s) => {
    if (typeof s.content === 'string') textBlob += ' ' + s.content;
  });

  return {
    title: j.text || '',
    location: cats.location || '',
    pay: extractPay(textBlob),
    url: j.hostedUrl || '',
  };
}
