const dateCache = new Map<string, Date | null>();

export function parsePostedDate(s?: string | null): Date | null {
  if (!s) return null;
  if (dateCache.has(s)) return dateCache.get(s)!;

  let result: Date | null = null;
  const d = new Date(s);
  if (!isNaN(d.getTime())) {
    result = d;
  } else {
    const lower = s.toLowerCase().replace(/posted\s+/i, '').trim();
    if (/^(today|just now|0 days?)/.test(lower)) {
      result = new Date();
    } else if (/^yesterday|^1 day/.test(lower)) {
      const t = new Date();
      t.setDate(t.getDate() - 1);
      result = t;
    } else {
      const m = lower.match(/^(\d+)\s*(day|week|month|hour|minute)s?\s*ago/);
      if (m) {
        const n = parseInt(m[1], 10);
        const unit = m[2];
        const t = new Date();
        if (unit === 'day') t.setDate(t.getDate() - n);
        else if (unit === 'week') t.setDate(t.getDate() - n * 7);
        else if (unit === 'month') t.setMonth(t.getMonth() - n);
        else if (unit === 'hour') t.setHours(t.getHours() - n);
        else if (unit === 'minute') t.setMinutes(t.getMinutes() - n);
        result = t;
      }
    }
  }

  dateCache.set(s, result);
  return result;
}

export function timeAgo(s?: string | null): string {
  if (!s) return '—';
  const d = parsePostedDate(s);
  if (!d) return s;
  const days = Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000));
  if (days < 7) return days + (days === 1 ? ' day ago' : ' days ago');
  if (days < 30) {
    const w = Math.floor(days / 7);
    return w + (w === 1 ? ' week ago' : ' weeks ago');
  }
  const mo = Math.floor(days / 30);
  return mo + (mo === 1 ? ' month ago' : ' months ago');
}

export function parsePayNum(s?: string | null): number {
  if (!s) return 0;
  const m = s.match(/\$\s*([\d,]+(?:\.\d+)?)/);
  return m ? parseFloat(m[1].replace(/,/g, '')) : 0;
}
