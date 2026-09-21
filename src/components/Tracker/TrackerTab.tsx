import { useEffect, useMemo, useState } from 'react';
import type { Application } from '../../api/types';
import { useApplicationsStore } from '../../store/applications';
import { usePreferencesStore } from '../../store/preferences';
import { COLUMN_DEFAULTS } from '../../utils/constants';
import { AddApplicationModal } from './AddApplicationModal';
import { PipelineBar } from './PipelineBar';
import { TrackerTable, type TrackerFilters } from './TrackerTable';
import styles from './Tracker.module.css';

const emptyFilters: TrackerFilters = { company: '', title: '', location: '', status: '', deadline: '', reminder: '', applied: '', notes: '' };

export function TrackerTab() {
  const { items, isLoading, error, loadApplications, addApplication, updateApplication, deleteApplication } = useApplicationsStore();
  const { columns, setColumnVisibility, sort, setSort } = usePreferencesStore();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<TrackerFilters>(emptyFilters);
  const [columnsOpen, setColumnsOpen] = useState(false);
  useEffect(() => { void loadApplications(); }, [loadApplications]);
  const filtered = useMemo(() => items.filter((app) => {
    const haystack = `${app.company} ${app.title} ${app.location || ''}`.toLowerCase();
    if (search && !haystack.includes(search.toLowerCase())) return false;
    if (filters.company && !app.company.toLowerCase().includes(filters.company.toLowerCase())) return false;
    if (filters.title && !app.title.toLowerCase().includes(filters.title.toLowerCase())) return false;
    if (filters.location && !(app.location || '').toLowerCase().includes(filters.location.toLowerCase())) return false;
    if (filters.status && app.status !== filters.status) return false;
    if (filters.deadline && (app.deadline || '') !== filters.deadline) return false;
    if (filters.reminder && (app.reminder_interval || 'daily') !== filters.reminder) return false;
    if (filters.applied && (app.applied_at || '') !== filters.applied) return false;
    if (filters.notes && !(app.notes || '').toLowerCase().includes(filters.notes.toLowerCase())) return false;
    return true;
  }).sort((a, b) => {
    const key = sort.column as keyof Application;
    return String(a[key] || '').localeCompare(String(b[key] || '')) * sort.direction;
  }), [items, search, filters, sort]);
  const applied = items.filter((app) => ['applied', 'phone_screen', 'interview', 'offer', 'accepted'].includes(app.status)).length;
  const interviewing = items.filter((app) => ['phone_screen', 'interview'].includes(app.status)).length;
  const offers = items.filter((app) => ['offer', 'accepted'].includes(app.status)).length;
  const setFilter = <K extends keyof TrackerFilters>(key: K, value: TrackerFilters[K]) => setFilters((current) => ({ ...current, [key]: value }));
  return <section className={styles.tracker}>
    <div className={styles.topline}><div><p className={styles.eyebrow}>Application tracker</p><h1>Keep your search moving</h1></div><button className={styles.addButton} onClick={() => setIsAddOpen(true)}>+ Add application</button></div>
    <div className={styles.stats}><Stat value={items.length} label="Tracked" /><Stat value={applied} label="Applied" /><Stat value={interviewing} label="Interviewing" /><Stat value={offers} label="Offers" /></div>
    {items.length > 0 && <PipelineBar items={items} activeStatus={filters.status} onStatus={(status) => setFilter('status', filters.status === status ? '' : status)} />}
    <div className={styles.toolbar}><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tracked applications…" aria-label="Search tracked applications" /><div className={styles.columnPicker}><button className={columnsOpen ? styles.active : ''} onClick={() => setColumnsOpen(!columnsOpen)}>Columns</button>{columnsOpen && <div className={styles.columnMenu}>{COLUMN_DEFAULTS.tracker.map((column) => <label key={column}><input type="checkbox" checked={columns.tracker.includes(column)} onChange={() => setColumnVisibility('tracker', column, !columns.tracker.includes(column))} />{column === 'remind' ? 'Remind' : column === 'applied' ? 'Applied' : column[0].toUpperCase() + column.slice(1)}</label>)}</div>}</div><span className={styles.resultCount}>{filtered.length} of {items.length}</span></div>
    {isLoading ? <div className={styles.empty}>Loading applications…</div> : error ? <div className={styles.error}>{error}</div> : !items.length ? <div className={styles.empty}><h2>No applications tracked yet</h2><p>Use Scanner to find a role, or add an application manually.</p><button className={styles.addButton} onClick={() => setIsAddOpen(true)}>+ Add application</button></div> : <TrackerTable items={filtered} columns={columns.tracker} filters={filters} onFilter={setFilter} sort={sort} onSort={setSort} onUpdate={updateApplication} onDelete={deleteApplication} />}
    <AddApplicationModal open={isAddOpen} onClose={() => setIsAddOpen(false)} onAdd={addApplication} />
  </section>;
}
function Stat({ value, label }: { value: number; label: string }) { return <div className={styles.stat}><strong>{value}</strong><span>{label}</span></div>; }
