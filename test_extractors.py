"""Fixture tests for extractors.py — verifies parsing against realistic page shapes."""

import json
import extractors as ex

# --- fixture 1: JSON-LD wrapped in @graph, jobLocation as a list (common shape)
JSONLD_GRAPH = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":"Organization","name":"Acme Corp"},
 {"@type":"JobPosting","title":"UX Research Intern, Summer 2027",
  "identifier":{"@type":"PropertyValue","value":"REQ-40188"},
  "datePosted":"2026-08-14","url":"https://acme.com/careers/40188",
  "jobLocation":[{"@type":"Place","address":{"@type":"PostalAddress",
    "addressLocality":"New York","addressRegion":"NY","addressCountry":"US"}}]}
]}
</script></head><body>whatever</body></html>
"""

# --- fixture 2: array of postings, one remote (TELECOMMUTE, no address)
JSONLD_ARRAY = """
<script type="application/ld+json">
[{"@type":"JobPosting","title":"Product Management Intern","url":"https://x.com/j/1",
  "jobLocationType":"TELECOMMUTE","jobLocation":{"address":{}}},
 {"@type":"JobPosting","title":"Design Co-Op","url":"https://x.com/j/2",
  "jobLocation":{"@type":"Place","address":{"addressLocality":"Jersey City","addressRegion":"NJ"}}}]
</script>
"""

# --- fixture 3: ld+json present but only breadcrumbs, no JobPosting
JSONLD_NOJOBS = """
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[]}
</script>
"""

# --- fixture 4: Next.js hydration payload with jobs nested a few levels down
NEXT_DATA = {
    "props": {"pageProps": {"initialData": {"openings": [
        {"id": 991, "name": "UX Design Intern", "office": "New York, NY"},
        {"id": 992, "name": "Content Strategy Intern", "office": "Newark, NJ"},
        {"id": 993, "name": "Backend Intern", "office": "Austin, TX"},
    ]}}},
    "buildId": "abc123",
}
NEXT_HTML = (
    '<html><body><div id="__next"></div>'
    '<script id="__NEXT_DATA__" type="application/json">'
    + json.dumps(NEXT_DATA)
    + "</script></body></html>"
)

# --- fixture 5: plain server-rendered listing for CSS selectors
CSS_HTML = """
<html><body>
<div class="openings">
  <div class="job-listing">
     <a href="/careers/ux-research-intern"><h3 class="job-title">UX Research Intern</h3></a>
     <span class="job-location">New York, NY</span>
  </div>
  <div class="job-listing">
     <a href="/careers/pm-intern"><h3 class="job-title">Product Management Intern</h3></a>
     <span class="job-location">Hoboken, NJ</span>
  </div>
  <div class="job-listing">
     <a href="/careers/swe"><h3 class="job-title">Software Engineer</h3></a>
     <span class="job-location">Remote</span>
  </div>
</div></body></html>
"""

fails = []


def check(label, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {label}{(' — ' + detail) if detail and not cond else ''}")
    if not cond:
        fails.append(label)


print("\n[1] JSON-LD @graph + list jobLocation")
jobs = ex.parse_jsonld(JSONLD_GRAPH, "https://acme.com/careers", "Acme")
check("finds 1 posting (ignores Organization)", len(jobs) == 1, f"got {len(jobs)}")
if jobs:
    j = jobs[0]
    check("title", j["title"] == "UX Research Intern, Summer 2027", j["title"])
    check("location from nested list", j["location"] == "New York, NY", j["location"])
    check("url", j["url"] == "https://acme.com/careers/40188", j["url"])
    check("id derived from identifier.value", j["id"].startswith("ld:Acme:"), j["id"])
    check("datePosted captured", j["posted"] == "2026-08-14", j["posted"])

print("\n[2] JSON-LD array + TELECOMMUTE")
jobs = ex.parse_jsonld(JSONLD_ARRAY, "https://x.com", "X")
check("finds 2 postings", len(jobs) == 2, f"got {len(jobs)}")
if len(jobs) == 2:
    check("remote -> 'Remote'", jobs[0]["location"] == "Remote", jobs[0]["location"])
    check("NJ location parsed", jobs[1]["location"] == "Jersey City, NJ", jobs[1]["location"])

print("\n[3] ld+json with no JobPosting")
check("returns empty, no crash", ex.parse_jsonld(JSONLD_NOJOBS, "u", "C") == [])

print("\n[4] malformed JSON in ld+json block")
check("skips bad block", ex.parse_jsonld(
    '<script type="application/ld+json">{not json,,,}</script>', "u", "C") == [])

print("\n[5] hydration payload discovery")
import re
m = re.search(ex.HYDRATION["next"], NEXT_HTML, re.S)
check("regex extracts __NEXT_DATA__", m is not None)
payload = json.loads(m.group(1))
arrays = ex.find_arrays(payload)
check("find_arrays locates the openings list", any("openings" in p for p, _, _ in arrays),
      str([p for p, _, _ in arrays]))
path = [p for p, n, k in arrays if "openings" in p][0]
print(f"       discovered path: {path}")
rows = ex.dig(payload, path)
check("dig() retrieves 3 rows", len(rows) == 3, f"got {len(rows)}")
check("row keys as expected", sorted(rows[0].keys()) == ["id", "name", "office"])

print("\n[6] ID stability (same input -> same hash)")
a = ex.parse_jsonld(JSONLD_GRAPH, "https://acme.com/careers", "Acme")[0]["id"]
b = ex.parse_jsonld(JSONLD_GRAPH, "https://acme.com/careers", "Acme")[0]["id"]
check("deterministic across runs", a == b, f"{a} vs {b}")

print("\n[7] CSS selector extraction")
# stub the network so we can test the parser against the fixture
ex._get = lambda url, **kw: type("R", (), {"text": CSS_HTML, "json": lambda self: {}})()
cfg = {"row": "div.job-listing", "title": "h3.job-title",
       "location": "span.job-location", "link": "a"}
jobs = ex.css_jobs("https://acme.com/careers", cfg, "Acme")
check("extracts all 3 rows", len(jobs) == 3, f"got {len(jobs)}")
if len(jobs) == 3:
    check("title parsed", jobs[0]["title"] == "UX Research Intern", jobs[0]["title"])
    check("location parsed", jobs[1]["location"] == "Hoboken, NJ", jobs[1]["location"])
    check("relative href made absolute",
          jobs[0]["url"] == "https://acme.com/careers/ux-research-intern", jobs[0]["url"])
    check("ids unique", len({j["id"] for j in jobs}) == 3)

print("\n[8] fingerprint change detection")


def fp(html, **kw):
    import hashlib
    text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    for pat in kw.get("strip_patterns", []):
        text = re.sub(pat, "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(text.encode()).hexdigest()


base = "<div>UX Intern</div><span>Generated at 2026-08-18T09:00:00Z</span>"
same_later = "<div>UX Intern</div><span>Generated at 2026-08-18T15:22:41Z</span>"
real_change = "<div>UX Intern</div><div>PM Intern</div><span>Generated at 2026-08-18T09:00:00Z</span>"
ts = [r"\d{4}-\d{2}-\d{2}T[\d:]+Z"]
check("volatile timestamp stripped -> no false alarm",
      fp(base, strip_patterns=ts) == fp(same_later, strip_patterns=ts))
check("without stripping, timestamp causes false alarm", fp(base) != fp(same_later))
check("real new posting detected", fp(base, strip_patterns=ts) != fp(real_change, strip_patterns=ts))

print("\n" + "=" * 60)
print("ALL PASSED" if not fails else f"{len(fails)} FAILURE(S): {fails}")
