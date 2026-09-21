import { useState } from 'react'
import { AccountSection } from './AccountSection'
import { AlertPreferences } from './AlertPreferences'
import { SettingsSection } from './SettingsSection'
import styles from './Profile.module.css'

type ProfilePane = 'account' | 'settings' | 'alerts'
const panes: Array<{ id: ProfilePane; label: string }> = [{ id: 'account', label: 'Account' }, { id: 'settings', label: 'Settings' }, { id: 'alerts', label: 'Alert Preferences' }]
export function ProfileTab() { const [pane, setPane] = useState<ProfilePane>('account'); return <section className={styles.profile}><div className={styles.tabs} role="tablist" aria-label="Profile sections">{panes.map(({ id, label }) => <button key={id} role="tab" aria-selected={pane === id} className={pane === id ? styles.active : ''} onClick={() => setPane(id)}>{label}</button>)}</div>{pane === 'account' && <AccountSection />}{pane === 'settings' && <SettingsSection />}{pane === 'alerts' && <AlertPreferences />}</section> }
