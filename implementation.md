# React Conversion — Implementation Plan

## Stack

| Layer | Current | Target |
|-------|---------|--------|
| Build | None (raw HTML) | Vite |
| UI | Vanilla DOM manipulation | React 19 + TypeScript |
| Styles | Inline `<style>` (1400 lines) | CSS Modules (per component) |
| State | Global vars + localStorage | Zustand |
| Routing | Manual hash routing | React Router v7 |
| Auth | Firebase Auth (static) / session cookies (server) | Same, behind abstraction |
| Data | Fetch + SSE / localStorage | Same, behind abstraction |
| Backend | Python `web.py` | Unchanged |
| Static build | `build_static.py` bakes HTML | Vite build + data injection |

No new runtime dependencies beyond React, React Router, Zustand, and the existing Firebase SDK.

---

## Architecture

```
src/
├── main.tsx                    # Entry, providers, router
├── App.tsx                     # Shell: header, tabs, auth gate
├── theme/
│   └── tokens.css              # Design tokens from :root
├── api/
│   ├── types.ts                # Job, Application, ScanConfig, etc.
│   ├── mode.ts                 # STATIC flag detection
│   ├── auth.ts                 # AuthProvider abstraction
│   ├── auth-firebase.ts        # Firebase Auth implementation
│   ├── auth-server.ts          # Cookie session implementation
│   ├── jobs.ts                 # Scan + job fetching (SSE / static data)
│   ├── applications.ts         # Tracker CRUD
│   ├── sync.ts                 # Firestore cloud sync
│   └── ats/                    # Client-side ATS fetchers
│       ├── greenhouse.ts
│       ├── lever.ts
│       ├── ashby.ts
│       ├── smartrecruiters.ts
│       ├── workday.ts
│       ├── usajobs.ts
│       ├── workable.ts
│       ├── bamboohr.ts
│       ├── recruitee.ts
│       ├── eightfold.ts
│       ├── jsonld.ts
│       └── hydration.ts
├── store/
│   ├── jobs.ts                 # allJobs, hiddenJobs, favJobs, scanning state
│   ├── applications.ts         # tracker state
│   ├── preferences.ts          # filters, column visibility, saved filters, sort
│   ├── companies.ts            # company list, customizations, favorites
│   └── auth.ts                 # currentUser, login state
├── hooks/
│   ├── useSSE.ts               # SSE scan subscription
│   ├── useCloudSync.ts         # Firestore bidirectional sync
│   ├── usePersistedState.ts    # localStorage <-> Zustand bridge
│   └── useFilters.ts           # Computed filtered/sorted job list
├── components/
│   ├── Shell/                  # App chrome
│   │   ├── Header.tsx
│   │   ├── TabBar.tsx
│   │   └── AuthScreen.tsx
│   ├── Landing/                # Home/dashboard tab
│   │   ├── LandingTab.tsx
│   │   ├── BentoGrid.tsx
│   │   ├── StatsCard.tsx
│   │   ├── SankeyChart.tsx
│   │   ├── DeadlinesCard.tsx
│   │   ├── HighlightsCard.tsx
│   │   ├── FavoritesCard.tsx
│   │   ├── ManualChecksCard.tsx
│   │   └── RecentCard.tsx
│   ├── Scanner/                # Scan tab
│   │   ├── ScannerTab.tsx
│   │   ├── ScanProgress.tsx
│   │   ├── JobTable.tsx
│   │   ├── JobRow.tsx
│   │   ├── JobDetailModal.tsx
│   │   ├── FilterBar.tsx
│   │   ├── SavedFilters.tsx
│   │   ├── ColumnPicker.tsx
│   │   └── ScanFilters.tsx
│   ├── Tracker/                # Tracker tab
│   │   ├── TrackerTab.tsx
│   │   ├── TrackerTable.tsx
│   │   ├── TrackerRow.tsx
│   │   ├── AddApplicationModal.tsx
│   │   ├── PipelineBar.tsx
│   │   └── ColumnFilters.tsx
│   ├── Profile/                # Profile tab
│   │   ├── ProfileTab.tsx
│   │   ├── AccountSection.tsx
│   │   ├── SettingsSection.tsx
│   │   └── AlertPreferences.tsx
│   └── shared/
│       ├── Badge.tsx
│       ├── Modal.tsx
│       ├── Toast.tsx
│       ├── StatusBadge.tsx
│       ├── CompanyModal.tsx
│       └── ConfirmDialog.tsx
└── utils/
    ├── classify.ts             # Level/pay/schedule classification
    ├── filters.ts              # Title/location regex matching
    ├── format.ts               # Date, pay, relative time formatters
    └── constants.ts            # STATUS_LABELS, PIPELINE_COLORS, MANUAL_CHECKS
```

---

## Dual-Mode Abstraction

The app runs in two modes determined at build/load time:

