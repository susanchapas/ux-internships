"""End-to-end test of resolve.py with a fake ATS network."""

import json
import pathlib
import sys
import types

import resolve as r

# ---- fake universe: which (board, slug) pairs "exist"
UNIVERSE = {
    ("greenhouse", "betterment"): ["UX Research Intern", "PM Intern", "Analyst"],
    ("greenhouse", "esusu"): ["Product Design Intern"],
    ("lever", "propel"): ["User Research Intern", "Engineer"],
    ("ashby", "ramp"): ["Design Intern", "Brand Intern"],
    ("smartrecruiters", "Bosch"): ["UX Intern"],
    ("workable", "bighuman"): ["Design Intern"],
    ("bamboohr", "barrel"): ["Marketing Intern"],
}

calls = {"n": 0}


class FakeResp:
    def __init__(self, status, payload):
        self.status_code = status
        self._p = payload

    def json(self):
        if self._p is None:
            raise ValueError("no json")
        return self._p


def fake_get(url, **kw):
    calls["n"] += 1
    import re as _re
    def hit(board, slug):
        return UNIVERSE.get((board, slug))

    m = _re.search(r"boards-api\.greenhouse\.io/v1/boards/([^/]+)/jobs", url)
    if m:
        t = hit("greenhouse", m.group(1))
        return FakeResp(200, {"jobs": [{"title": x} for x in t]}) if t else FakeResp(404, None)
    m = _re.search(r"api\.lever\.co/v0/postings/([^?]+)", url)
    if m:
        t = hit("lever", m.group(1))
        return FakeResp(200, [{"text": x} for x in t]) if t else FakeResp(404, None)
    m = _re.search(r"posting-api/job-board/([^?/]+)", url)
    if m:
        t = hit("ashby", m.group(1))
        return FakeResp(200, {"jobs": [{"title": x} for x in t]}) if t else FakeResp(404, None)
    m = _re.search(r"smartrecruiters\.com/v1/companies/([^/]+)/postings", url)
    if m:
        t = hit("smartrecruiters", m.group(1))
        return FakeResp(200, {"content": [{"name": x} for x in t],
                              "totalFound": len(t)}) if t else FakeResp(404, None)
    m = _re.search(r"workable\.com/api/v1/widget/accounts/([^?]+)", url)
    if m:
        t = hit("workable", m.group(1))
        return FakeResp(200, {"jobs": [{"title": x} for x in t]}) if t else FakeResp(404, None)
    m = _re.search(r"https://([^.]+)\.bamboohr\.com", url)
    if m:
        t = hit("bamboohr", m.group(1))
        return FakeResp(200, {"result": [{"jobOpeningName": x} for x in t]}) if t else FakeResp(404, None)
    m = _re.search(r"https://([^.]+)\.recruitee\.com", url)
    if m:
        t = hit("recruitee", m.group(1))
        return FakeResp(200, {"offers": [{"title": x} for x in t]}) if t else FakeResp(404, None)
    return FakeResp(404, None)


r.requests = types.SimpleNamespace(get=fake_get, RequestException=Exception)
r.DELAY = 0

fails = []


def check(label, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {label}{(' — ' + detail) if detail and not cond else ''}")
    if not cond:
        fails.append(label)


print("\n[1] resolves each board type")
for name, hint, want_board, want_slug in [
    ("Betterment", "betterment", "greenhouse", "betterment"),
    ("Esusu", "esusu", "greenhouse", "esusu"),
    ("Propel", "propel", "lever", "propel"),
    ("Ramp", "ramp", "ashby", "ramp"),
    ("Big Human", "bighuman", "workable", "bighuman"),
    ("Barrel", "barrel", "bamboohr", "barrel"),
]:
    rec = r.resolve_one(name, hint, verbose=False)
    ok = rec and rec["board"] == want_board and rec["slug"] == want_slug
    check(f"{name} -> {want_board}/{want_slug}", ok,
          f"got {rec}")

print("\n[2] resolves without a hint (candidate generation must find it)")
rec = r.resolve_one("Big Human", None, verbose=False)
check("Big Human found via generated candidate", rec and rec["slug"] == "bighuman", str(rec))

print("\n[3] unknown company returns None, doesn't crash")
before = calls["n"]
rec = r.resolve_one("Totally Fake Company XYZ", None, verbose=False)
check("returns None", rec is None)
check("bounded probe count", calls["n"] - before <= r.MAX_CANDIDATES * len(r.PROBES),
      f"{calls['n']-before} probes")
print(f"       (worst case cost: {calls['n']-before} requests for a miss)")

print("\n[4] captures job count and samples")
rec = r.resolve_one("Betterment", "betterment", verbose=False)
check("open_jobs recorded", rec["open_jobs"] == 3, str(rec.get("open_jobs")))
check("samples recorded", "UX Research Intern" in rec["samples"], str(rec.get("samples")))
check("marked verified", rec["confidence"] == "verified")

print("\n[5] Workday URL parsing -> config shape")
wd = r.parse_workday_url("https://prudential.wd5.myworkdayjobs.com/en-US/Prudential_Careers/job/Newark")
check("tenant", wd["tenant"] == "prudential", str(wd))
check("wd cluster", wd["wd"] == 5)
check("site", wd["site"] == "Prudential_Careers", wd["site"])
check("no-locale form works",
      r.parse_workday_url("https://pge.wd1.myworkdayjobs.com/External_Careers")["site"] == "External_Careers")
check("rejects non-workday", r.parse_workday_url("https://acme.com/jobs") is None)

print("\n[6] write_config emits correct shapes")
tmp = pathlib.Path("_t_config.json")
r.OUT_CONFIG = tmp
cache = {
    "Betterment": {"board": "greenhouse", "slug": "betterment"},
    "Prudential": {"board": "workday", "tenant": "prudential", "wd": 5,
                   "site": "Prudential_Careers", "search": "intern"},
    "Nowhere Inc": {"board": None},
}
r.write_config(cache)
cfg = json.loads(tmp.read_text())
entries = {c["name"]: c for c in cfg["companies"]}
check("greenhouse entry has slug", entries["Betterment"]["slug"] == "betterment")
check("workday entry has tenant/site",
      entries["Prudential"]["tenant"] == "prudential" and entries["Prudential"]["site"] == "Prudential_Careers")
check("unresolved company excluded", "Nowhere Inc" not in entries)
check("usajobs appended", any(c["board"] == "usajobs" for c in cfg["companies"]))
tmp.unlink()

print("\n[7] targets.json integrity")
t = json.loads(pathlib.Path("targets.json").read_text())
names = [c["name"] for v in t["categories"].values() for c in v["companies"]]
check("no duplicate company names", len(names) == len(set(names)),
      f"dupes: {[n for n in set(names) if names.count(n) > 1]}")
check("every company has a name", all(c.get("name") for v in t["categories"].values() for c in v["companies"]))
check("every category has a label+priority",
      all(v.get("label") and v.get("priority") for v in t["categories"].values()))
print(f"       {len(names)} companies total")

print("\n" + "=" * 60)
print("ALL PASSED" if not fails else f"{len(fails)} FAILURE(S): {fails}")
sys.exit(1 if fails else 0)
