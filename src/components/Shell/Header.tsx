import { Link } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import styles from './Shell.module.css'
export function Header() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  return <header className={styles.header}><Link className={styles.logo} to="/" aria-label="UX Internship Watch home"><span>UX</span> Internship Watch</Link><div className={styles.account}>{user && <span className={styles.userInfo}>{user.username}</span>}<span className={styles.phase}>React migration · Phase 6</span>{user && <button className={styles.logout} onClick={() => void logout()}>Sign out</button>}</div></header>
}
