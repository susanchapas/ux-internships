import { useEffect, useRef } from 'react';
import type { Application, ApplicationStatus } from '../../api/types';
import { STATUS_LABELS } from '../../utils/constants';
import { Link } from 'react-router-dom';
import styles from './Landing.module.css';

const active: ApplicationStatus[] = ['saved', 'applied', 'phone_screen', 'interview', 'offer', 'accepted'];
const closed: ApplicationStatus[] = ['rejected', 'withdrawn', 'ghosted'];
const colors: Record<ApplicationStatus, string> = { saved: '#6b83b0', applied: '#2a9d6e', phone_screen: '#c47d52', interview: '#b5723d', offer: '#1e8a5a', accepted: '#2a9d6e', rejected: '#dc4545', withdrawn: '#8b95a5', ghosted: '#7c3aed' };
type Node = { label: string; value: number; color: string; y: number; h: number; group?: 'active' | 'closed' };

function markup(applications: Application[]) {
  if (!applications.length) return '<p class="sankey-empty">Track applications to see your pipeline flow</p>';
  const counts = Object.fromEntries([...active, ...closed].map((key) => [key, 0])) as Record<ApplicationStatus, number>;
  applications.forEach(({ status }) => { if (status in counts) counts[status]++; });
  const total = applications.length, W = 820, H = 240, nodeW = 10, gap = 5, colX = [100, 360, 580];
  const activeN = active.reduce((sum, key) => sum + counts[key], 0), closedN = closed.reduce((sum, key) => sum + counts[key], 0);
  const h = (value: number) => value ? Math.max(4, value / total * (H - gap * 10)) : 0;
  const groups: Node[] = [{ label: 'Active', value: activeN, color: '#2a9d6e', y: 0, h: 0 }, { label: 'Closed', value: closedN, color: '#94a3b8', y: 0, h: 0 }].filter((node) => node.value);
  const stages: Node[] = [...active, ...closed].filter((key) => counts[key]).map((key) => ({ label: STATUS_LABELS[key], value: counts[key], color: colors[key], group: active.includes(key) ? 'active' : 'closed', y: 0, h: 0 }));
  const layout = (nodes: Node[], start = 0, available = H) => { const needed = nodes.reduce((sum, node) => sum + h(node.value), 0) + gap * Math.max(0, nodes.length - 1); let y = start + (available - needed) / 2; nodes.forEach((node) => { node.h = h(node.value); node.y = y; y += node.h + gap; }); };
  layout(groups); groups.forEach((group) => layout(stages.filter((node) => node.group === group.label.toLowerCase()), group.y, group.h));
  const sourceH = h(total), sourceY = (H - sourceH) / 2;
  const flow = (sx: number, sy: number, sh: number, dx: number, dy: number, dh: number, color: string) => { const x1 = sx + nodeW, mid = (x1 + dx) / 2; return `<path class="sankey-flow" d="M${x1},${sy} C${mid},${sy} ${mid},${dy} ${dx},${dy} L${dx},${dy + dh} C${mid},${dy + dh} ${mid},${sy + sh} ${x1},${sy + sh} Z" fill="${color}" fill-opacity=".2" stroke="${color}" stroke-width=".5" stroke-opacity=".3"/>`; };
  let flows = '', sourceOffset = sourceY;
  groups.forEach((group) => { const flowH = group.value / total * sourceH; flows += flow(colX[0], sourceOffset, flowH, colX[1], group.y, group.h, group.color); sourceOffset += flowH; let offset = group.y; stages.filter((node) => node.group === group.label.toLowerCase()).forEach((stage) => { const stageH = stage.value / group.value * group.h; flows += flow(colX[1], offset, stageH, colX[2], stage.y, stage.h, stage.color); offset += stageH; }); });
  const rect = (x: number, node: Node) => `<rect x="${x}" y="${node.y}" width="${nodeW}" height="${node.h}" rx="2" fill="${node.color}"/>`;
  const source: Node = { label: 'Applications', value: total, color: '#6b83b0', y: sourceY, h: sourceH };
  const label = (x: number, node: Node) => `<text x="${x}" y="${node.y + node.h / 2}" dominant-baseline="middle" class="sankey-label">${node.label} <tspan class="sankey-count">${node.value}</tspan></text>`;
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Application flow: ${total} applications"><title>Application flow</title>${flows}${rect(colX[0], source)}${groups.map((n) => rect(colX[1], n)).join('')}${stages.map((n) => rect(colX[2], n)).join('')}<text x="${colX[0] - 12}" y="${sourceY + sourceH / 2 - 16}" text-anchor="end" class="sankey-label-src">Applications</text><text x="${colX[0] - 12}" y="${sourceY + sourceH / 2 + 8}" text-anchor="end" class="sankey-label-n">${total}</text>${groups.map((n) => label(colX[1] + nodeW + 8, n)).join('')}${stages.map((n) => label(colX[2] + nodeW + 8, n)).join('')}</svg>`;
}
export function SankeyChart({ applications }: { applications: Application[] }) { const chart = useRef<HTMLDivElement>(null); useEffect(() => { if (chart.current) chart.current.innerHTML = markup(applications); }, [applications]); return <section className={`${styles.card} ${styles.sankey}`}><header className={styles.header}><h2>Application Flow</h2><Link to="/tracker">Open tracker →</Link></header><div ref={chart} className={styles.sankeyChart} /></section>; }
