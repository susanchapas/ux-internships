import { useEffect } from 'react';
import { getStaticData, isStaticMode } from '../../api/mode';
import { useApplicationsStore } from '../../store/applications';
import { useCompaniesStore } from '../../store/companies';
import { useJobsStore } from '../../store/jobs';
import { BentoGrid } from './BentoGrid';
import styles from './Landing.module.css';

export function LandingTab() {
  const jobs = useJobsStore((state) => state.allJobs);
  const setAllJobs = useJobsStore((state) => state.setAllJobs);
  const applications = useApplicationsStore((state) => state.items);
  const loadApplications = useApplicationsStore((state) => state.loadApplications);
  const hiddenIds = useJobsStore((state) => state.hiddenIds);
  const favoriteCompanies = useCompaniesStore((state) => state.favEmployers);
  useEffect(() => { const staticJobs = getStaticData()?.jobs; if (isStaticMode() && staticJobs && jobs.length === 0) setAllJobs(staticJobs); }, [jobs.length, setAllJobs]);
  useEffect(() => { void loadApplications(); }, [loadApplications]);
  return <section className={styles.landing} aria-label="Dashboard"><BentoGrid jobs={jobs} applications={applications} hiddenIds={hiddenIds} favoriteCompanies={favoriteCompanies} /></section>;
}
