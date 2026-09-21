export const PAY_REGEX =
  /\$\s*[\d,]+(?:\.\d{2})?(?:\s*(?:[-–—\/]|to)\s*\$?\s*[\d,]+(?:\.\d{2})?)?(?:\s*(?:per|\/|an?)\s*(?:hour|hr|yr|year|month|week|annum|annually))?(?:\s*(?:USD|CAD))?(?:\s*(?:per|\/|an?)\s*(?:hour|hr|yr|year|month|week|annum|annually))?/gi;

export const CLIENT_LEVEL_RULES: [string, RegExp][] = [
  ['intern', /\bintern(?:ship)?\b|\bco-?op\b|\bextern(?:ship)?\b|\btrainee\b|\bpracticum\b/i],
  ['fellow', /\bfellow(?:ship)?\b/i],
  ['apprentice', /\bapprentice(?:ship)?\b/i],
  ['entry', /\b(?:associate|junior|jr\.?|entry[\s-]level|new[\s-]grad|analyst\s*I\b)/i],
  ['manager+', /\b(?:manager|director|vp\b|vice\s*president|head\s+of|chief|president)\b/i],
  ['senior+', /\b(?:senior|sr\.?|lead|staff|principal)\b/i],
];

export function extractPay(text?: string | null): string {
  if (!text) return '';
  const cleanText = text
    .replace(/<[^>]*>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");

  const matches = cleanText.match(PAY_REGEX) || [];
  const unique = [...new Set(matches.map((m) => m.trim()))].filter(Boolean);
  return unique.join('; ');
}

export interface ClassifiableJob {
  title?: string;
  pay?: string;
  commitment?: string;
  employment_type?: string;
  level?: string;
  pay_type?: 'hourly' | 'salary' | '' | string;
  schedule?: 'full-time' | 'part-time' | 'contract' | '' | string;
}

export function classifyJob<T extends ClassifiableJob>(job: T): T {
  let level = 'mid';
  const title = job.title || '';

  for (const [lbl, pat] of CLIENT_LEVEL_RULES) {
    if (pat.test(title)) {
      level = lbl;
      break;
    }
  }
  job.level = level;

  const pay = job.pay || '';
  if (!pay) {
    job.pay_type = '';
  } else if (/(?:per|\/|an?)\s*(?:hour|hr)\b/i.test(pay)) {
    job.pay_type = 'hourly';
  } else if (/(?:per|\/|an?)\s*(?:year|yr|annum|annually)\b/i.test(pay)) {
    job.pay_type = 'salary';
  } else {
    const a = pay.match(/\$\s*([\d,]+)/);
    job.pay_type = a && parseInt(a[1].replace(/,/g, ''), 10) > 1000 ? 'salary' : 'hourly';
  }

  const emp = (job.commitment || job.employment_type || '').toLowerCase();
  const tl = title.toLowerCase();

  if (/\bpart[\s-]?time\b/.test(tl) || emp.includes('part-time') || emp.includes('parttime')) {
    job.schedule = 'part-time';
  } else if (/\bfull[\s-]?time\b/.test(tl) || emp.includes('full-time') || emp.includes('fulltime')) {
    job.schedule = 'full-time';
  } else if (emp.includes('contract') || emp.includes('temporary') || /\bcontract\b/.test(tl)) {
    job.schedule = 'contract';
  } else {
    job.schedule = '';
  }

  return job;
}
