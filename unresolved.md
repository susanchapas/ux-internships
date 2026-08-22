# Company Resolution Status

**195** of 241 resolved. **46** remain. `config.json` rebuilt with all 195.

---

## Still Unresolved (48)

### Custom / proprietary platforms (12)

| Company | Careers URL | Category |
|---|---|---|
| Amazon | `amazon.jobs` | big_tech |
| Apple | `jobs.apple.com` | big_tech |
| Deque Systems | `deque.com/company/careers/` | accessibility |
| Goldman Sachs | `higher.gs.com` | banks_insurance |
| Google | `careers.google.com` | big_tech |
| IBM | `careers.ibm.com` | big_tech |
| Intuit | `jobs.intuit.com` (TalentBrew/Radancy) | big_tech |
| Meta | `metacareers.com` | big_tech |
| Microsoft | `careers.microsoft.com` | big_tech |
| Rippling | `rippling.com/careers` (own HR platform) | fintech_core |
| Uber | `uber.com/careers` | big_tech |
| Vimeo | `vimeo.com/careers` (old Greenhouse board expired) | big_tech |

### Oracle HCM (5)

| Company | Careers URL | Category |
|---|---|---|
| American Express | `egug.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1` | banks_insurance |
| Chubb | `fa-ewgu-saasfaprod1.fa.ocs.oraclecloud.com` | banks_insurance |
| JPMorgan Chase | `jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001` | banks_insurance |
| Oracle | `eeho.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/jobsearch` | big_tech |
| Warby Parker | `jobs.warbyparker.com` (Oracle HCM backend) | big_tech |

### Other unsupported ATS (8)

| Company | ATS | Careers URL | Category |
|---|---|---|---|
| Accion | iCIMS | `jobs-accion.icims.com` | fintech_mission |
| Ally | Avature | `ally.avature.net/careers` | banks_insurance |
| Coforma | Pinpoint | `coforma.pinpointhq.com` | civic_tech |
| DocuSign | iCIMS | `uscareers-docusign.icims.com` | best_places_to_work |
| Grameen America | TriNet Hire | `app.trinethire.com/companies/924509-grameen-america-inc` | fintech_mission |
| Helen Keller Services | ADP Workforce Now | — | accessibility |
| Moody's | SAP SuccessFactors | `career8.successfactors.com/career?career_company=MoodysProd` | banks_insurance |
| U.S. Digital Response | Breezy HR | `us-digital-response.breezy.hr` | civic_tech |
| Vispero | UKG Pro | — | accessibility |

### Expired Greenhouse / Lever boards (6)

These had valid boards that now return 404. They likely migrated ATS — run `discover.py` on the current careers page.

| Company | Old board | Current careers URL | Category |
|---|---|---|---|
| Designit | greenhouse / `designitnorthamerica` | — | ux_agencies |
| Fearless | greenhouse / `fearless` | `jobs.fearless.com` | civic_tech |
| Flywire | greenhouse / `flywire2` | — | fintech_core |
| Rangle | lever / `rangle` | — | ux_agencies |
| Truss | lever / `trussworks` | — | civic_tech |
| ustwo | greenhouse / `ustwo` | — | ux_agencies |

### Email-only / no ATS (10)

| Company | Contact | Category |
|---|---|---|
| Aira | `aira.io/careers` | accessibility |
| American Foundation for the Blind | `afb.org/about-afb/leadership/careers-afb` | accessibility |
| Athletics | `jobs@athleticsnyc.com` | ux_agencies |
| Barrel | `jobs@barrelny.com` | ux_agencies |
| Be My Eyes | `bemyeyes.com/business/join-our-team` | accessibility |
| Big Human | `jobs@bighuman.com` | ux_agencies |
| Collins | `wearecollins.com/careers` (was 404) | ux_agencies |
| Greenwood | `job@gogreenwood.com` | fintech_mission |
| Pentagram | `pentagram.com/careers` (apply direct) | ux_agencies |
| TPGi | `Careers@TPGi.com` | accessibility |
| Work and Co | `careers@work.co` (now Accenture Song) | ux_agencies |

### No ATS found / not hiring (4)

| Company | Note | Category |
|---|---|---|
| Civilla | Not currently hiring | civic_tech |
| Petal | No standard ATS found; check Wellfound | fintech_mission |
| Siegel+Gale | Part of Omnicom; no public ATS | ux_agencies |

---

## Resolved This Session (30)

### Workday (15)

