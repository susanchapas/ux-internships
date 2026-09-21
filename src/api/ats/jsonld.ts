import type { CompanyEntry, Job } from '../types';

export async function fetchJsonLd(entry: CompanyEntry): Promise<Job[]> {
  if (!entry.url) return [];

  const response = await fetch(entry.url);
  if (!response.ok) {
    throw new Error(`JSON-LD fetch error: ${response.status} ${response.statusText}`);
  }
  const html = await response.text();

  const scriptRegex = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let match: RegExpExecArray | null;
  const blocks: string[] = [];

  while ((match = scriptRegex.exec(html)) !== null) {
    if (match[1]) blocks.push(match[1].trim());
  }

  const out: Job[] = [];

  function walk(value: unknown, cb: (item: Record<string, unknown>) => void) {
    if (Array.isArray(value)) {
      for (const it of value) walk(it, cb);
    } else if (value && typeof value === 'object') {
      const obj = value as Record<string, unknown>;
      if (Array.isArray(obj['@graph'])) {
        walk(obj['@graph'], cb);
      } else {
        cb(obj);
      }
    }
  }

  for (const block of blocks) {
    try {
      const parsed = JSON.parse(block);
      walk(parsed, (job) => {
        const typeStr = String(job['@type'] || '');
        if (!typeStr.includes('JobPosting')) return;

        const title = String(job.title || '');
        const jobUrl = String(job.url || entry.url || '');
        const datePosted = String(job.datePosted || '');

        let locations: unknown[] = [];
        if (Array.isArray(job.jobLocation)) {
          locations = job.jobLocation;
        } else if (job.jobLocation) {
          locations = [job.jobLocation];
        }

        const locationParts: string[] = [];
        for (const loc of locations) {
          if (loc && typeof loc === 'object') {
            const addr = (loc as Record<string, unknown>).address;
            if (addr && typeof addr === 'object') {
              const a = addr as Record<string, unknown>;
              const parts = [a.addressLocality, a.addressRegion, a.addressCountry]
                .filter(Boolean)
                .map(String);
              if (parts.length) locationParts.push(parts.join(', '));
            }
          }
        }
        if (job.jobLocationType === 'TELECOMMUTE') {
          locationParts.push('Remote');
        }

        let salary = '';
        if (job.baseSalary) {
          salary =
            typeof job.baseSalary === 'object'
              ? JSON.stringify(job.baseSalary)
              : String(job.baseSalary);
        }

        // Simple hash of url + title + datePosted
        const key = btoa(encodeURIComponent(`${jobUrl}|${title}|${datePosted}`))
          .replace(/[^a-zA-Z0-9]/g, '')
          .slice(0, 16);

        out.push({
          id: `ld:${key}`,
          title,
          location: locationParts.join('; '),
          url: jobUrl,
          company: entry.name,
          source: 'jsonld',
          pay: salary,
          description: String(job.description || ''),
          posted_at: datePosted,
        });
      });
    } catch {
      // Ignore invalid JSON-LD blocks
    }
  }

  return out;
}
