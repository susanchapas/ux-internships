export const CORE_UX_REGEX =
  /\bUX\b|\bUI\b|\buser experience|\buser interface|\buser research|\bproduct design|\binteraction design|\binteractive design|\bexperience design|\bhuman-centered design|\binclusive design|\baccessibility\b|\ba11y\b|\busability\b|\bHCI\b|\bUXR\b|\bdesign research|\bdesign system|\bcontent design|\bUX writing|\bdesign engineer|\bdesign engineering|\bcreative developer|\bcreative development|\bUX engineer|\bUX developer|\bUI engineer|\bUI developer/i;

export const DOMAIN_EXCLUDE_REGEX =
  /\bsales\b|\brecruiting\b|\brecruiter\b|\btalent acquisition\b|\bclinical\b|\bhuman resources\b|\bhr\b|\blegal\b|\bcompliance\b|\baudit\b|\baccounting\b|\bsupply chain\b|\bdata science\b|\bdata scientist\b|\bmachine learning\b|\bdata analyst\b|\bequity research\b|\bcredit research\b/gi;

export const REMOTE_REGEX =
  /\bremote\b|\bhybrid\b|\bvirtual\b|\btelecommute\b|\btelecommuting\b|\bwork from home\b|\bwfh\b|\banywhere\b|\bdistributed\b/i;

export const US_REGEX = /\bUS\b|\bU\.S\b|\bUSA\b|\bunited states\b/i;

export interface FilterConfig {
  title_include: string[];
  title_exclude?: string[];
  location_include: string[];
  location_exclude?: string[];
  allow_all_remote?: boolean;
}

export function compileFilterConfig(cfg: FilterConfig) {
  return {
    titleInc: new RegExp(cfg.title_include.join('|'), 'i'),
    titleExc: cfg.title_exclude?.length ? new RegExp(cfg.title_exclude.join('|'), 'i') : null,
    locInc: new RegExp(cfg.location_include.join('|'), 'i'),
    locExc: cfg.location_exclude?.length ? new RegExp(cfg.location_exclude.join('|'), 'i') : null,
    allowAllRemote: Boolean(cfg.allow_all_remote),
  };
}

export function matchJob(
  job: { title?: string; location?: string; description?: string },
  compiled: ReturnType<typeof compileFilterConfig>
): boolean {
  const t = job.title || '';
  const l = job.location || '';

  if (!compiled.titleInc.test(t)) {
    return false;
  }

  if (compiled.titleExc && compiled.titleExc.test(t)) {
    if (CORE_UX_REGEX.test(t)) {
      const stripped = t.replace(DOMAIN_EXCLUDE_REGEX, ' ');
      if (compiled.titleExc.test(stripped)) {
        return false;
      }
    } else {
      return false;
    }
  }

  if (!l) {
    return true;
  }

  if (compiled.locInc.test(l)) {
    return true;
  }

  if (compiled.allowAllRemote && REMOTE_REGEX.test(l)) {
    return true;
  }

  if (REMOTE_REGEX.test(l)) {
    if (US_REGEX.test(l)) {
      return true;
    }
    if (compiled.locExc && compiled.locExc.test(l)) {
      return false;
    }
    return true;
  }

  return false;
}
