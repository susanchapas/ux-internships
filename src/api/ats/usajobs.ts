import type { CompanyEntry, Job } from '../types';

interface USAJobsRemuneration {
  MinimumRange?: string;
  MaximumRange?: string;
  Description?: string;
}

interface USAJobsMatchedObject {
  PositionID?: string;
  PositionTitle?: string;
  PositionLocation?: Array<{ LocationName?: string }>;
  PositionRemuneration?: USAJobsRemuneration[];
  PositionURI?: string;
  OrganizationName?: string;
  PublicationStartDate?: string;
}

interface USAJobsResponse {
  SearchResult?: {
    SearchResultItems?: Array<{
      MatchedObjectDescriptor?: USAJobsMatchedObject;
    }>;
  };
}

export async function fetchUSAJobs(entry: CompanyEntry): Promise<Job[]> {
  const apiKey = (import.meta.env?.VITE_USAJOBS_API_KEY as string | undefined) || '';
  const email = (import.meta.env?.VITE_USAJOBS_EMAIL as string | undefined) || '';

  if (!apiKey || !email) {
    // Graceful skip when API keys are not set in the client
    return [];
  }

  const locations = entry.locations || ['New York, New York', 'Newark, New Jersey'];
  const keyword = entry.keyword || entry.search || 'intern';
  const out: Job[] = [];

  for (const loc of locations) {
    const params = new URLSearchParams({
      Keyword: keyword,
      LocationName: loc,
      ResultsPerPage: '100',
    });

    const response = await fetch(`https://data.usajobs.gov/api/search?${params.toString()}`, {
      headers: {
        'Authorization-Key': apiKey,
        'User-Agent': email,
      },
    });

    if (!response.ok) {
      throw new Error(`USAJOBS API error: ${response.status} ${response.statusText}`);
    }

    const data = (await response.json()) as USAJobsResponse;
    const items = data.SearchResult?.SearchResultItems || [];

    for (const it of items) {
      const d = it.MatchedObjectDescriptor || {};
      const locs = d.PositionLocation || [{}];
      const sal = d.PositionRemuneration?.[0];
      let pay = '';
      if (sal) {
        const mn = sal.MinimumRange;
        const mx = sal.MaximumRange;
        const desc = sal.Description || '';
        if (mn) {
          pay = `$${parseFloat(mn).toLocaleString()}`;
          if (mx && mx !== mn) {
            pay += ` - $${parseFloat(mx).toLocaleString()}`;
          }
          if (desc) {
            pay += ` ${desc}`;
          }
        }
      }

      out.push({
        id: `usa:${d.PositionID || Math.random().toString()}`,
        title: d.PositionTitle || '',
        location: locs[0]?.LocationName || '',
        url: d.PositionURI || '',
        company: d.OrganizationName || entry.name,
        source: 'usajobs',
        pay,
        posted_at: d.PublicationStartDate || '',
      });
    }
  }

  return out;
}
