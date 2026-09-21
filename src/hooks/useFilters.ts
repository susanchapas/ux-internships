import { useMemo } from 'react';
import type { Job } from '../api/types';
import { useCompaniesStore } from '../store/companies';
import { useJobsStore } from '../store/jobs';
import { usePreferencesStore } from '../store/preferences';
import { parsePayNum, parsePostedDate } from '../utils/format';

export function useFilters() {
  const allJobs = useJobsStore((state) => state.allJobs);
  const hiddenIds = useJobsStore((state) => state.hiddenIds);
  const favJobIds = useJobsStore((state) => state.favJobIds);
  const favEmployers = useCompaniesStore((state) => state.favEmployers);
  const filters = usePreferencesStore((state) => state.filters);
  const scanFilters = usePreferencesStore((state) => state.scanFilters);
  const sort = usePreferencesStore((state) => state.sort);

  const hiddenSet = useMemo(() => new Set(hiddenIds), [hiddenIds]);
  const favJobSet = useMemo(() => new Set(favJobIds), [favJobIds]);
  const favEmpSet = useMemo(() => new Set(favEmployers), [favEmployers]);

  const filteredJobs = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase();
    const sfLoc = (scanFilters.location || '').trim().toLowerCase();
    const minH = scanFilters.minHourly ? parseFloat(scanFilters.minHourly) : 0;
    const minS = scanFilters.minSalary ? parseFloat(scanFilters.minSalary) : 0;

    const levelFilterSet = filters.level.length ? new Set(filters.level) : null;
    const payTypeFilterSet = filters.payType.length ? new Set(filters.payType) : null;
    const scheduleFilterSet = filters.schedule.length ? new Set(filters.schedule) : null;
    const sourceFilterSet = filters.source.length ? new Set(filters.source) : null;

    const sfLevelsSet = scanFilters.levels.length ? new Set(scanFilters.levels) : null;
    const sfSchedulesSet = scanFilters.schedules.length ? new Set(scanFilters.schedules) : null;

    return allJobs.filter((j) => {
      const isHidden = hiddenSet.has(j.id);
      if (!filters.showHidden && isHidden) return false;
      if (filters.showHidden && !isHidden) return false;

      const isFav = favJobSet.has(j.id);
      // A favorited employer is a favorite in the legacy dashboard too.
      if (filters.favOnly && !isFav && !favEmpSet.has(j.company)) return false;

      if (q) {
        const hay = `${j.title} ${j.company} ${j.location || ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }

      // Multi-select filters
      const jLevel = j.level || 'mid';
      if (levelFilterSet && !levelFilterSet.has(jLevel)) return false;

      const jPayType = j.pay_type || 'unspecified';
      if (payTypeFilterSet && !payTypeFilterSet.has(jPayType)) return false;

      const jSchedule = j.schedule || 'other';
      if (scheduleFilterSet && !scheduleFilterSet.has(jSchedule)) return false;

      if (sourceFilterSet && !sourceFilterSet.has(j.source)) return false;

      // Scan preferences filters
      if (sfLevelsSet && !sfLevelsSet.has(jLevel)) return false;
      if (sfSchedulesSet && !sfSchedulesSet.has(jSchedule)) return false;

      if (scanFilters.payListed && !j.pay) return false;
      if (minH > 0 && j.pay_type === 'hourly' && parsePayNum(j.pay) < minH) return false;
      if (minS > 0 && j.pay_type === 'salary' && parsePayNum(j.pay) < minS) return false;

      if (scanFilters.favoritesOnly && !isFav && !favEmpSet.has(j.company)) return false;
      if (sfLoc && !(j.location || '').toLowerCase().includes(sfLoc)) return false;

      return true;
    });
  }, [allJobs, favEmpSet, favJobSet, filters, hiddenSet, scanFilters]);

  const sortedJobs = useMemo(() => {
    const list = [...filteredJobs];
    const { column, direction } = sort;

    list.sort((a, b) => {
      let cmp = 0;
      switch (column) {
        case 'company':
          cmp = (a.company || '').localeCompare(b.company || '');
          break;
        case 'title':
          cmp = (a.title || '').localeCompare(b.title || '');
          break;
        case 'location':
          cmp = (a.location || '').localeCompare(b.location || '');
          break;
        case 'pay': {
          const payA = parsePayNum(a.pay);
          const payB = parsePayNum(b.pay);
          cmp = payA - payB;
          break;
        }
        case 'posted_at': {
          const dateA = parsePostedDate(a.posted_at)?.getTime() || 0;
          const dateB = parsePostedDate(b.posted_at)?.getTime() || 0;
          cmp = dateA - dateB;
          break;
        }
        case 'source':
          cmp = (a.source || '').localeCompare(b.source || '');
          break;
        default:
          cmp = (a.company || '').localeCompare(b.company || '');
          break;
      }
      return cmp * direction;
    });

    return list;
  }, [filteredJobs, sort]);

  const stats = useMemo(() => {
    let newCount = 0;
    let payCount = 0;
    const companySet = new Set<string>();

    for (const j of filteredJobs) {
      if (j.is_new) newCount++;
      if (j.pay) payCount++;
      if (j.company) companySet.add(j.company);
    }

    return {
      totalMatches: filteredJobs.length,
      newMatches: newCount,
      withPay: payCount,
      companiesCount: companySet.size,
    };
  }, [filteredJobs]);

  return {
    filteredJobs: sortedJobs,
    unSortedFilteredJobs: filteredJobs,
    totalCount: allJobs.length,
    stats,
  };
}
