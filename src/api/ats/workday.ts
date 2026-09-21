import type { CompanyEntry, Job } from '../types';

interface WorkdayPosting {
  externalPath?: string;
  title?: string;
  locationsText?: string;
  compensationAmount?: string | number;
  salaryAmount?: string | number;
  bulletFields?: string[];
  externalDescription?: string;
  jobDescription?: string;
  postedOn?: string;
}

interface WorkdayResponse {
  jobPostings?: WorkdayPosting[];
  total?: number;
}

export async function fetchWorkday(entry: CompanyEntry): Promise<Job[]> {
  const tenant = entry.tenant || entry.slug || '';
  const wd = entry.wd || 5;
  const site = entry.site || 'External';
  const base = `https://${tenant}.wd${wd}.myworkdayjobs.com`;
  const endpoint = `${base}/wday/cxs/${tenant}/${site}/jobs`;

  const searchTerms = entry.search_terms || [
    entry.search || 'intern',
    'co-op',
    'fellowship',
    'apprentice',
    'trainee',
    'placement',
    'extern',
    'residency',
    'student',
  ];

  const uniqueQueries = [...new Set(searchTerms.filter(Boolean))];
  const emitted = new Set<string>();
  const out: Job[] = [];

  for (const query of uniqueQueries) {
    let offset = 0;
    while (true) {
      const body = {
        appliedFacets: {},
        limit: 20,
        offset,
        searchText: query,
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`Workday API error: ${response.status} ${response.statusText}`);
      }

      const data = (await response.json()) as WorkdayResponse;
      const posts = data.jobPostings || [];

      for (const j of posts) {
        const path = j.externalPath || '';
        if (!path || emitted.has(path)) continue;
        emitted.add(path);

        const sal = j.compensationAmount || j.salaryAmount || '';
        const pay = sal ? String(sal) : '';
        const descParts = [
          Array.isArray(j.bulletFields) ? j.bulletFields.join(' ') : '',
          j.externalDescription || '',
          j.jobDescription || '',
        ]
          .filter(Boolean)
          .join(' ');

        out.push({
          id: `wd:${tenant}:${path}`,
          title: j.title || '',
          location: j.locationsText || '',
          url: `${base}/en-US/${site}${path}`,
          company: entry.name,
          source: 'workday',
          pay,
          description: descParts,
          posted_at: j.postedOn || '',
        });
      }

      offset += 20;
      if (offset >= (data.total || 0) || posts.length === 0) {
        break;
      }
    }
  }

  return out;
}