```
Mode detection:
  window.STATIC_DATA exists → static mode (GitHub Pages)
  otherwise → server mode (Python backend)
```

Abstract through a `DataSource` interface:

```ts
interface DataSource {
  scan(): AsyncIterable<ScanEvent>      // SSE in server mode, client-side fetch in static
  getApplications(): Promise<Application[]>
  addApplication(app): Promise<string>
  updateApplication(id, patch): Promise<void>
  deleteApplication(id): Promise<void>
  hideJob(id): Promise<void>
  unhideJob(id): Promise<void>
  getHiddenIds(): Promise<string[]>
}

interface AuthSource {
  login(credentials): Promise<User>
  register(credentials): Promise<User>
  loginWithGoogle(): Promise<User>
  logout(): Promise<void>
  onAuthStateChanged(cb): Unsubscribe
  currentUser: User | null
  updateUsername(name): Promise<void>
  updateEmail(email): Promise<void>
  updatePassword(current, next): Promise<void>
}
```

Two implementations each. Mode flag selects at startup. Zustand stores consume the interface, never the implementation.

---

## State Management (Zustand)

Migrate from global variables + localStorage to Zustand slices with localStorage persistence:

| Current global | Zustand store | Persisted |
|----------------|--------------|-----------|
| `allJobs` | `jobs.allJobs` | No (scan result) |
| `hiddenJobs` (Set) | `jobs.hiddenIds` | Yes |
| `favJobs` (Set) | `jobs.favJobIds` | Yes |
| `favEmployers` (Set) | `companies.favEmployers` | Yes |
| `applications` | `applications.items` | Server/Firestore |
| `scanning` | `jobs.scanState` | No |
| `currentUser` | `auth.user` | Session |
| Filter state | `preferences.filters` | Yes |
| Column visibility | `preferences.columns` | Yes |
| Saved filters | `preferences.savedFilters` | Yes |
| Scan config overrides | `preferences.scanConfig` | Yes |
| Sort config | `preferences.sort` | Yes |
| Hidden columns | `preferences.hiddenColumns` | Yes |
| Company customizations | `companies.overrides` | Yes |
| Tab state | React Router | URL |

`usePersistedState` hook bridges Zustand ↔ localStorage on init and subscribes to changes. Cloud sync (Firestore) merges on top when authenticated.

---

## Component Extraction Map

### Shell
- **AuthScreen** ← `#auth-screen` div + login/register forms + Google sign-in button
- **Header** ← `.app-header` with logo, user info, logout
- **TabBar** ← `.tab-nav` buttons (Landing, Scanner, Tracker, Profile)

### Landing Tab
- **BentoGrid** ← `buildBentoGrid()` function (~200 lines) → composable card layout
- **SankeyChart** ← `buildSankey()` function (~250 lines) → SVG generation, keep as-is in a React wrapper with `useRef`
- **StatsCard** ← Stats section of bento grid (total jobs, new today, response rate, etc.)
- **DeadlinesCard** ← Upcoming deadlines from tracker applications
- **FavoritesCard** ← Favorite jobs list from `favJobs`
- **HighlightsCard** ← New/notable jobs highlight
- **ManualChecksCard** ← `MANUAL_CHECKS` constant → links to check manually

### Scanner Tab
- **ScanProgress** ← SSE progress bar + company-by-company status
- **JobTable** ← `#results-table` with sortable headers
- **JobRow** ← Individual job row with action buttons (favorite, hide, track, detail)
- **JobDetailModal** ← `#job-detail-modal` with full job info + actions
- **FilterBar** ← Level/pay/schedule/source/lane multi-select filters
- **ColumnPicker** ← Column visibility toggles
- **SavedFilters** ← Save/load/delete filter presets
- **ScanFilters** ← Title include/exclude, location filters, company selection

### Tracker Tab
- **TrackerTable** ← `#tracker-table` with inline editing
- **TrackerRow** ← Editable row (status dropdown, deadline picker, notes, etc.)
- **AddApplicationModal** ← `#add-app-modal` form
- **PipelineBar** ← Pipeline visualization bar (saved → applied → screen → interview → offer)
- **ColumnFilters** ← Per-column filter inputs

### Profile Tab
- **AccountSection** ← Username, email, password change forms
- **SettingsSection** ← Theme, notification preferences
- **AlertPreferences** ← Discord/ntfy webhook config

### Shared
- **Modal** ← Generic modal wrapper (backdrop, close, animation)
- **Badge** ← Level/lane/schedule badges
- **StatusBadge** ← Application status with pipeline color
- **Toast** ← Notification toasts
- **CompanyModal** ← `#companies-modal` — add/remove/edit companies
- **ConfirmDialog** ← Delete confirmations

---

## Migration Phases

### Phase 1: Scaffold (est. 2-3 hours)
1. `npm create vite@latest . -- --template react-ts` (in new branch)
2. Move Firebase config to `src/api/auth-firebase.ts`
3. Extract CSS tokens to `src/theme/tokens.css`
4. Set up React Router with 4 tab routes
5. Create empty tab components + Shell
6. Verify dev server runs with blank shell

