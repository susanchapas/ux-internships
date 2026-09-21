import { useEffect, useState } from 'react';
import { getStaticData, isStaticMode } from '../../api/mode';
import type { Job } from '../../api/types';
import { useSSE } from '../../hooks/useSSE';
import { useFilters } from '../../hooks/useFilters';
import { useApplicationsStore } from '../../store/applications';
import { useCompaniesStore } from '../../store/companies';
import { useJobsStore } from '../../store/jobs';
import { ScanFilters } from './ScanFilters';
import { FilterBar } from './FilterBar';
import { JobDetailModal } from './JobDetailModal';
import { JobTable } from './JobTable';
import { ScanProgress } from './ScanProgress';
import styles from './Scanner.module.css';

export function ScannerTab() {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const allJobs = useJobsStore((state) => state.allJobs);
  const hiddenIds = useJobsStore((state) => state.hiddenIds);
  const setAllJobs = useJobsStore((state) => state.setAllJobs);
  const toggleHideJob = useJobsStore((state) => state.toggleHideJob);
  const toggleFavJob = useJobsStore((state) => state.toggleFavJob);
  const toggleFavEmployer = useCompaniesStore((state) => state.toggleFavEmployer);
  const trackJob = useApplicationsStore((state) => state.trackJob);
  const isJobTracked = useApplicationsStore((state) => state.isJobTracked);
  const { start: scanNow, scanState } = useSSE();
  const { filteredJobs } = useFilters();
  useEffect(() => { const initialJobs = getStaticData()?.jobs; if (isStaticMode() && initialJobs && !allJobs.length) setAllJobs(initialJobs); }, [allJobs.length, setAllJobs]);
  const sources = [...new Set(allJobs.map((job) => job.source).filter(Boolean))].sort();
  return <section className={styles.scanner}>
    <div className={styles.topline}><div><p className={styles.eyebrow}>Opportunity scanner</p><h1>Find your next UX role</h1></div><div className={styles.actions}><ScanFilters /><button className={styles.scanButton} onClick={scanNow}>{scanState.isScanning ? 'Restart scan' : 'Scan now'}</button></div></div>
    <ScanProgress scan={scanState} />
    {!allJobs.length && !scanState.isScanning ? <div className={styles.empty}><h2>Ready to scan</h2><p>Scan company boards for matching UX postings.</p></div> : <>
      <div className={styles.stats}><Stat value={allJobs.length} label="Matches" /><Stat value={allJobs.filter((job) => job.is_new).length} label="New" /><Stat value={sources.length} label="Sources" /><Stat value={allJobs.filter((job) => job.pay).length} label="With pay" /></div>
      <FilterBar sources={sources} hiddenCount={hiddenIds.length} />
      {scanState.scanErrors.length > 0 && <details className={styles.errors}><summary>{scanState.scanErrors.length} scan error{scanState.scanErrors.length === 1 ? '' : 's'}</summary><ul>{scanState.scanErrors.map((error, index) => <li key={`${error.company}-${index}`}>{error.company}: {error.error}</li>)}</ul></details>}
      <JobTable jobs={filteredJobs} total={allJobs.length} onOpen={setSelectedJob} onHide={toggleHideJob} onFavorite={toggleFavJob} onEmployer={toggleFavEmployer} onTrack={trackJob} />
    </>}
    <JobDetailModal job={selectedJob} onClose={() => setSelectedJob(null)} onFavorite={toggleFavJob} onHide={toggleHideJob} onTrack={trackJob} isTracked={isJobTracked(selectedJob?.id || '')} />
  </section>;
}
function Stat({ value, label }: { value: number; label: string }) { return <div className={styles.stat}><strong>{value}</strong><span>{label}</span></div>; }
