import { extractPay } from '../../utils/classify';
import type { CompanyEntry, Job } from '../types';

export async function fetchHydrationJobs(entry: CompanyEntry): Promise<Job[]> {
  if (!entry.url) return [];

  const response = await fetch(entry.url);
  if (!response.ok) {
    throw new Error(`Hydration fetch error: ${response.status} ${response.statusText}`);
  }
  const html = await response.text();

  const match = /<script[^>]*id=["']__NEXT_DATA__["'][^>]*>([\s\S]*?)<\/script>/i.exec(html);
  if (!match || !match[1]) return [];

  let payload: unknown;
  try {
    payload = JSON.parse(match[1].trim());
  } catch {
    return [];
  }

  const out: Job[] = [];
  const seen = new Set<string>();

  function walk(value: unknown) {
    if (!value || typeof value !== 'object') return;

    if (Array.isArray(value)) {
      for (const item of value) walk(item);
      return;
    }

    const obj = value as Record<string, unknown>;
    const title = obj.title || obj.name || obj.text;
    const path =
      obj.absolute_url ||
      obj.absoluteUrl ||
      obj.jobUrl ||
      obj.url ||
      obj.externalPath;
    const identifier = obj.id || obj.jobId || path;

    if (
      typeof title === 'string' &&
      title.trim() &&
      identifier &&
      path &&
      typeof path === 'string'
    ) {
      let jobUrl = path;
      try {
        jobUrl = new URL(path, entry.url).toString();
      } catch {
        // keep path
      }

      const key = `hydr:${btoa(encodeURIComponent(String(identifier))).replace(/[^a-zA-Z0-9]/g, '').slice(0, 16)}`;
      if (!seen.has(key)) {
        seen.add(key);
        const location = obj.location || obj.locationsText || '';
        const description = obj.description || obj.descriptionHtml || '';

        out.push({
          id: key,
          title: title.trim(),
          location: String(location),
          url: jobUrl,
          company: entry.name,
          source: 'hydration',
          description: String(description),
          pay: extractPay(String(description)),
          posted_at: String(obj.datePosted || obj.postedOn || ''),
        });
      }
    }

    for (const child of Object.values(obj)) {
      walk(child);
    }
  }

  walk(payload);
  return out;
}
