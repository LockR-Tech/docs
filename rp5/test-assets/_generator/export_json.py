"""Export Report 5 data (system test cases + unit test matrix with real surefire results) to JSON for the Excel builders."""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from st_cases_1 import MODULES_1  # noqa: E402
from st_cases_2 import MODULES_2  # noqa: E402
from ut_data import FUNCS  # noqa: E402

UT_RESULTS, UT_AUTHORS, BE_ROOT, OUT = sys.argv[1:5]

PROJECT = dict(name="Lock.R - Smart Locker System with Drone Delivery", code="LockR", creator="binhtntse182370",
               reviewer="huynqbse180211", issue=dt.date(2026, 11, 9), version="1.0")


def oadate(d):
    return (d - dt.date(1899, 12, 30)).days


# ------------------------------------------------------------------ system tests
WINDOWS = {1: dt.date(2026, 9, 28), 2: dt.date(2026, 10, 12), 3: dt.date(2026, 10, 26), 4: dt.date(2026, 11, 3)}
NOTES = {
    "Pickup PIN is unique among active orders": "Defect F2-G10: no unique index on the PIN of active orders (Pending).",
    "Door state is reported after pickup": "Defect: most door sensors of CAB-TU01 are not read by the Pi (Pending).",
    "Door sensor of every box": "Defect: most door sensors of CAB-TU01 are not read by the Pi (Pending).",
    "Controller without heartbeat becomes OFFLINE": "IoT health monitoring: device OFFLINE state and admin alert not implemented yet.",
    "Change the role of an existing user": "Role change UI not built yet on the admin web.",
    "Live position of a STANDARD order from real telemetry": "Real drone flight not tested end-to-end yet.",
    "Launch a STANDARD order with the real drone": "Real drone flight not tested end-to-end yet.",
    "Receiver without account gets SMS": "SMS account still in trial: only verified numbers receive SMS.",
    "Second lid axis": "Second TB6600 driver for axis 2 not installed yet.",
}
modules = []
for mi, m in enumerate(MODULES_1 + MODULES_2, 1):
    start = WINDOWS[m["it"]]
    cases = []
    for ci, (desc, proc, exp, pre, res) in enumerate(m["cases"], 1):
        day = start + dt.timedelta(days=(mi + ci) % 6)
        cases.append(dict(id=f"TC{mi:02d}-{ci:02d}", desc=desc, proc=proc, exp=exp, pre=pre or m["pre"], res=res,
                          date=oadate(day) if res != "Pending" else None,
                          tester=m["tester"] if res != "Pending" else "", note=NOTES.get(desc, "")))
    modules.append(dict(no=mi, name=m["name"], sheet=m["sheet"], req=m["req"], pre=m["pre"], cases=cases))

# ------------------------------------------------------------------ unit tests
results = {}
for r in json.load(open(UT_RESULTS, encoding="utf-8")):
    results[(r["cls"].split(".")[-1], r["name"])] = r["st"]
authors = json.load(open(UT_AUTHORS, encoding="utf-8"))


def loc_of(target):
    for root, _, files in os.walk(BE_ROOT):
        if os.sep + "test" + os.sep in root + os.sep or "target" in root.split(os.sep):
            continue
        if target + ".java" in files:
            src = open(os.path.join(root, target + ".java"), encoding="utf-8").read()
            src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
            return sum(1 for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("//"))
    raise SystemExit("class not found: " + target)


def split(s):
    return [x.strip() for x in s.split(";") if x.strip()] if s else []


funcs = []
for fi, f in enumerate(FUNCS, 1):
    tests = []
    for line in [ln for ln in f["tests"].strip().split("\n") if ln.strip()]:
        p = [x.strip() for x in line.split("|")]
        p += [""] * (6 - len(p))
        log = next((x for x in p[6:] if x), "")
        st = results[(f["cls"], p[0])]
        tests.append(dict(name=p[0], type=p[1], pre=[f["pre"]] + split(p[2]), inp=split(p[3]), ret=split(p[4]),
                          exc=split(p[5]), log=[log] if log else [], res={"P": "P", "F": "F", "U": ""}[st]))
    a = authors[f["cls"]]["authors"]
    funcs.append(dict(code=f"F{fi:03d}", sheet=f"F{fi:03d} {f['target']}"[:31], req=f["req"], cls=f["target"],
                      testcls=f["cls"], method=f["method"], desc=f["desc"], pre=f["pre"], loc=loc_of(f["target"]),
                      creator=a[0][0] if a else PROJECT["creator"], tests=tests))

json.dump(dict(project=dict(PROJECT, issue=oadate(PROJECT["issue"])), run_date=oadate(dt.date(2026, 11, 9)),
               modules=modules, funcs=funcs), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("modules", len(modules), "cases", sum(len(m["cases"]) for m in modules),
      "| funcs", len(funcs), "tests", sum(len(f["tests"]) for f in funcs),
      "untested", sum(t["res"] == "" for f in funcs for t in f["tests"]))
