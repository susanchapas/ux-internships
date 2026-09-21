import type { ReactNode } from 'react'
import { Header } from './Header'
import { TabBar } from './TabBar'
import styles from './Shell.module.css'
export function Shell({children}:{children:ReactNode}) { return <div className={styles.shell}><Header/><TabBar/><main className={styles.content}>{children}</main></div> }
