import type { Application, Job } from '../../api/types';
import { DeadlinesCard } from './DeadlinesCard';
import { FavoritesCard } from './FavoritesCard';
import { HighlightsCard } from './HighlightsCard';
import { ManualChecksCard } from './ManualChecksCard';
import { SankeyChart } from './SankeyChart';
import { StatsCard } from './StatsCard';
import { Link } from 'react-router-dom';
import styles from './Landing.module.css';
interface Props { jobs: Job[]; applications: Application[]; hiddenIds: string[]; favoriteCompanies: string[] }
export function BentoGrid({ jobs, applications, hiddenIds, favoriteCompanies }: Props) { const hasDeadlines = applications.some((item) => item.status === 'saved' && Boolean(item.deadline)); return <div className={`${styles.grid} ${hasDeadlines ? styles.hasDeadlines : ''}`}><SankeyChart applications={applications} /><Link className={`${styles.card} ${styles.scannerLink}`} to="/scanner"><span className={styles.linkTitle}>Job Scanner</span><span className={styles.linkSubtitle}>Scan company boards for matching UX postings</span><span className={styles.arrow} aria-hidden="true">→</span></Link><Link className={`${styles.card} ${styles.trackerLink}`} to="/tracker"><span className={styles.linkTitle}>Tracker</span><span className={styles.linkSubtitle}>Track your applications &amp; pipeline</span><span className={styles.arrow} aria-hidden="true">→</span></Link><DeadlinesCard applications={applications} /><HighlightsCard jobs={jobs} hiddenIds={hiddenIds} /><StatsCard applications={applications} /><FavoritesCard companies={favoriteCompanies} /><ManualChecksCard /></div>; }
