import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { LandingTab } from './components/Landing/LandingTab'
import { ProfileTab } from './components/Profile/ProfileTab'
import { ScannerTab } from './components/Scanner/ScannerTab'
import { Shell } from './components/Shell/Shell'
import { TrackerTab } from './components/Tracker/TrackerTab'
import { AuthScreen } from './components/Shell/AuthScreen'
import { useCloudSync } from './hooks/useCloudSync'
import { isStaticMode } from './api/mode'
import { useAuthStore } from './store/auth'
import { useJobsStore } from './store/jobs'

function AppRoutes() {
  useCloudSync()
  const user = useAuthStore((state) => state.user)
  const isLoading = useAuthStore((state) => state.isLoading)
  const init = useAuthStore((state) => state.init)
  const loadHiddenIds = useJobsStore((state) => state.loadHiddenIds)
  useEffect(() => init(), [init])
  useEffect(() => {
    if (user && !isStaticMode()) void loadHiddenIds()
  }, [user, loadHiddenIds])
  if (isLoading) return <div className="app-loading" role="status">Loading your dashboard…</div>
  if (!user) return <AuthScreen />
  return <Shell><Routes><Route path="/" element={<LandingTab/>}/><Route path="/scanner" element={<ScannerTab/>}/><Route path="/tracker" element={<TrackerTab/>}/><Route path="/profile" element={<ProfileTab/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes></Shell>
}
export default function App(){return <AppRoutes/>}