| Company | Workday URL | Postings |
|---|---|---|
| Bank of America | `ghr.wd1.myworkdayjobs.com/Lateral-US` | 1,004 |
| BlackRock | `blackrock.wd1.myworkdayjobs.com/BlackRock_Professional` | 187 |
| Citi | `citi.wd5.myworkdayjobs.com/2` | 2,000 |
| Droga5 | `accenture.wd103.myworkdayjobs.com/AccentureCareers` (search "Droga5") | 2,000 |
| Etsy | `etsy.wd5.myworkdayjobs.com/Etsy_Careers` | 13 |
| Federal Reserve Bank of NY | `rb.wd5.myworkdayjobs.com/FRS` | 76 |
| MoneyLion | `gen.wd1.myworkdayjobs.com/careers` (via Gen Digital) | 0 |
| Morgan Stanley | `ms.wd5.myworkdayjobs.com/External` | 698 |
| Netflix | `netflix.wd108.myworkdayjobs.com/Netflix` | 380 |
| Prudential Financial | `pru.wd5.myworkdayjobs.com/Careers` | 89 |
| Remitly | `remitly.wd5.myworkdayjobs.com/Remitly_Careers` | 76 |
| S&P Global | `spgi.wd5.myworkdayjobs.com/SPGI_Careers` | 296 |
| Snap | `snapchat.wd1.myworkdayjobs.com/snap` | 96 |
| Synchrony | `synchronyfinancial.wd5.myworkdayjobs.com/careers` | 44 |
| Vanguard | `vanguard.wd5.myworkdayjobs.com/vanguard_external` | 240 |

### Standard ATS (15)

| Company | Board / Slug | Jobs |
|---|---|---|
| Ad Hoc | workable / `adhocteam` | 0 |
| Addepar | greenhouse / `addepar1` | 123 |
| Deel | ashby / `deel` | 0 |
| ~~Esusu~~ | ~~greenhouse / `esusu`~~ | removed — board 404, no replacement ATS found |
| Kiva | greenhouse / `kivaorg` | 2 |
| Local Projects | workable / `local-projects-llc-1` | 0 |
| Marqeta | greenhouse / `marqeta` | 2 |
| MoCaFi | greenhouse / `mocafi` | 0 |
| Nava PBC | greenhouse / `navapbc` | 16 |
| Navan | greenhouse / `tripactions` | 207 |
| Publicis Sapient | smartrecruiters / `PublicisSapient12` | 0 |
| Skylight | greenhouse / `skylighthq` | 4 |
| Stash | greenhouse / `stashinvest` | 13 |
| Thoughtbot | workable / `thoughtbot` | 0 |
| Varo | lever / `varomoney` | 0 |

---

## Previously Resolved (165)

All Priority 2 Workday (45), Priority 2 Other ATS (96 of 97, all except DocuSign), and Priority 3 (24) were resolved in prior runs. See `resolved.json` for full details.

## Government Portals — manual check (17)

No ATS — check each URL periodically.

| Organization | Note | URL |
|---|---|---|
| NYC Office of Technology & Innovation (OTI) | Best NYC civic UX entry point | https://www.nyc.gov/content/oti/pages/ |
| NYC Economic Development Corporation | | https://edc.nyc/careers |
| MTA | Formal internship program | https://new.mta.info/careers |
| Port Authority of NY & NJ | Formal summer internship | https://www.panynj.gov/corporate/en/careers.html |
| NJ Office of Innovation | Actively hires designers/researchers | https://innovation.nj.gov/ |
| NJ Civil Service Commission | | https://www.nj.gov/csc/ |
| NJ Transit | | https://www.njtransit.com/careers |
| NJ Economic Development Authority | | https://www.njeda.gov/careers/ |
| New York State ITS | | https://statejobs.ny.gov/ |
| Federal Reserve Bank of New York | CDFI background is relevant | https://www.newyorkfed.org/careers |
| FDIC | CDFI-adjacent policy work | https://www.fdic.gov/about/careers/ |
| OCC | | https://www.occ.gov/careers/ |
| SEC | | https://www.sec.gov/careers |
| FINRA | | https://www.finra.org/careers |
| United Nations | Internships typically unpaid | https://careers.un.org/ |
| UNICEF | | https://www.unicef.org/careers/ |
| World Bank | | https://www.worldbank.org/en/about/careers |

> **Note:** 18F and the U.S. Digital Service were significantly restructured during 2025 — verify current status. The civic_tech contractors hire more predictably.