### Phase 2: Data Layer (est. 3-4 hours)
1. Define TypeScript types from existing JS objects (`Job`, `Application`, `ScanConfig`, etc.)
2. Implement `DataSource` — server mode (REST + SSE)
3. Implement `DataSource` — static mode (baked `STATIC_DATA` + client-side ATS fetchers)
4. Port ATS fetchers from `BOARD_FETCH` in `dashboard.html` lines ~2200-2600 to `src/api/ats/`
5. Implement `AuthSource` — Firebase and server variants
6. Set up Zustand stores with localStorage persistence
7. Port Firestore cloud sync to `useCloudSync` hook

### Phase 3: Scanner Tab (est. 4-5 hours)
1. Port `ScanProgress` — SSE event handling + progress bar
2. Port `JobTable` + `JobRow` — sorting, column visibility, action buttons
3. Port `FilterBar` — multi-select filters with counts
4. Port `JobDetailModal`
5. Port `SavedFilters` + `ColumnPicker`
6. Port `ScanFilters` (title/location regex config, company toggles)
7. Wire hide/favorite/track actions to stores

### Phase 4: Tracker Tab (est. 3-4 hours)
1. Port `TrackerTable` with inline editing
2. Port `AddApplicationModal`
3. Port `PipelineBar` visualization
4. Port column filters + sorting
5. Wire CRUD to `DataSource` + Zustand

### Phase 5: Landing Tab (est. 3-4 hours)
1. Port `BentoGrid` layout
2. Port `SankeyChart` — wrap SVG generation in `useRef` + `useEffect`
3. Port stat calculations + cards
4. Port `DeadlinesCard`, `FavoritesCard`, `ManualChecksCard`
5. Port highlight/recent cards

### Phase 6: Profile + Auth (est. 2-3 hours)
1. Port `AuthScreen` (login, register, Google sign-in)
2. Port profile forms (username, email, password change)
3. Port settings + alert preferences
4. Wire auth state to route protection

### Phase 7: Static Build + Deploy (est. 2-3 hours)
1. Update `build_static.py` to inject `STATIC_DATA` / `STATIC_CONFIG` into Vite's `index.html` output
2. Update GitHub Actions `deploy.yml` to run `npm run build` then `build_static.py`
3. Verify GitHub Pages deploy works
4. Update `ci.yml` for TypeScript checks

### Phase 8: Polish + Parity Check (est. 2-3 hours)
1. Visual diff against current dashboard
2. Test both modes (server + static)
3. Verify localStorage migration (existing users' data carries over)
4. Test cloud sync flow (login → Firestore → cross-device)
5. Test scan flow end-to-end in both modes
6. Responsive/mobile check

---

## Key Decisions

**CSS Modules over Tailwind/styled-components** — The existing CSS is well-structured with clear token usage. CSS Modules preserve the mental model, avoid a new dependency, and let us copy styles nearly verbatim.

**Zustand over Context/Redux** — Lightweight, no boilerplate, built-in persistence middleware. The app has ~10 independent state slices that don't need a single global reducer tree.

**Keep Python backend unchanged** — The backend is small (418 lines), stable, and already works. No reason to rewrite it. The React app consumes the same REST/SSE API.

**No SSR** — This is a client-side SPA (static deploy to GitHub Pages). Vite's default client build is sufficient.

**Port ATS fetchers to TypeScript** — The client-side ATS fetchers in `dashboard.html` (~400 lines) must be ported to `src/api/ats/`. The Python fetchers in `internship_watch.py` stay as-is for server mode.

**Sankey chart: keep vanilla SVG** — The Sankey generation (~250 lines) produces raw SVG. Wrap it in a React component with `useRef` rather than rewriting with a charting library — it's custom-shaped to the pipeline and has no external dependency.

---

## Files to Delete After Migration

```
dashboard.html          # Replaced by src/
build_static.py         # Replaced (rewritten to inject into Vite output)
```

All Python backend files (`web.py`, `db.py`, `auth.py`, `models.py`, `schemas.py`, `internship_watch.py`) remain unchanged.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| localStorage key compatibility | Use identical keys so existing users keep their data |
| Static inject breaks with Vite | Test `build_static.py` against Vite's output format early (Phase 7) |
| Client-side ATS fetchers have CORS issues | They work today because of the same browser fetch — no change in behavior |
| Sankey SVG relies on DOM measurements | Use `useLayoutEffect` + `ResizeObserver` for sizing |
| Firebase compat SDK (v10 compat) | Migrate to modular SDK (v10+) during port for tree-shaking |

---

## Estimated Total: 21-29 hours

Phase 1-2 (foundation) should be complete before any UI work begins. Phases 3-6 can overlap if working on separate branches.
