# Resolving the 278 unresolved companies

**What this file is:** everything needed to finish resolving `targets.json` without
doing 278 manual Google searches. Drop this in a project, point an AI agent at it,
and tell it to follow the Runbook below.

**Why it's built this way.** ATS slugs go stale — companies migrate platforms,
Workday tenants get renamed, job boards get retired. A hand-typed list of 278 URLs
is wrong within a couple of months and you have no way to tell which entries rotted.
So instead of a static list, this is a **resolver that discovers and then verifies**
each endpoint against the live jobs API. Nothing gets written to your config unless
it actually returns job postings right now. Re-run it any time to re-verify.

What's pre-loaded here (the research that *is* worth hand-doing):

- Company → primary domain for all 277 companies, so the resolver knows where to look.
- An ATS hint for 195 of them (69 Workday, 101 Greenhouse, 15 in-house, plus Lever/Ashby/Eightfold/Oracle).
- Direct careers-search URLs for the 15 companies that run their own recruiting
  stack and will never match an ATS fingerprint.
- Corrections to the platform guesses in your current doc — see Corrections below.

---

## Runbook

```bash
pip install requests

# save the two code blocks at the bottom of this file as seeds.tsv and auto_resolve.py
python auto_resolve.py --priority 1          # start here, ~88 companies, a few minutes
python auto_resolve.py --priority 2 --resume
python auto_resolve.py --priority 3 --resume
python auto_resolve.py --deep --resume       # wider Workday brute force for stragglers
```

Then feed the results into your existing tooling:

```bash
bash out/commands.sh          # runs resolve.py --workday for every Workday hit
python resolve.py --write-config
python internship_watch.py --dry-run
```

Outputs land in `out/`:

| File | What's in it |
|---|---|
| `resolved.json` | every company, machine-readable, with the verified API endpoint |
| `resolved.md` | readable table: company, ATS, slug, live posting count |
| `unresolved.md` | what still needs eyes, with the careers pages already checked |
| `commands.sh` | ready-to-run `resolve.py --workday` lines |

`--resume` skips anything already resolved, so it's safe to stop and restart.

### How it resolves each company

1. **Sniff** — fetches the homepage, follows careers links one hop, tries ~14 common
   careers paths, then regexes the HTML for fingerprints of 17 ATS platforms.
   This catches most companies because the careers page almost always links to,
   iframes, or redirects to the real board.
2. **Guess** — if sniffing came up empty, probes likely slugs against the public
   JSON APIs of Greenhouse, Lever, Ashby, SmartRecruiters and Workable, using
   several normalizations of the company name (`bristolmyerssquibb`,
   `bristol-myers-squibb`, `bms`, `bristol`...).
3. **Brute force (Workday only)** — Workday tenants genuinely can't be guessed by
   hand, but the CXS endpoint is public and unauthenticated, so tenant × host ×
   site-name combinations can be tested in bulk. `--deep` widens this to 13 hosts
   × 20 site names.
4. **Verify** — every candidate is confirmed by calling the real jobs API and
   counting postings. A slug that returns zero jobs is treated as a miss.

The verified endpoints it uses:

| ATS | Verification endpoint |
|---|---|
| Workday | `POST {tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` |
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{slug}/jobs` |
| Lever | `api.lever.co/v0/postings/{slug}?mode=json` |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{slug}` |
| SmartRecruiters | `api.smartrecruiters.com/v1/companies/{slug}/postings` |
| Workable | `apply.workable.com/api/v1/widget/accounts/{slug}` |
| Recruitee | `{slug}.recruitee.com/api/offers/` |
| Eightfold | `{slug}.eightfold.ai/api/apply/v2/jobs?domain={domain}` |

iCIMS, Taleo, Oracle Recruiting, Phenom, Jobvite and in-house stacks have no clean
public JSON board. Those come back marked `scrape` with the correct search URL
attached, ready for change-detection.

### Note on `myworkdaysite.com`

Newer Workday tenants sit on `myworkdaysite.com` rather than `myworkdayjobs.com`.
The resolver handles both, but if `resolve.py` on your side only accepts
`myworkdayjobs.com`, loosen that check or `commands.sh` will reject valid hits.

---

## Corrections to the current doc

These matter because they're where the existing list would send you down dead ends.

**Filed under "Workday" but almost certainly not Workday.** All of these run their
own recruiting stack or a different platform, so brute-forcing a Workday tenant for
them will burn time and find nothing. The resolver already routes them to their real
careers search page instead.

Amazon · Apple · Google · Meta · Microsoft · IBM · Oracle · Uber · Netflix ·
Goldman Sachs · Morgan Stanley · JPMorgan Chase · Citi · Bank of America ·
Bloomberg · The Walt Disney Company

**Filed under "Workday" but more likely a standard ATS** (the resolver will confirm
which): Etsy, Snap, Vimeo, Warby Parker, Condé Nast, The New York Times.

**Consulting firms** (Deloitte, EY, PwC, KPMG, McKinsey, Bain, Accenture) all use
custom or hybrid portals rather than a clean Workday board, and their design arms
(Deloitte Digital, Accenture Song, McKinsey Design, BCG X, Bain Vector) usually post
under the parent firm's listing — so filter by role title, not by employer name.

**Duplicate.** "Prudential Financial" (Priority 1, banks_insurance) and "Prudential"
(Priority 2, media_retail_cpg) are the same company. Deduped here, which is why the
seed list has 277 rows rather than 278.

**Probably not worth a watcher slot.** Bed Bath & Beyond (brand sold, operates as an
Overstock property), MediaMath (assets sold off after 2023 bankruptcy), Vroom (wound
down e-commerce operations in 2024). Marked `defunct` in the seeds so they're skipped
— delete the flag if you want them checked anyway.

**U.S. Digital Response** is volunteer-based rather than a paid-internship pipeline.
Worth engaging with, but it won't behave like the rest of the list.

Your existing note about 18F and USDS is worth keeping in view — the civic-tech
contractors in that category (Nava, Ad Hoc, Coforma, Truss, Skylight, Fearless,
Civilla) do very similar work and hire on a normal cycle.

---

## Government portals — manual, no ATS

These don't run on standard ATS platforms and need periodic manual checks. Pulled
forward from the original doc unchanged; the resolver doesn't touch them.

