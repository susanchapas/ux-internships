import { NavLink } from 'react-router-dom'
import styles from './Shell.module.css'
const tabs=[{to:'/',label:'Home',end:true},{to:'/scanner',label:'Scanner'},{to:'/tracker',label:'Tracker'},{to:'/profile',label:'Profile'}]
export function TabBar(){return <nav className={styles.tabs} aria-label="Main navigation">{tabs.map(({to,label,end})=><NavLink key={to} to={to} end={end} className={({isActive})=>`${styles.tab} ${isActive?styles.active:''}`}>{label}</NavLink>)}</nav>}
