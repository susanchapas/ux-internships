import styles from './Scanner.module.css';
type ScanState = { isScanning: boolean; progressPercent: number; statusMessage?: string };
export function ScanProgress({ scan }: { scan: ScanState }) {
  if (!scan.isScanning && !scan.statusMessage) return null;
  return <div className={styles.progress} aria-live="polite"><div className={styles.progressTrack}><span style={{ width: `${scan.progressPercent}%` }} /></div><p>{scan.statusMessage}</p></div>;
}