| Organization | URL | Note |
|---|---|---|
| Federal Reserve Bank of New York | https://www.newyorkfed.org/careers | Strong internship program; CDFI background is directly relevant |
| NJ Office of Innovation | https://innovation.nj.gov/ | Actively hires designers and user researchers. Small team, high signal |
| NYC Office of Technology & Innovation | https://www.nyc.gov/content/oti/pages/ | Best NYC civic UX entry point |
| Port Authority of NY & NJ | https://www.panynj.gov/corporate/en/careers.html | Bi-state, commutable, formal summer internship |
| MTA | https://new.mta.info/careers | Formal internship program, large customer-experience org |
| NYC Economic Development Corporation | https://edc.nyc/careers | |
| NJ Civil Service Commission | https://www.nj.gov/csc/ | |
| NJ Transit | https://www.njtransit.com/careers | |
| NJ Economic Development Authority | https://www.njeda.gov/careers/ | |
| New York State ITS | https://statejobs.ny.gov/ | |
| FDIC | https://www.fdic.gov/about/careers/ | Financial regulator, CDFI-adjacent policy work |
| OCC | https://www.occ.gov/careers/ | |
| SEC | https://www.sec.gov/careers | |
| FINRA | https://www.finra.org/careers | |
| United Nations | https://careers.un.org/ | Typically unpaid — check before investing time |
| UNICEF | https://www.unicef.org/careers/ | |
| World Bank | https://www.worldbank.org/en/about/careers | |

The Fed, the Port Authority and NJ Office of Innovation are the three with the
clearest match to a UX-research-plus-community-banking background, and all three
recruit on fixed calendars rather than rolling — worth a calendar reminder rather
than a scraper.

---

## Troubleshooting

**Lots of unresolved on the first pass.** Normal. Run `--deep`, then check
`unresolved.md` — it lists the careers pages the resolver already fetched, so a human
pass is just opening those and looking for an ATS domain in the URL bar.

**Rate limiting / connection errors.** Drop `--workers` to 3. Greenhouse and Lever
are tolerant; Workday CXS endpoints are the ones that will start refusing.

**A resolved company returns zero jobs later.** That's the point of storing the API
URL — it means they paused hiring or migrated. Re-run with `--only "Company Name"`.

**Something resolves to the wrong company.** Slug collisions happen (short names
especially). `resolved.json` records how each one was found; anything with
`"method": "guess"` deserves a spot-check, anything with `"method": "sniff"` came off
the company's own careers page and is reliable.

---

## File 1 — `seeds.tsv`

Tab-separated: `name`, `domain`, `category`, `priority`, `hint`. The hint biases the
search order; it doesn't override verification, so a wrong hint costs a little time
but can't produce a wrong result. Edit freely — add a company by adding a row.

