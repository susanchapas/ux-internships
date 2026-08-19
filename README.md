# internship-watch

**[Live Dashboard](https://susanchapas.github.io/ux-internships/)**

Polls company ATS APIs on a schedule, pushes you a notification when a new posting matches your filters. Includes an interactive REPL for scanning, filtering, and tracking applications.

## Setup

```bash
pip install requests selectolax
python internship_watch.py --dry-run     # see what matches before wiring notifications
python internship_watch.py --seed        # mark everything currently open as "seen"
python internship_watch.py               # from here on, only new stuff notifies
```

Then drop `watch.yml` into `.github/workflows/` in a **private** repo and add your secrets under
Settings → Secrets and variables → Actions. Free tier covers this easily.

## Interactive REPL

Launch the interactive shell for hands-on scanning, filtering, and application tracking:

```bash
python repl.py
```

### Available commands

| Command | Description |
|---|---|
| `scan` | Run a scan across all configured companies |
| `jobs` | Show results from the last scan |
| `apps` | List tracked applications |
| `save <job#> [notes]` | Save a matched job to your application tracker |
| `status <app_id> <status>` | Update an application's status |
| `delete <app_id>` | Remove a tracked application |
| `undo` | Undo the last status change |
| `filter [name]` | Show or switch the filter strategy |
| `config` | Show configuration summary |
| `help` | Show all commands |
| `quit` | Exit |

### Filter strategies

Switch filtering logic at runtime with `filter <name>`:

| Strategy | Description |
|---|---|
| `default` | Uses `title_include` / `title_exclude` / `location_include` from `config.json` |
| `ux-only` | Strict: title must mention both a UX discipline and an internship-level role |
| `paid` | Like default, but only jobs that list compensation |
| `remote` | Like default, but only remote or hybrid locations |

### Application statuses

`saved` → `applied` → `phone_screen` → `interview` → `offer` → `accepted`

Also: `rejected`, `withdrawn`

### Example session

```
$ python repl.py
Internship Watch — Interactive Mode
Filter: default  |  166 companies loaded
Type 'help' for commands.

>>> filter ux-only
  Filter → ux-only
>>> scan
  [1/166] AIG... 342 open, 0 match
  [2/166] AKQA... 15 open, 2 match
  NEW: AKQA | UX Design Intern | New York, NY
       https://boards.greenhouse.io/akqa/jobs/...
  ...
>>> jobs
  #     Company                  Title                                        Location                 Pay
  ───── ─────────────────────── ───────────────────────────────────────────── ─────────────────────── ────────────────────
  1     AKQA                    UX Design Intern                              New York, NY
  2     Braze                   Product Design Intern, Summer 2027            New York, NY             $30/hr
  ...
>>> save 2 "Great company, applied via website"
  Saved as application #1
>>> apps
  ID    Company                  Title                              Status          Updated
  ───── ─────────────────────── ─────────────────────────────────── ─────────────── ────────────────────
  1     Braze                   Product Design Intern, Summer 2027  saved           2026-08-19
>>> status 1 applied
  Updated #1 → 'applied'
>>> undo
  Undone: Braze — Product Design Intern, Summer 2027: 'saved' → 'applied'
```

## Architecture — design patterns

The system uses five GoF design patterns, implemented in [`patterns.py`](patterns.py):

### Observer (`EventBus`, `JobObserver`)

Decouples scan events from notification channels. When new jobs are found, the
`EventBus` broadcasts to all registered observers. Adding a new notification
channel (e.g., Slack, email) means writing one class — no changes to scan logic.

| Observer | Channel |
|---|---|
| `ConsoleObserver` | stdout |
| `NtfyObserver` | ntfy.sh push notification |
| `DiscordObserver` | Discord webhook |

### Memento (`ApplicationMemento`, `ApplicationCaretaker`)

Enables undo for application status changes. Before each update, a `Memento`
snapshot is saved to the `Caretaker`'s stack. The `undo` command pops and
restores the previous state.

### Strategy (`FilterStrategy` subclasses)

Swappable filtering algorithms. The active strategy can be changed at runtime
via the REPL's `filter` command. Strategies compose: `PaidOnlyFilterStrategy`
and `RemoteFilterStrategy` wrap an inner strategy (decorator pattern).

### Factory (`FetcherFactory`)

Creates the correct `Fetcher` subclass from a `config.json` company entry.
Each ATS board (Greenhouse, Lever, Ashby, SmartRecruiters, Workday, USAJobs)
has its own `Fetcher` class. The factory hides this selection behind
`FetcherFactory.create(entry)`.

### Facade (`InternshipFacade`)

Single entry point that wires together scanning (Factory), filtering (Strategy),
notifications (Observer), application tracking, and undo (Memento). Both the
REPL and any future interface (web, API) use the facade rather than calling
subsystems directly.

## Project structure

```
├── repl.py              # Interactive REPL — the main user interface
├── patterns.py          # Design patterns: Observer, Memento, Strategy, Factory, Facade
├── internship_watch.py  # ATS fetchers and CLI scan runner
├── config.json          # Filter regexes and company list (generated by resolve.py)
├── resolve.py           # Discovers ATS slugs from company names
├── targets.json         # 303 companies across 14 categories
├── discover.py          # Probes a careers page to identify the ATS in use
├── extractors.py        # Scrapers for sites not on a standard board
├── db.py                # SQLite storage for scan history and applications
├── web.py               # Browser dashboard (localhost)
├── build_static.py      # Static dashboard builder for GitHub Pages
├── dashboard.html       # Dashboard template
└── README.md
```

## Notifications

Pick one, set it as an env var / GitHub secret:

- **`NTFY_TOPIC`** — easiest. Pick any unguessable string (`susan-jobs-7fq3xk`), install the ntfy
  app, subscribe to that topic. No account, no auth. Anyone who guesses the topic can read it, so
  make it random.
- **`DISCORD_WEBHOOK`** — make a private server, Channel Settings → Integrations → New Webhook,
  paste the URL. Better if you want a searchable archive of everything that's opened.

## Finding a company's ATS slug — this is the actual work

Open the company's careers page. Look at the URL, or open DevTools → Network → filter XHR and
reload.

| What you see | Board | Slug |
|---|---|---|
| `boards.greenhouse.io/acme` or `job-boards.greenhouse.io/acme` | `greenhouse` | `acme` |
| `jobs.lever.co/acme` | `lever` | `acme` |
| `jobs.ashbyhq.com/acme` | `ashby` | `acme` |
| `jobs.smartrecruiters.com/Acme` | `smartrecruiters` | `Acme` (case-sensitive) |
| `acme.wd5.myworkdayjobs.com/en-US/External` | `workday` | tenant `acme`, wd `5`, site `External` |

Many companies embed Greenhouse/Lever in an iframe on their own `/careers` page — the Network tab
will still show the underlying `boards-api.greenhouse.io` call. That's your slug.

Test one before adding it:

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=false" | head -c 400
```

If you get JSON, you're good. 404 means wrong slug.

## Boards you'll hit that aren't covered here

- **iCIMS, Taleo, SuccessFactors, Phenom** — older enterprise systems, no clean public JSON.
  Some have feeds, most don't. If a target company uses one, it's usually less work to just set
  a calendar reminder to check manually than to build a parser.
- **LinkedIn / Indeed / Glassdoor** — don't. They rate-limit and ban aggressively, and the
  postings are mirrored from the ATS endpoints above anyway.

## Tuning

Start with the broad `title_include` in `config.json` — it catches every internship at each
company. Run `--dry-run` for a few days, see the volume, then tighten. If a company posts 200
internships a cycle, add a discipline filter:

```json
"title_include": ["(intern|co-?op|summer analyst).*(UX|user experience|design|research|product|content|strategy)",
                  "(UX|user experience|design|research|product).*(intern|co-?op)"]
```

## Timing

Fall is when Summer 2027 postings drop — roughly late August through October for large employers,
with finance and consulting earliest and agencies latest (often Jan–Mar). Getting this running now
is good timing.

---

# Part 2: scraping company sites directly

For companies not on a board `internship_watch.py` covers.

## Workflow

```bash
pip install requests selectolax
python discover.py https://www.company.com/careers
```

It reports which of five approaches will work, then you wire up the matching
extractor from `extractors.py`.

## The five approaches, best to worst

**1. Hidden ATS.** Lots of "custom" careers pages are an iframe or widget over
Greenhouse/Lever. `discover.py` catches this by looking for the signature
anywhere in the page, not just the URL. If it hits, you're done — use the
existing fetcher.

**2. JSON-LD (`schema.org/JobPosting`).** Google requires this markup to index
a posting into Google Jobs, so companies that want that traffic embed it. It's
a published standard, so one parser works across unrelated sites and survives
redesigns. Listings pages often omit it while each detail page has it — that's
what `jsonld_crawl()` handles.

**3. Hydration payload.** React/Vue sites embed their initial data as JSON in
the HTML (`__NEXT_DATA__`, `__NUXT__`). Same data the API returns, no API call.
Find where the jobs live once:

```python
import extractors as ex
p = ex.hydration_payload("https://company.com/careers", "next")
for path, n, keys in ex.find_arrays(p):
    print(f"{n:>4}  {path}\n      {keys}")
# spot the jobs array, then hardcode:
rows = ex.dig(p, "props.pageProps.initialData.openings")
```

**4. CSS selectors.** Right-click the repeating job row, Inspect, grab the
class. Works fine, breaks on redesign — a run that suddenly returns 0 matches
usually means selectors, not an empty board.

**5. Fingerprint the page.** For anything not worth parsing: hash it, alert on
change. Never breaks, but tells you *something* moved, not what. Always pass
`strip_patterns` for timestamps and counters or every check fires:

```python
h, _ = ex.page_fingerprint(url, selector="#jobs",
                           strip_patterns=[r"\d{4}-\d{2}-\d{2}T[\d:]+Z"])
```

## JS-rendered pages

If `discover.py` reports a near-empty shell and finds no payload, the listings
are fetched after page load. Two options:

- **Find the XHR.** DevTools > Network > Fetch/XHR, reload, look for the call
  returning job JSON. Right-click > Copy as cURL, replay it with `requests`.
  Almost always possible, and far lighter than a browser.
- **Playwright**, if the endpoint is signed or session-gated. Works on GitHub
  Actions with `playwright install --with-deps chromium` in the workflow, but
  it's slow and adds ~400MB to each run. Use it for the handful of sites that
  genuinely need it, not as a default.

## Extra ATS fetchers in extractors.py

Workable, BambooHR, Recruitee, Eightfold. Confidence is noted in each
docstring — these are less standardized than the big four, so verify with
`discover.py` before adding a company.

Not worth automating: **iCIMS, Taleo, SuccessFactors, Phenom**. No clean public
JSON, heavy session state, frequent markup churn. Fingerprint them, or set a
calendar reminder.

## Being a good client

- One request every few seconds, and don't parallelize across a single host.
  Your entire target list is maybe a few hundred requests twice a day — trivial
  load if paced, and enough to get IP-blocked if fired all at once.
- Check `robots.txt`. `discover.py` prints any `Disallow` covering job paths.
- Set a real User-Agent. Some sites 403 obvious defaults; more importantly it
  lets an admin see who you are rather than guessing.
- Cache aggressively. If a board's postings haven't changed, don't re-fetch
  detail pages.
- Public postings a company actively wants indexed are the least contentious
  thing to read. Anything behind a login is a different situation — don't.

---

# Part 3: the target list

`targets.json` holds 303 companies across 14 categories, plus 19 government
portals. It is a list of **names, not slugs** — deliberately.

## Why there are no slugs in the list

ATS slugs aren't derivable from a company name (`bms` vs `bristolmyerssquibb`),
and companies migrate between Greenhouse/Lever/Ashby regularly. A handwritten
slug list would be wrong often enough that you couldn't tell a bad slug from a
company with no current openings — the worst kind of failure, because it's
silent.

So `resolve.py` discovers them by probing the real APIs and keeps only what
responds. Everything in `resolved.json` was confirmed live.

## Usage

```bash
python resolve.py                              # list categories
python resolve.py --category fintech_mission   # start here
python resolve.py --priority 1                 # all high-priority categories
python resolve.py --report                     # what landed, no network
python resolve.py --write-config               # emit config.json
```

Results cache to `resolved.json` after every company, so it's interruptible and
resumable. Re-running skips anything already resolved.

Budget: a hit costs a handful of requests, a miss costs up to 42. Start with one
category to see the hit rate before running `--all`.

## Fortune 500 → use the Workday path

Categories flagged `expect_workday` (banks, pharma, big tech, consulting, retail)
are skipped by slug probing, because Workday configs can't be guessed — tenant,
cluster number, and site name all vary independently. But all three are visible
in the careers URL:

```
https://prudential.wd5.myworkdayjobs.com/en-US/Prudential_Careers
         └─tenant  └wd            └──── site ────┘
```

So paste the URL instead:

```bash
python resolve.py --workday "Prudential" "https://prudential.wd5.myworkdayjobs.com/en-US/Prudential_Careers"
```

It parses, verifies against the live API, prints matching postings, and caches.
Two minutes per company, and it actually works.

## Categories

| Category | Pri | N | Why |
|---|---|---|---|
| `fintech_mission` | 1 | 20 | CDFI/financial-inclusion. Your Spring Bank background is a rare match. |
| `fintech_core` | 1 | 35 | Payments, wealth, banking infra |
| `ux_agencies` | 1 | 33 | Design studios and consultancies |
| `civic_tech` | 1 | 15 | Government contractors. Heavy UX research. |
| `accessibility` | 1 | 10 | Continuous with your smart-glasses lab work |
| `banks_insurance` | 1 | 30 | Fortune 500 finance, formal summer programs |
| `big_tech` | 1 | 31 | Named UX Research / Product Design internship tracks |
| `product_saas` | 2 | 31 | Design-led software companies |
| `health_tech` | 2 | 16 | NYC-dense |
| `pharma_nj` | 2 | 15 | Densest pharma corridor in the country, commutable |
| `media_retail_cpg` | 2 | 33 | NY/NJ Fortune 500 |
| `consulting` | 2 | 10 | Deloitte Digital, Accenture Song, BCG X |
| `edtech` | 3 | 12 | |
| `quant_trading` | 3 | 12 | Few design roles, exceptional pay |

## Government

`targets.json` → `government_portals`. Two are automated:

- **USAJOBS** — built into `internship_watch.py`. Covers the federal Pathways
  Internship Program. Needs a free key from developer.usajobs.gov.
- **NYC Jobs** — `extractors.fetch_nyc_jobs()` hits NYC Open Data's Socrata API,
  which carries every city-agency posting (OTI, EDC, DDC, H+H, Comptroller...).
  No key needed at this volume.

The other 17 (Port Authority, NJ Office of Innovation, MTA, NY Fed, FDIC, SEC,
UN) run on portals with no usable API. They're listed with URLs for manual
checking. The NJ Office of Innovation and the New York Fed are worth checking by
hand regardless — both hire researchers, both are small enough that a scraper
wouldn't help much anyway.

Note: 18F and USDS were the classic federal design-research entry points, and
both were significantly restructured during 2025. Verify their current status
before building them in. The private civic-tech firms in `civic_tech` do much of
the same work and hire more predictably.

## When a company doesn't resolve

Not a bug. Three likely causes, in order:

1. They're on Workday/iCIMS/Taleo → use `--workday`, or check manually.
2. They use a custom careers site → `python discover.py <careers-url>`.
3. Small studios (Pentagram, Local Projects, Collins) often have no ATS at all
   and hire interns by portfolio email. For those the scraper was never the
   right tool — email them in September.