```tsv
Adobe	adobe.com	big_tech	1	workday
AIG	aig.com	banks_insurance	1	workday
Ally	ally.com	banks_insurance	1	workday
Amazon	amazon.com	big_tech	1	custom
American Express	americanexpress.com	banks_insurance	1	
Apple	apple.com	big_tech	1	custom
Bank of America	bankofamerica.com	banks_insurance	1	custom
BlackRock	blackrock.com	banks_insurance	1	workday
Chubb	chubb.com	banks_insurance	1	workday
Citi	citi.com	banks_insurance	1	custom
Discover	discover.com	banks_insurance	1	workday
Etsy	etsy.com	big_tech	1	greenhouse
Federal Reserve Bank of New York	newyorkfed.org	banks_insurance	1	workday
Goldman Sachs	goldmansachs.com	banks_insurance	1	custom
Google	google.com	big_tech	1	custom
IBM	ibm.com	big_tech	1	custom
Intuit	intuit.com	big_tech	1	workday
JPMorgan Chase	jpmorganchase.com	banks_insurance	1	custom
Mastercard	mastercard.com	banks_insurance	1	workday
Meta	meta.com	big_tech	1	custom
Microsoft	microsoft.com	big_tech	1	custom
Moody's	moodys.com	banks_insurance	1	workday
Morgan Stanley	morganstanley.com	banks_insurance	1	custom
Nasdaq	nasdaq.com	banks_insurance	1	workday
Netflix	netflix.com	big_tech	1	eightfold
Oracle	oracle.com	big_tech	1	oracle
Prudential Financial	prudential.com	banks_insurance	1	workday
S&P Global	spglobal.com	banks_insurance	1	workday
Salesforce	salesforce.com	big_tech	1	workday
Snap	snap.com	big_tech	1	greenhouse
Synchrony	synchrony.com	banks_insurance	1	workday
TIAA	tiaa.org	banks_insurance	1	workday
Travelers	travelers.com	banks_insurance	1	workday
Uber	uber.com	big_tech	1	custom
Vanguard	vanguard.com	banks_insurance	1	workday
Vimeo	vimeo.com	big_tech	1	greenhouse
Warby Parker	warbyparker.com	big_tech	1	greenhouse
Accion	accion.org	fintech_mission	1	
Ad Hoc	adhocteam.us	civic_tech	1	greenhouse
Addepar	addepar.com	fintech_core	1	greenhouse
Aira	aira.io	accessibility	1	
American Foundation for the Blind	afb.org	accessibility	1	
Athletics	athleticsnyc.com	ux_agencies	1	
Barrel	barrelny.com	ux_agencies	1	
Be My Eyes	bemyeyes.com	accessibility	1	
Big Human	bighuman.com	ux_agencies	1	
Civilla	civilla.com	civic_tech	1	
Coforma	coforma.io	civic_tech	1	greenhouse
Collins	wearecollins.com	ux_agencies	1	
Deel	deel.com	fintech_core	1	greenhouse
Dentsu	dentsu.com	ux_agencies	1	
Deque Systems	deque.com	accessibility	1	
Designit	designit.com	ux_agencies	1	
Droga5	droga5.com	ux_agencies	1	
EPAM	epam.com	ux_agencies	1	
Esusu	esusurent.com	fintech_mission	1	greenhouse
Fearless	fearless.tech	civic_tech	1	greenhouse
Flywire	flywire.com	fintech_core	1	greenhouse
Grameen America	grameenamerica.org	fintech_mission	1	
Greenwood	bankgreenwood.com	fintech_mission	1	
Helen Keller Services	helenkeller.org	accessibility	1	
Kiva	kiva.org	fintech_mission	1	greenhouse
LendingClub	lendingclub.com	fintech_mission	1	greenhouse
Lippincott	lippincott.com	ux_agencies	1	
Local Projects	localprojects.net	ux_agencies	1	
Marqeta	marqeta.com	fintech_core	1	greenhouse
MoCaFi	mocafi.com	fintech_mission	1	
MoneyLion	moneylion.com	fintech_mission	1	greenhouse
Nava PBC	navapbc.com	civic_tech	1	greenhouse
Navan	navan.com	fintech_core	1	greenhouse
Pentagram	pentagram.com	ux_agencies	1	manual
Petal	petalcard.com	fintech_mission	1	greenhouse
Publicis Sapient	publicissapient.com	ux_agencies	1	
Rangle	rangle.io	ux_agencies	1	
Remitly	remitly.com	fintech_core	1	greenhouse
Rippling	rippling.com	fintech_core	1	
Siegel+Gale	siegelgale.com	ux_agencies	1	
Skylight	skylight.digital	civic_tech	1	
Slalom	slalom.com	ux_agencies	1	
Stash	stash.com	fintech_mission	1	greenhouse
Thoughtbot	thoughtbot.com	ux_agencies	1	
TPGi	tpgi.com	accessibility	1	
Truss	truss.works	civic_tech	1	greenhouse
U.S. Digital Response	usdigitalresponse.org	civic_tech	1	
ustwo	ustwo.com	ux_agencies	1	
Varo	varomoney.com	fintech_mission	1	greenhouse
Vispero	vispero.com	accessibility	1	
Work and Co	work.co	ux_agencies	1	
Accenture	accenture.com	consulting	2	
ADP	adp.com	media_retail_cpg	2	workday
AstraZeneca	astrazeneca.com	pharma_nj	2	workday
Bain	bain.com	consulting	2	
Bayer	bayer.com	pharma_nj	2	workday
Becton Dickinson	bd.com	pharma_nj	2	workday
Bloomberg	bloomberg.com	media_retail_cpg	2	custom
Booking Holdings	bookingholdings.com	media_retail_cpg	2	workday
Boston Consulting Group	bcg.com	consulting	2	workday
Bristol Myers Squibb	bms.com	pharma_nj	2	workday
Campbell's	campbellsoupcompany.com	media_retail_cpg	2	workday
Church & Dwight	churchdwight.com	media_retail_cpg	2	workday
Cognizant	cognizant.com	media_retail_cpg	2	workday
Colgate-Palmolive	colgatepalmolive.com	media_retail_cpg	2	workday
Comcast NBCUniversal	comcast.com	media_retail_cpg	2	
Conde Nast	condenast.com	media_retail_cpg	2	greenhouse
Deloitte	deloitte.com	consulting	2	
Delta Air Lines	delta.com	media_retail_cpg	2	workday
Eli Lilly	lilly.com	pharma_nj	2	workday
Estee Lauder	elcompanies.com	media_retail_cpg	2	workday
EY	ey.com	consulting	2	
Foot Locker	footlocker.com	media_retail_cpg	2	workday
Gartner	gartner.com	consulting	2	workday
GSK	gsk.com	pharma_nj	2	workday
Hilton	hilton.com	media_retail_cpg	2	workday
JetBlue	jetblue.com	media_retail_cpg	2	workday
Johnson & Johnson	jnj.com	pharma_nj	2	workday
KPMG	kpmg.com	consulting	2	
L'Oreal USA	loreal.com	media_retail_cpg	2	workday
Macy's	macysinc.com	media_retail_cpg	2	workday
Marriott	marriott.com	media_retail_cpg	2	workday
McKinsey	mckinsey.com	consulting	2	
Merck	merck.com	pharma_nj	2	workday
Mondelez	mondelezinternational.com	media_retail_cpg	2	workday
Novartis	novartis.com	pharma_nj	2	workday
Novo Nordisk	novonordisk.com	pharma_nj	2	workday
Organon	organon.com	pharma_nj	2	workday
Paramount	paramount.com	media_retail_cpg	2	workday
PepsiCo	pepsico.com	media_retail_cpg	2	workday
Pfizer	pfizer.com	pharma_nj	2	workday
PVH	pvh.com	media_retail_cpg	2	workday
PwC	pwc.com	consulting	2	
Ralph Lauren	ralphlauren.com	media_retail_cpg	2	workday
Regeneron	regeneron.com	pharma_nj	2	workday
Sanofi	sanofi.com	pharma_nj	2	workday
Takeda	takeda.com	pharma_nj	2	workday
Tapestry	tapestry.com	media_retail_cpg	2	workday
The New York Times	nytco.com	media_retail_cpg	2	greenhouse
The Walt Disney Company	disney.com	media_retail_cpg	2	custom
Unilever	unilever.com	media_retail_cpg	2	workday
United Airlines	united.com	media_retail_cpg	2	workday
Verizon	verizon.com	media_retail_cpg	2	
Warner Bros Discovery	wbd.com	media_retail_cpg	2	workday
Wayfair	wayfair.com	media_retail_cpg	2	
ZS Associates	zs.com	consulting	2	
Airtable	airtable.com	product_saas	2	greenhouse
Alma	helloalma.com	health_tech	2	greenhouse
Amplitude	amplitude.com	product_saas	2	greenhouse
Asana	asana.com	product_saas	2	greenhouse
AT&T	att.com	fortune500_nycnj	2	
Atlassian	atlassian.com	product_saas	2	
Autodesk	autodesk.com	best_places_to_work	2	workday
Avis Budget Group	avisbudgetgroup.com	fortune500_nycnj	2	
Babylist	babylist.com	best_places_to_work	2	greenhouse
Barnes & Noble	barnesandnoble.com	fortune500_nycnj	2	
Bed Bath & Beyond	bedbathandbeyond.com	fortune500_nycnj	2	defunct
Broadridge	broadridge.com	fortune500_nycnj	2	workday
Bumble	bumble.com	product_saas	2	greenhouse
Calm	calm.com	product_saas	2	greenhouse
Canva	canva.com	product_saas	2	lever
Casper	casper.com	best_places_to_work	2	greenhouse
Cedar	cedar.com	health_tech	2	greenhouse
Compass	compass.com	fortune500_nycnj	2	greenhouse
Coty	coty.com	fortune500_nycnj	2	workday
CrowdStrike	crowdstrike.com	best_places_to_work	2	greenhouse
DocuSign	docusign.com	best_places_to_work	2	
DoorDash	doordash.com	product_saas	2	greenhouse
Dropbox	dropbox.com	product_saas	2	greenhouse
Duolingo	duolingo.com	product_saas	2	greenhouse
Elastic	elastic.co	best_places_to_work	2	greenhouse
Epic Games	epicgames.com	best_places_to_work	2	greenhouse
FactSet	factset.com	fortune500_nycnj	2	workday
Figma	figma.com	product_saas	2	greenhouse
Fiserv	fiserv.com	fortune500_nycnj	2	workday
Flatiron Health	flatiron.com	health_tech	2	greenhouse
Framer	framer.com	product_saas	2	ashby
Glassdoor	glassdoor.com	best_places_to_work	2	greenhouse
Glossier	glossier.com	best_places_to_work	2	greenhouse
Grubhub	grubhub.com	fortune500_nycnj	2	greenhouse
Hanes	hanes.com	fortune500_nycnj	2	
Harry's	harrys.com	best_places_to_work	2	greenhouse
Headspace	headspace.com	product_saas	2	greenhouse
Headway	headway.co	health_tech	2	greenhouse
Henry Schein	henryschein.com	fortune500_nycnj	2	
Hess	hess.com	fortune500_nycnj	2	
Hinge	hinge.co	product_saas	2	greenhouse
Hinge Health	hingehealth.com	health_tech	2	greenhouse
Honeywell	honeywell.com	fortune500_nycnj	2	workday
HubSpot	hubspot.com	product_saas	2	greenhouse
IFF	iff.com	fortune500_nycnj	2	workday
iHeartMedia	iheartmedia.com	fortune500_nycnj	2	
Included Health	includedhealth.com	health_tech	2	greenhouse
Indeed	indeed.com	best_places_to_work	2	
Instacart	instacart.com	product_saas	2	greenhouse
Interpublic Group	interpublic.com	fortune500_nycnj	2	
K Health	khealth.com	health_tech	2	greenhouse
Kindbody	kindbody.com	health_tech	2	greenhouse
Klaviyo	klaviyo.com	product_saas	2	greenhouse
Komodo Health	komodohealth.com	health_tech	2	greenhouse
Linear	linear.app	product_saas	2	ashby
LiveRamp	liveramp.com	best_places_to_work	2	greenhouse
Maven Clinic	mavenclinic.com	health_tech	2	greenhouse
MediaMath	mediamath.com	best_places_to_work	2	defunct
Mixpanel	mixpanel.com	product_saas	2	greenhouse
MSCI	msci.com	fortune500_nycnj	2	workday
MSG Entertainment	msg.com	fortune500_nycnj	2	
NBCUniversal	nbcuniversal.com	fortune500_nycnj	2	
Noom	noom.com	best_places_to_work	2	greenhouse
Notion	notion.com	product_saas	2	greenhouse
Okta	okta.com	best_places_to_work	2	greenhouse
Omada Health	omadahealth.com	health_tech	2	greenhouse
Omnicom Group	omnicomgroup.com	fortune500_nycnj	2	
Otis	otis.com	fortune500_nycnj	2	workday
Palo Alto Networks	paloaltonetworks.com	best_places_to_work	2	
Patreon	patreon.com	product_saas	2	greenhouse
Rent the Runway	renttherunway.com	best_places_to_work	2	greenhouse
Retool	retool.com	product_saas	2	greenhouse
Revlon	revlon.com	fortune500_nycnj	2	
Ro	ro.co	health_tech	2	greenhouse
Roblox	roblox.com	best_places_to_work	2	greenhouse
Saks	saks.com	fortune500_nycnj	2	
Scholastic	scholastic.com	fortune500_nycnj	2	
Sealed Air	sealedair.com	fortune500_nycnj	2	workday
ServiceNow	servicenow.com	best_places_to_work	2	
Shopify	shopify.com	product_saas	2	
Simon & Schuster	simonandschuster.com	fortune500_nycnj	2	
Snowflake	snowflake.com	best_places_to_work	2	greenhouse
Sony Music	sonymusic.com	fortune500_nycnj	2	
Splunk	splunk.com	best_places_to_work	2	
Spring Health	springhealth.com	health_tech	2	greenhouse
Stitch Fix	stitchfix.com	best_places_to_work	2	greenhouse
Substack	substack.com	product_saas	2	greenhouse
T-Mobile	t-mobile.com	fortune500_nycnj	2	
Take-Two Interactive	take2games.com	best_places_to_work	2	
Talkspace	talkspace.com	health_tech	2	greenhouse
The Trade Desk	thetradedesk.com	best_places_to_work	2	greenhouse
Thirty Madison	thirtymadison.com	best_places_to_work	2	greenhouse
ThredUp	thredup.com	best_places_to_work	2	greenhouse
Tiffany & Co	tiffany.com	fortune500_nycnj	2	
Twilio	twilio.com	product_saas	2	greenhouse
Twitch	twitch.tv	best_places_to_work	2	greenhouse
Unity	unity.com	best_places_to_work	2	greenhouse
Vercel	vercel.com	product_saas	2	ashby
Verisk	verisk.com	fortune500_nycnj	2	
Vroom	vroom.com	best_places_to_work	2	defunct
Warner Music	wmg.com	fortune500_nycnj	2	
Webflow	webflow.com	product_saas	2	greenhouse
WeWork	wework.com	fortune500_nycnj	2	
Wix	wix.com	product_saas	2	
Workday	workday.com	best_places_to_work	2	workday
Zapier	zapier.com	product_saas	2	greenhouse
Zillow	zillow.com	fortune500_nycnj	2	
Zocdoc	zocdoc.com	health_tech	2	greenhouse
Zoom	zoom.com	product_saas	2	
Zscaler	zscaler.com	best_places_to_work	2	greenhouse
2U	2u.com	edtech	3	
Amplify	amplify.com	edtech	3	greenhouse
AQR Capital	aqr.com	quant_trading	3	greenhouse
Bridgewater Associates	bridgewater.com	quant_trading	3	greenhouse
Citadel	citadel.com	quant_trading	3	greenhouse
Codecademy	codecademy.com	edtech	3	greenhouse
Coursera	coursera.org	edtech	3	greenhouse
DE Shaw	deshaw.com	quant_trading	3	
General Assembly	generalassemb.ly	edtech	3	greenhouse
Guild	guild.com	edtech	3	greenhouse
IMC Trading	imc.com	quant_trading	3	
Jane Street	janestreet.com	quant_trading	3	custom
Khan Academy	khanacademy.org	edtech	3	greenhouse
MasterClass	masterclass.com	edtech	3	greenhouse
Millennium	mlp.com	quant_trading	3	
Newsela	newsela.com	edtech	3	greenhouse
Optiver	optiver.com	quant_trading	3	greenhouse
Point72	point72.com	quant_trading	3	greenhouse
Quizlet	quizlet.com	edtech	3	greenhouse
Skillshare	skillshare.com	edtech	3	greenhouse
Susquehanna	sig.com	quant_trading	3	
Two Sigma	twosigma.com	quant_trading	3	greenhouse
Udemy	udemy.com	edtech	3	greenhouse
Virtu Financial	virtu.com	quant_trading	3	
```

---

## File 2 — `auto_resolve.py`

```python
#!/usr/bin/env python3
"""
auto_resolve.py — find and VERIFY the ATS endpoint for every unresolved company.

Strategy per company:
  1. SNIFF   fetch the careers page(s), regex for ATS fingerprints in the HTML
             (Workday, Greenhouse, Lever, Ashby, SmartRecruiters, Workable,
              Recruitee, Eightfold, iCIMS, Taleo, Oracle, Phenom, Jobvite...)
  2. GUESS   if sniffing found nothing, probe likely slugs against each ATS's
             public JSON API (company name normalized a few different ways)
  3. BRUTE   for Workday only: probe tenant x wd-host x site-name combinations
             (--deep). Workday tenants are unguessable by hand but trivial to
             brute force because the CXS endpoint is public.
  4. VERIFY  every candidate is confirmed by hitting the real jobs API and
             counting postings. Nothing is written unless it returns jobs.

Outputs (in --out dir):
  resolved.json      machine-readable, keyed by company
  resolved.md        human-readable table
  unresolved.md      what still needs a human, with the careers URL to check
  commands.sh        ready-to-run `python resolve.py --workday ...` lines

Usage:
  pip install requests
  python auto_resolve.py                 # normal pass
  python auto_resolve.py --deep          # + Workday brute force (slower)
  python auto_resolve.py --only "Pfizer,Merck"
  python auto_resolve.py --priority 1
  python auto_resolve.py --resume        # skip companies already in resolved.json
"""

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/json,*/*"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

PRINT_LOCK = threading.Lock()


def log(*a):
    with PRINT_LOCK:
        print(*a, flush=True)


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------

def get(url, timeout=20, **kw):
    try:
        return SESSION.get(url, timeout=timeout, allow_redirects=True, **kw)
    except Exception:
        return None


def post_json(url, payload, timeout=20):
    try:
        return SESSION.post(
            url, json=payload, timeout=timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
    except Exception:
        return None


# --------------------------------------------------------------------------
# ATS fingerprints found in careers-page HTML
# --------------------------------------------------------------------------

PATTERNS = [
    # Workday: tenant.wdN.myworkdayjobs.com[/en-US]/SiteName
    ("workday", re.compile(
        r"https?://([a-z0-9][a-z0-9\-]*)\.(wd\d+)\.(myworkdayjobs|myworkdaysite)\.com"
        r"(?:/wday/cxs/[^/]+)?(?:/[a-z]{2}-[A-Z]{2})?/([A-Za-z0-9_\-]+)", re.I)),
    ("greenhouse", re.compile(
        r"(?:job-)?boards(?:-api)?\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_\-]+)", re.I)),
    ("greenhouse", re.compile(r"greenhouse\.io/embed/job_board/js\?for=([a-z0-9_\-]+)", re.I)),
    ("lever", re.compile(r"jobs\.(?:eu\.)?lever\.co/([a-z0-9\-\.]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([a-z0-9\-\.]+)", re.I)),
    ("smartrecruiters", re.compile(
        r"(?:careers|jobs|api)\.smartrecruiters\.com/(?:v1/companies/)?([A-Za-z0-9_\-]+)", re.I)),
    ("workable", re.compile(r"apply\.workable\.com/([a-z0-9\-]+)", re.I)),
    ("recruitee", re.compile(r"([a-z0-9\-]+)\.recruitee\.com", re.I)),
    ("eightfold", re.compile(r"([a-z0-9\-]+)\.eightfold\.ai", re.I)),
    ("rippling", re.compile(r"([a-z0-9\-]+)\.rippling-ats\.com", re.I)),
    ("jobvite", re.compile(r"jobs\.jobvite\.com/([a-z0-9\-]+)", re.I)),
    ("bamboohr", re.compile(r"([a-z0-9\-]+)\.bamboohr\.com/(?:careers|jobs)", re.I)),
    ("paylocity", re.compile(r"recruiting\.paylocity\.com/recruiting/jobs/All/([a-z0-9\-]+)", re.I)),
    ("teamtailor", re.compile(r"([a-z0-9\-]+)\.teamtailor\.com", re.I)),
    # scrape-only platforms: capture the host so change-detection can be pointed at it
    ("icims", re.compile(r"(https?://[a-z0-9\-]+\.icims\.com/jobs[^\"'\s]*)", re.I)),
    ("taleo", re.compile(r"(https?://[a-z0-9\-\.]*taleo\.net/[^\"'\s]*)", re.I)),
    ("oracle", re.compile(r"(https?://[a-z0-9\-\.]+\.oraclecloud\.com/hcmUI/CandidateExperience[^\"'\s]*)", re.I)),
    ("phenom", re.compile(r"(https?://[a-z0-9\-\.]+/(?:widgets|search-results)\?[^\"'\s]*)", re.I)),
]

# tokens that show up inside Workday/GH URLs but are never a real slug/site
JUNK = {"www", "en", "en-us", "static", "cdn", "assets", "img", "images", "app",
        "api", "js", "css", "login", "signin", "home", "index", "null", "undefined",
        "embed", "job_board", "jobs", "job", "boards", "v1", "search", "widget"}


def sniff(html):
    """Return list of (ats, capture...) tuples found in a blob of HTML."""
    hits = []
    for ats, rx in PATTERNS:
        for m in rx.finditer(html):
            groups = tuple(g for g in m.groups() if g)
            if not groups:
                continue
            if groups[0].lower() in JUNK:
                continue
            hits.append((ats, groups))
    # de-dupe, preserve order
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


# --------------------------------------------------------------------------
# Careers-page discovery
# --------------------------------------------------------------------------

CAREER_PATHS = [
    "/careers", "/careers/", "/jobs", "/company/careers", "/about/careers",
    "/en/careers", "/us/en/careers", "/careers/jobs", "/careers/search",
    "/about-us/careers", "/join-us", "/work-with-us", "/company/jobs",
    "/careers/open-positions", "/about/jobs",
]

CAREER_LINK_RX = re.compile(
    r'href=["\']([^"\']*(?:career|job|join-us|work-with-us|opportunit)[^"\']*)["\']', re.I)


def collect_html(domain, max_pages=8):
    """Fetch homepage + likely careers pages, follow careers links one hop."""
    blobs = []
    tried = set()

    def fetch(url):
        if url in tried or len(tried) > max_pages:
            return None
        tried.add(url)
        r = get(url)
        if r is not None and r.status_code < 400 and r.text:
            blobs.append((r.url, r.text))
            return r
        return None

    root = f"https://{domain}"
    home = fetch(root)

    # follow careers-ish links off the homepage
    if home is not None and home.text:
        links = CAREER_LINK_RX.findall(home.text)[:40]
        cands = []
        for href in links:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = root + href
            elif not href.startswith("http"):
                continue
            if "career" in href.lower() or "/jobs" in href.lower() or "join-us" in href.lower():
                cands.append(href.split("#")[0])
        for u in list(dict.fromkeys(cands))[:4]:
            fetch(u)

    for p in CAREER_PATHS:
        if len(tried) > max_pages:
            break
        fetch(root + p)

    return blobs


# --------------------------------------------------------------------------
# Verification — every ATS below has a public JSON endpoint
# --------------------------------------------------------------------------

def v_greenhouse(slug):
    r = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("jobs", []))
    except Exception:
        return None
    return {"ats": "greenhouse", "slug": slug, "count": n,
            "api": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
            "human": f"https://job-boards.greenhouse.io/{slug}"} if n else None


def v_lever(slug):
    r = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if r is None or r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    if not isinstance(data, list) or not data:
        return None
    return {"ats": "lever", "slug": slug, "count": len(data),
            "api": f"https://api.lever.co/v0/postings/{slug}?mode=json",
            "human": f"https://jobs.lever.co/{slug}"}


def v_ashby(slug):
    r = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("jobs", []))
    except Exception:
        return None
    return {"ats": "ashby", "slug": slug, "count": n,
            "api": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
            "human": f"https://jobs.ashbyhq.com/{slug}"} if n else None


def v_smartrecruiters(slug):
    r = get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=10")
    if r is None or r.status_code != 200:
        return None
    try:
        j = r.json()
        n = j.get("totalFound", len(j.get("content", [])))
    except Exception:
        return None
    return {"ats": "smartrecruiters", "slug": slug, "count": n,
            "api": f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
            "human": f"https://careers.smartrecruiters.com/{slug}"} if n else None


def v_workable(slug):
    r = get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("jobs", []))
    except Exception:
        return None
    return {"ats": "workable", "slug": slug, "count": n,
            "api": f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
            "human": f"https://apply.workable.com/{slug}/"} if n else None


def v_recruitee(slug):
    r = get(f"https://{slug}.recruitee.com/api/offers/")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("offers", []))
    except Exception:
        return None
    return {"ats": "recruitee", "slug": slug, "count": n,
            "api": f"https://{slug}.recruitee.com/api/offers/",
            "human": f"https://{slug}.recruitee.com/"} if n else None


def v_eightfold(slug, domain=None):
    dom = domain or f"{slug}.com"
    url = (f"https://{slug}.eightfold.ai/api/apply/v2/jobs"
           f"?domain={dom}&start=0&num=10&exclude_pid=&sort_by=relevance")
    r = get(url)
    if r is None or r.status_code != 200:
        return None
    try:
        n = r.json().get("count", 0)
    except Exception:
        return None
    return {"ats": "eightfold", "slug": slug, "count": n, "api": url,
            "human": f"https://{slug}.eightfold.ai/careers"} if n else None


def v_workday(tenant, host, site, base="myworkdayjobs"):
    """host is like 'wd5'. Confirms via the public CXS jobs endpoint."""
    url = f"https://{tenant}.{host}.{base}.com/wday/cxs/{tenant}/{site}/jobs"
    r = post_json(url, {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""})
    if r is None or r.status_code != 200:
        return None
    try:
        j = r.json()
    except Exception:
        return None
    n = j.get("total")
    if not isinstance(n, int) or n <= 0:
        return None
    return {"ats": "workday", "tenant": tenant, "host": host, "site": site,
            "count": n, "api": url,
            "human": f"https://{tenant}.{host}.{base}.com/en-US/{site}",
            "resolve_url": f"https://{tenant}.{host}.{base}.com/en-US/{site}"}


VERIFIERS = {
    "greenhouse": v_greenhouse,
    "lever": v_lever,
    "ashby": v_ashby,
    "smartrecruiters": v_smartrecruiters,
    "workable": v_workable,
    "recruitee": v_recruitee,
}

SCRAPE_ONLY = {"icims", "taleo", "oracle", "phenom", "jobvite", "bamboohr",
               "paylocity", "teamtailor", "rippling"}

# Companies that run their own recruiting stack. These will never match an ATS
# fingerprint, so we point change-detection straight at the right search page.
# (URLs verified as of Aug 2026 — the script re-checks each one returns 200.)
CUSTOM_CAREERS = {
    "Amazon": "https://www.amazon.jobs/en/search?base_query=design+intern",
    "Apple": "https://jobs.apple.com/en-us/search?team=Design-DES",
    "Google": "https://www.google.com/about/careers/applications/jobs/results/?employment_type=INTERN",
    "Meta": "https://www.metacareers.com/jobs?roles[0]=Internship",
    "Microsoft": "https://jobs.careers.microsoft.com/global/en/search?lc=United%20States",
    "IBM": "https://www.ibm.com/careers/search",
    "Uber": "https://www.uber.com/us/en/careers/list/?department=Design",
    "Netflix": "https://explore.jobs.netflix.net/careers",
    "Goldman Sachs": "https://higher.gs.com/roles",
    "Morgan Stanley": "https://www.morganstanley.com/careers/career-opportunities-search",
    "JPMorgan Chase": "https://careers.jpmorgan.com/us/en/students/programs",
    "Bank of America": "https://careers.bankofamerica.com/en-us/job-search",
    "Citi": "https://jobs.citi.com/search-jobs",
    "Bloomberg": "https://careers.bloomberg.com/job/search",
    "Oracle": "https://careers.oracle.com/jobs/#en/sites/jobsearch",
    "The Walt Disney Company": "https://jobs.disneycareers.com/search-jobs",
    "Jane Street": "https://www.janestreet.com/join-jane-street/open-roles/",
    "Deloitte": "https://apply.deloitte.com/careers",
    "EY": "https://careers.ey.com/ey/search/",
    "PwC": "https://jobs.us.pwc.com/search-jobs",
    "KPMG": "https://www.kpmguscareers.com/search-jobs",
    "McKinsey": "https://www.mckinsey.com/careers/search-jobs",
    "Bain": "https://www.bain.com/careers/find-a-role/",
    "Accenture": "https://www.accenture.com/us-en/careers/jobsearch",
    "Verizon": "https://mycareer.verizon.com/jobs/",
    "AT&T": "https://www.att.jobs/search-jobs",
    "T-Mobile": "https://careers.t-mobile.com/search-jobs",
    "Shopify": "https://www.shopify.com/careers/search",
    "Pentagram": "https://www.pentagram.com/careers",
}


# --------------------------------------------------------------------------
# Slug guessing
# --------------------------------------------------------------------------

def name_variants(name, domain):
    base = re.sub(r"[^a-z0-9\s\-]", "", name.lower())
    base = base.replace("&", "and")
    words = base.split()
    stop = {"inc", "llc", "co", "corp", "corporation", "company", "the",
            "group", "holdings", "usa", "pbc", "associates"}
    core = [w for w in words if w not in stop]
    joined = "".join(core)
    hyph = "-".join(core)
    dom = domain.split(".")[0]
    out = [joined, hyph, dom, core[0] if core else joined,
           joined + "careers", "".join(words), "-".join(words)]
    seen, res = set(), []
    for v in out:
        v = v.strip("-")
        if v and v not in seen and len(v) > 1:
            seen.add(v)
            res.append(v)
    return res


WD_HOSTS = ["wd1", "wd5", "wd3", "wd2", "wd12", "wd101", "wd103", "wd10",
            "wd102", "wd104", "wd105", "wd502", "wd505"]

WD_SITES = ["External", "External_Career_Site", "ExternalCareerSite", "Careers",
            "careers", "External_Careers", "external", "External_Site",
            "ExternalSite", "Global_Careers", "GlobalCareers", "CorporateCareers",
            "Search", "jobs", "Jobs", "PublicJobs", "External_Experienced",
            "external_experienced", "Professional_Careers", "USA_Careers"]


def workday_brute(name, domain, deep=False, workers=24):
    tenants = name_variants(name, domain)[:4]
    hosts = WD_HOSTS if deep else WD_HOSTS[:6]
    sites = WD_SITES if deep else WD_SITES[:8]
    combos = [(t, h, s) for t in tenants for h in hosts for s in sites]
    found = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(v_workday, t, h, s): (t, h, s) for t, h, s in combos}
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception:
                r = None
            if r:
                found.append(r)
                for other in futs:
                    other.cancel()
                break
    return found[0] if found else None


def guess_standard(name, domain, workers=12):
    """Probe greenhouse/lever/ashby/smartrecruiters/workable with name variants."""
    variants = name_variants(name, domain)
    jobs = []
    for ats in ("greenhouse", "lever", "ashby", "smartrecruiters", "workable"):
        for v in variants:
            jobs.append((ats, v))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(VERIFIERS[a], v): (a, v) for a, v in jobs}
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception:
                r = None
            if r:
                return r
    return None


# --------------------------------------------------------------------------
# Per-company pipeline
# --------------------------------------------------------------------------

def resolve_company(row, deep=False):
    name, domain, cat, pri, hint = row
    rec = {"name": name, "domain": domain, "category": cat, "priority": pri,
           "hint": hint, "status": "unresolved", "careers_seen": []}

    if hint == "defunct":
        rec["status"] = "skip"
        rec["note"] = "company likely defunct/acquired — verify before spending time"
        return rec
    if hint == "manual":
        rec["status"] = "manual"
        rec["note"] = "no ATS; apply direct"
        rec["human"] = CUSTOM_CAREERS.get(name, f"https://{domain}")
        return rec

    # Known in-house recruiting stacks: skip ATS discovery, hand back the
    # search page for change-detection (after confirming it still loads).
    if hint == "custom" and name in CUSTOM_CAREERS:
        url = CUSTOM_CAREERS[name]
        r = get(url)
        rec["status"] = "scrape"
        rec["ats"] = "custom"
        rec["human"] = url
        rec["note"] = ("in-house ATS, no public JSON board — point change-detection here"
                       + ("" if (r is not None and r.status_code < 400) else " (URL did not load, re-check)"))
        return rec

    if hint == "eightfold":
        r = v_eightfold(domain.split(".")[0], domain)
        if r:
            rec.update(r)
            rec["status"] = "resolved"
            rec["method"] = "hint"
            return rec

    # 1. sniff
    blobs = collect_html(domain)
    rec["careers_seen"] = [u for u, _ in blobs][:6]
    all_hits = []
    for _, html in blobs:
        all_hits += sniff(html)

    # prefer the hinted ATS if we have one
    def rank(h):
        return 0 if (hint and h[0] == hint) else 1
    all_hits.sort(key=rank)

    for ats, groups in all_hits:
        if ats == "workday":
            tenant, host, base, site = groups[0], groups[1], groups[2], groups[3]
            if site.lower() in JUNK or site.lower().startswith("wday"):
                continue
            r = v_workday(tenant.lower(), host.lower(), site, base.lower())
            if r:
                rec.update(r)
                rec["status"] = "resolved"
                rec["method"] = "sniff"
                return rec
        elif ats in VERIFIERS:
            r = VERIFIERS[ats](groups[0].lower())
            if r:
                rec.update(r)
                rec["status"] = "resolved"
                rec["method"] = "sniff"
                return rec
        elif ats == "eightfold":
            r = v_eightfold(groups[0].lower(), domain)
            if r:
                rec.update(r)
                rec["status"] = "resolved"
                rec["method"] = "sniff"
                return rec
        elif ats in SCRAPE_ONLY:
            # remember it, but keep looking for something with a real API
            rec.setdefault("scrape_candidate", {"ats": ats, "url": groups[0]})

    # 2. guess standard ATS slugs
    r = guess_standard(name, domain)
    if r:
        rec.update(r)
        rec["status"] = "resolved"
        rec["method"] = "guess"
        return rec

    # 3. workday brute force
    if hint == "workday" or deep:
        r = workday_brute(name, domain, deep=deep)
        if r:
            rec.update(r)
            rec["status"] = "resolved"
            rec["method"] = "brute"
            return rec

    # 4. fall back to scrape target
    if "scrape_candidate" in rec:
        rec["status"] = "scrape"
        rec["ats"] = rec["scrape_candidate"]["ats"]
        rec["human"] = rec["scrape_candidate"]["url"]
        rec["note"] = "no public JSON API — use change-detection on this URL"
        return rec

    rec["note"] = "check careers page by hand"
    return rec


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def write_reports(records, outdir):
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "resolved.json"), "w") as f:
        json.dump({r["name"]: r for r in records}, f, indent=2)

    res = [r for r in records if r["status"] == "resolved"]
    scr = [r for r in records if r["status"] == "scrape"]
    unr = [r for r in records if r["status"] in ("unresolved", "manual", "skip")]

    res.sort(key=lambda r: (r["priority"], r["name"]))
    lines = ["# Resolved", "",
             f"{len(res)} companies verified against a live jobs API.", "",
             "| Company | Pri | ATS | Endpoint | Open roles | How |",
             "|---|---|---|---|---|---|"]
    for r in res:
        ident = r.get("slug") or f"{r.get('tenant')}/{r.get('host')}/{r.get('site')}"
        lines.append(
            f"| {r['name']} | {r['priority']} | {r['ats']} | `{ident}` | "
            f"{r.get('count','?')} | {r.get('method','')} |")
    lines += ["", "## Full endpoints", ""]
    for r in res:
        lines.append(f"- **{r['name']}** — {r.get('human','')}")
    with open(os.path.join(outdir, "resolved.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    lines = ["# Needs a human", ""]
    if scr:
        lines += ["## Scrape / change-detection only (no public API)", "",
                  "| Company | Pri | Platform | URL |", "|---|---|---|---|"]
        for r in sorted(scr, key=lambda r: (r["priority"], r["name"])):
            lines.append(f"| {r['name']} | {r['priority']} | {r.get('ats','?')} | {r.get('human','')} |")
        lines.append("")
    if unr:
        lines += ["## Unresolved", "",
                  "| Company | Pri | Domain | Pages checked | Note |", "|---|---|---|---|---|"]
        for r in sorted(unr, key=lambda r: (r["priority"], r["name"])):
            seen = " ".join(r.get("careers_seen", [])[:2]) or "-"
            lines.append(f"| {r['name']} | {r['priority']} | {r['domain']} | {seen} | {r.get('note','')} |")
    with open(os.path.join(outdir, "unresolved.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    cmds = ["#!/usr/bin/env bash", "set -e", ""]
    for r in res:
        if r["ats"] == "workday":
            cmds.append(f'python resolve.py --workday "{r["name"]}" "{r["resolve_url"]}"')
    cmds += ["", "python resolve.py --write-config", "python internship_watch.py --dry-run"]
    with open(os.path.join(outdir, "commands.sh"), "w") as f:
        f.write("\n".join(cmds) + "\n")

    log(f"\n  resolved: {len(res)}   scrape-only: {len(scr)}   still open: {len(unr)}")
    log(f"  wrote {outdir}/resolved.json, resolved.md, unresolved.md, commands.sh")


# --------------------------------------------------------------------------

def load_seeds(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            while len(parts) < 5:
                parts.append("")
            rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip(),
                         int(parts[3] or 3), parts[4].strip()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="seeds.tsv")
    ap.add_argument("--out", default="out")
    ap.add_argument("--workers", type=int, default=6,
                    help="companies in parallel (keep low; each spawns its own probes)")
    ap.add_argument("--deep", action="store_true", help="wider Workday brute force")
    ap.add_argument("--priority", type=int, default=0, help="only this priority tier")
    ap.add_argument("--only", default="", help="comma-separated company names")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    rows = load_seeds(args.seeds)
    if args.priority:
        rows = [r for r in rows if r[3] == args.priority]
    if args.only:
        want = {s.strip().lower() for s in args.only.split(",")}
        rows = [r for r in rows if r[0].lower() in want]

    done = {}
    path = os.path.join(args.out, "resolved.json")
    if args.resume and os.path.exists(path):
        done = json.load(open(path))
        before = len(rows)
        rows = [r for r in rows if done.get(r[0], {}).get("status") != "resolved"]
        log(f"resume: skipping {before - len(rows)} already resolved")

    log(f"resolving {len(rows)} companies with {args.workers} workers"
        f"{' (deep)' if args.deep else ''}\n")

    records = list(done.values()) if args.resume else []
    names_done = {r["name"] for r in records}
    records = [r for r in records if r["name"] not in {x[0] for x in rows}]

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(resolve_company, r, args.deep): r[0] for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            name = futs[f]
            try:
                rec = f.result()
            except Exception as e:
                rec = {"name": name, "status": "unresolved", "priority": 3,
                       "domain": "", "category": "", "note": f"error: {e}"}
            records.append(rec)
            mark = {"resolved": "OK  ", "scrape": "SCR ", "manual": "MAN ",
                    "skip": "SKIP"}.get(rec["status"], "--  ")
            detail = rec.get("human", rec.get("note", ""))
            log(f"[{i:3}/{len(rows)}] {mark} {name:<32} {detail[:70]}")
            if i % 25 == 0:
                write_reports(records, args.out)

    write_reports(records, args.out)
    log(f"\ndone in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
```
