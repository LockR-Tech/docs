"""Fill form BM04 (Review 2 Commitment) for FA26SE002 – draft before the review.

Run: uv run --no-project --with python-docx python build_bm04.py

Features, NFRs, out-of-scope items, workflows and demo scenarios are read from build_brief.py (Design Brief,
Appendix A) and the required fixes from build_bm02.py, so the forms cannot drift apart.
Highlighted yellow: proposals the team must confirm, and fields completed at or after Review 2.
Reviewer fields (verification, decision, signatures) stay empty.
"""
import copy
import os
import re
from collections import Counter

import docx

from formfill import (FULL_NAME, LEADER, MEMBER_ORDER, STUDENT_ID, TEAM_LINE, TODO, member_names, fill_column, fill_table, keep_rows_together,
                      rebrand_sep490, remove_grey_guidance, set_widths)
from ci_test_map import E2E_CI, FEATURE_CI, NFR_CI, STATE_CI

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT_DIR, 'bieu-mau', 'SWP490_R2_BM04_Review2_Commitment_1.docx')
OUT = os.path.join(OUT_DIR, 'SEP490_FA26SE002_R2_Commitment.docx')


def load_content(script, marker):
    """Run the content part of another build script (everything before marker) and return its names."""
    src = open(os.path.join(OUT_DIR, script), encoding='utf-8').read().split(marker)[0]
    ns = {'__file__': os.path.join(OUT_DIR, script)}
    exec(compile(src, script, 'exec'), ns)
    return ns


BRIEF = load_content('build_brief.py', '# ---------------------------------------------------------------- helpers')
SELF = load_content('build_bm02.py', '\ndef summary_rows')

OWNER_ROW = {o[0]: o for o in BRIEF['OWNERS']}
# Every member is written by full name in the team order (formfill.MEMBER_ORDER); the short name is only an
# internal key shared with build_brief.py / build_bm02.py.
SHORT_OF = {FULL_NAME[s]: s for s in ('Vi', 'Bình', 'Huy', 'Nhã')}
MEMBERS = [  # short name, full name, student id, role, owned workflow (role and workflow from the Ownership Map)
    (SHORT_OF[full], full, STUDENT_ID[full], OWNER_ROW[full][1], OWNER_ROW[full][3]) for full in MEMBER_ORDER
]
FULL_OF = {s: f for f, s in SHORT_OF.items()}
WF_OWNER = {m[4]: m[0] for m in MEMBERS}
OWNER_WF = {m[0]: m[4] for m in MEMBERS}

# Balanced 5 features per member (20 features / 4 members = 5 each), matching real git authorship on tag review-2:
# Vi (5): F-10, F-11, F-12, F-17, F-20
# Bình (5): F-02, F-03, F-04, F-06, F-13
# Huy (5): F-01, F-05, F-07, F-09, F-16
# Nhã (5): F-08, F-14, F-15, F-18, F-19
FEATURE_OWNER = {
    'F-01': 'Huy', 'F-02': 'Bình', 'F-03': 'Bình', 'F-04': 'Bình', 'F-05': 'Huy', 'F-06': 'Bình',
    'F-07': 'Huy', 'F-08': 'Nhã', 'F-09': 'Huy', 'F-10': 'Vi', 'F-11': 'Vi', 'F-12': 'Vi',
    'F-13': 'Bình', 'F-14': 'Nhã', 'F-15': 'Nhã', 'F-16': 'Huy', 'F-17': 'Vi', 'F-18': 'Nhã',
    'F-19': 'Nhã', 'F-20': 'Vi',
}
NFR_OWNER = {'N1': 'Nhã', 'N2': 'Huy', 'N3': 'Vi', 'N4': 'Bình', 'N5': 'Huy', 'N6': 'Nhã'}
NFR_WORKFLOW = {'N1': 'WF-02', 'N2': 'WF-02', 'N3': 'WF-01', 'N4': 'WF-02', 'N5': 'WF-02', 'N6': 'WF-02'}
# 57 state transitions (Design Brief A3), one test each, placed in the workflow that exercises the transition.
# The owner split balances the test load (32, 32, 32, 31 = 127 total); entity, transitions, owner.
STATE_TESTS = {
    'WF-01': [('Stage', 15, 'Vi'),    # main flight & home pickup stages
              ('Stage', 3, 'Nhã'),    # parcel-drop & recovery stages
              ('Drone', 4, 'Huy'),    # order accepted, launch, mission done, fault in flight
              ('Order', 3, 'Nhã')],   # drone order: create, delivered to cell, cancel / failed / dropped
    'WF-02': [('Order', 6, 'Bình'),   # create, pay & drop, cancel / unpaid, picked up / ended, overdue, expired
              ('Box', 5, 'Huy')],     # add, reserve, drop, order canceled, order closed
    'WF-03': [('Box', 5, 'Bình'),     # reports from AVAILABLE / OCCUPIED, fault confirmed, rejected, resolved
              ('Ticket', 4, 'Bình')],  # report, claim / assign, resolve, reject
    'WF-04': [('Box', 5, 'Huy'),      # fault reported, cleaning start/end, out of service, back to service
              ('Drone', 7, 'Nhã')],   # add, charge, fault reported, set maintenance x2, resolved, done
}
SUPPORTING = {
    'WF-01': 'Bình, Huy, Nhã',
    'WF-02': 'Bình, Nhã, Vi',
    'WF-03': 'Nhã, Huy, Vi',
    'WF-04': 'Bình, Huy, Vi',
}
DOC_SECTIONS = {
    'Vi': 'Report 3 §3.2.19–20, §3.4.1, §3.6.2; Report 4 §3.14–17, §3.26; Report 5 Drone Delivery & Telemetry',
    'Bình': 'Report 3 §3.2.9–18, §3.2.21–26, §3.3.4–7; Report 4 §3.6–7, §3.9–13, §3.19; Report 5 Orders & Payment',
    'Huy': 'Report 3 §3.1–3.2.5, §3.2.31–32, §3.5, §3.6.1, §3.6.5, §3.6.10–11; Report 4 §1–2, §3.1–5, §3.8, §3.21–25',
    'Nhã': 'Report 3 §3.3.1, §3.3.8, §3.3.10, §3.4.2–5, §3.6.6–7; Report 4 §3.18, §3.20, §3.27; Report 5 Maintenance',
}
ACTIVITY = {
    'WF-01': 'Pending G3 – source docs/rp3/srs-assets/drawio/06c-activity-drone-delivery.drawio',
    'WF-02': 'Pending G3 – source 06b-activity-rent-locker.drawio, 06a-activity-send-parcel.drawio',
    'WF-03': 'Pending G3 – source 06f-activity-handle-incident-ticket.drawio',
    'WF-04': 'Pending G3 – source 06g-activity-periodic-inspection.drawio (add drone path, G7)',
}


def expand(ids):
    """'F-01–F-05, F-09' -> ['F-01', ..., 'F-05', 'F-09']"""
    out = []
    for part in ids.split(','):
        nums = [int(n) for n in re.findall(r'\d+', part)]
        out += [f'F-{n:02d}' for n in range(nums[0], nums[-1] + 1)]
    return out


FEATURES = {f[0]: f for f in BRIEF['FEATURES']}
WORKFLOWS = {w[0]: w for w in BRIEF['WORKFLOWS']}
WF_FEATURES = {wf: expand(w[5]) for wf, w in WORKFLOWS.items()}


def home_workflow(fid):
    """Workflow under which a feature's tests are counted once: its owner's workflow if listed there."""
    listed = [wf for wf, fs in WF_FEATURES.items() if fid in fs]
    own = OWNER_WF[FEATURE_OWNER[fid]]
    return own if own in listed else listed[0]


HOME = {fid: home_workflow(fid) for fid in FEATURES}


def tc_ids(fid):
    return f'TC-F{fid[2:]}-01..03'


def by_key(pairs):
    """[(key, n), …] -> 'key n, …' summed per key, largest first."""
    acc = {}
    for k, n in pairs:
        acc[k] = acc.get(k, 0) + n
    return ', '.join(f'{k} {n}' for k, n in sorted(acc.items(), key=lambda kv: -kv[1]))


def wf_counts(wf):
    feat = 3 * sum(1 for f in FEATURES if HOME[f] == wf)
    states = sum(n for _, n, _ in STATE_TESTS[wf])
    nfr = sum(1 for n, w in NFR_WORKFLOW.items() if w == wf)
    return feat, 1, states, nfr, feat + 1 + states + nfr


def member_counts(name):
    feat = 3 * sum(1 for f, o in FEATURE_OWNER.items() if o == name)
    states = sum(n for parts in STATE_TESTS.values() for _, n, o in parts if o == name)
    nfr = sum(1 for o in NFR_OWNER.values() if o == name)
    return feat + 1 + states + nfr


WF_TOTALS = {wf: wf_counts(wf)[4] for wf in WORKFLOWS}
TOTAL = sum(WF_TOTALS.values())
A3_TOTAL = int(BRIEF['TEST_TARGET'][-1][2])
assert TOTAL == sum(member_counts(m[0]) for m in MEMBERS) == A3_TOTAL, 'workflow / member totals must match A3'
assert sum(n for parts in STATE_TESTS.values() for _, n, _ in parts) == int(BRIEF['TEST_TARGET'][2][0])

# Automated in CI: committed test cases already backed by a CI test at tag review-2 (ci_test_map.py).
for wf, parts in STATE_TESTS.items():
    want = Counter()
    for e, n, o in parts:
        want[(e, o)] += n
    assert want == Counter((s[1], s[2]) for s in STATE_CI if s[0] == wf), f'ci_test_map STATE_CI differs for {wf}'
assert set(FEATURE_CI) == set(FEATURE_OWNER) and all(len(v) == 3 for v in FEATURE_CI.values())


def wf_auto(wf):
    feat = sum(1 for f in FEATURES if HOME[f] == wf for test in FEATURE_CI[f] if test)
    e2e = 1 if E2E_CI[wf] else 0
    states = sum(1 for s in STATE_CI if s[0] == wf and s[4])
    nfr = sum(1 for n, w in NFR_WORKFLOW.items() if w == wf and NFR_CI[n])
    return feat, e2e, states, nfr, feat + e2e + states + nfr


def member_auto(name):
    feat = sum(1 for f, o in FEATURE_OWNER.items() if o == name for test in FEATURE_CI[f] if test)
    e2e = 1 if E2E_CI[OWNER_WF[name]] else 0
    states = sum(1 for s in STATE_CI if s[2] == name and s[4])
    nfr = sum(1 for n, o in NFR_OWNER.items() if o == name and NFR_CI[n])
    return feat + e2e + states + nfr


WF_AUTO = {wf: wf_auto(wf)[4] for wf in WORKFLOWS}
AUTO = sum(WF_AUTO.values())
assert AUTO == sum(member_auto(m[0]) for m in MEMBERS), 'automated totals by workflow and by member must match'
DUE = 'Before Defense 1.1'


def pct(n, of):
    return f'{n} ({round(100 * n / of)} %)'

# Required fixes: Planned items of BM02, one owner, workflow = the owner's workflow.
FIXES = []
for sr in SELF['FINDINGS']:
    resp = SELF['RESPONSE'][sr[0]]
    if resp.startswith('Planned'):
        item, owner_due = resp[len('Planned – '):].rsplit(' – ', 1)
        owner, due = [x.strip() for x in owner_due.split(',')]
        FIXES.append([f'RF-{len(FIXES) + 1:02d}', f'{item} (BM02 {sr[0]})', OWNER_WF[owner], owner, due])

# Items from the Review 2 minutes, numbered after the BM02 items: (item, owner short name, due dd/mm/yyyy).
# Empty until the team has the minutes; the workflow is the owner's workflow, as for the BM02 items.
MINUTES = []
MINUTES_FIXES = [[f'RF-{len(FIXES) + i + 1:02d}', f'{item} (Review 2 minutes)', OWNER_WF[owner], owner, due]
                 for i, (item, owner, due) in enumerate(MINUTES)]

# ---------------------------------------------------------------- build
d = docx.Document(SRC)
rebrand_sep490(d)


def drop_block(start_text, end_text):
    """Remove every body element from the paragraph starting with start_text up to (not incl.) end_text."""
    body = d.element.body
    removing = False
    for el in list(body):
        text = ''.join(el.itertext()).strip() if el.tag.endswith('}p') else ''
        if text.startswith(start_text):
            removing = True
        elif removing and text.startswith(end_text):
            break
        if removing:
            body.remove(el)


drop_block('6.5 Workflow WF-05', '7. Individual Commitments')
drop_block('7.5 Member 5', '8. Summary and Cross-check')
t = d.tables

fill_column(t[0], [
    'FA26SE002 (group GFA26SE32)',
    'Drone Delivery and Smart Locker Management System (DDSLMS) – product name Lock.R',
    TEAM_LINE,
    'Đặng Ngọc Minh Đức · Đỗ Hữu Tiến',
    '06/11/2026', 'ThinhDP2', 'TaiNT51',
    '0.1 (draft before Review 2)', '09/11/2026',
])
fill_column(t[1], ['2.0', 'YES', 'SEP490_FA26SE002_R2_Registration.pdf'])

fill_table(t[2], [[f, FEATURES[f][1], FEATURES[f][2], FEATURES[f][3],
                   ', '.join(wf for wf, fs in WF_FEATURES.items() if f in fs),
                   FULL_NAME[FEATURE_OWNER[f]]] for f in FEATURES])
set_widths(t[2], [1.2, 2.8, 2.2, 6.0, 1.8, 3.0])
fill_table(t[3], [[n[0], n[1], n[2], n[3], n[4], FULL_NAME[NFR_OWNER[n[0]]]] for n in BRIEF['NFRS']])
set_widths(t[3], [1.0, 2.2, 3.4, 3.4, 4.4, 3.0])
fill_table(t[4], BRIEF['OUT_OF_SCOPE'])

demos = BRIEF['DEMOS']
for i, wf in enumerate(sorted(WORKFLOWS)):
    w = WORKFLOWS[wf]
    base = 5 + 6 * i
    owner = WF_OWNER[wf]
    fill_column(t[base], [
        w[1], FULL_NAME[owner], member_names(SUPPORTING[wf]), w[2], w[3], w[4], w[6], ACTIVITY[wf],
    ])
    fill_table(t[base + 1], [[f, FEATURES[f][1], FEATURES[f][3],
                              tc_ids(f) + ('' if HOME[f] == wf else f' (counted in {HOME[f]})')]
                             for f in WF_FEATURES[wf]])
    set_widths(t[base + 1], [1.4, 3.0, 9.0, 3.6])
    fill_table(t[base + 2], [[s[0], s[2], s[3], s[4], s[5], member_names(s[6])] for s in demos if s[1] == wf])
    set_widths(t[base + 2], [1.6, 1.8, 3.2, 3.8, 3.4, 3.2])
    feat, e2e, states, nfr, total = wf_counts(wf)
    a_feat, a_e2e, a_states, a_nfr, a_total = wf_auto(wf)
    feat_owners = by_key((FULL_NAME[FEATURE_OWNER[f]], 3) for f in FEATURES if HOME[f] == wf)
    nfr_ids = [n for n, x in NFR_WORKFLOW.items() if x == wf]
    tests = [
        ['Feature tests (≥ 3 per feature)', str(feat), str(a_feat), feat_owners],
        ['End-to-end workflow test (≥ 1)', str(e2e), str(a_e2e), FULL_NAME[owner]],
        ['State transition tests (≥ 1 per transition)',
         f'{states} ({by_key((e, n) for e, n, _ in STATE_TESTS[wf])})', str(a_states),
         by_key((FULL_NAME[o], n) for _, n, o in STATE_TESTS[wf])],
        ['NFR tests (≥ 1 per NFR)', f'{nfr} ({", ".join(nfr_ids)})' if nfr_ids else '0', str(a_nfr),
         ', '.join(sorted({FULL_NAME[NFR_OWNER[n]] for n in nfr_ids})) or '–'],
        ['Total for this workflow', str(total), pct(a_total, total), ''],
    ]
    fill_table(t[base + 3], tests)
    fill_column(t[base + 4], [None, None, '1 of 1 (100 %)',
                              '≥ 90 %; 100 % of main-path tests of its features', None], start_row=1)

DS_OF = {wf: [s[0] for s in demos if s[1] == wf] for wf in WORKFLOWS}
for i, (short, full, sid, role, wf) in enumerate(MEMBERS):
    base = 29 + 5 * i
    fill_column(t[base], [full, sid, role])
    owned = [f for f, o in FEATURE_OWNER.items() if o == short]
    owner_row = OWNER_ROW[FULL_OF[short]]
    fill_table(t[base + 1], [
        ['Main workflow(s) owned', wf, WORKFLOWS[wf][1]],
        ['Mandatory features owned', ', '.join(owned), ''],
        ['Modules / entities owned', owner_row[2], ''],
        ['Design decisions owned (D-IDs)', owner_row[4], ''],
        ['NFRs responsible', ', '.join(n for n, o in NFR_OWNER.items() if o == short) or '–', ''],
    ])
    my_fixes = [f[0] for f in FIXES if f[3] == short]
    fill_table(t[base + 2], [
        ['Functional test cases written', str(member_counts(short)), DUE],
        ['Of which automated in CI', pct(member_auto(short), member_counts(short)), DUE],
        ['Demo scenarios presented', ', '.join(DS_OF[wf]), DUE],
        ['Required fixes owned (section 9)', ', '.join(my_fixes) or '–', 'See section 9'],
        ['Documentation sections (Report / section)', DOC_SECTIONS[short], '22/11/2026'],
    ])

t81, t82, t83, t84, t9, t11 = t[49], t[50], t[51], t[52], t[53], t[54]
rows = []
for wf in sorted(WORKFLOWS):
    rows.append([wf, FULL_NAME[WF_OWNER[wf]], str(len(WF_FEATURES[wf])), f'{len(DS_OF[wf]) - 1} / 1',
                 str(WF_TOTALS[wf]), str(WF_AUTO[wf])])
rows.append(['Total', '', f'{len(FEATURES)} distinct', f'{len(WORKFLOWS)} / {len(WORKFLOWS)}', str(TOTAL),
             pct(AUTO, TOTAL)])
fill_table(t81, rows)
rows = []
for short, full, sid, role, wf in MEMBERS:
    rows.append([full, wf, str(sum(1 for o in FEATURE_OWNER.values() if o == short)),
                 str(member_counts(short)), str(member_auto(short)), ', '.join(DS_OF[wf]), ''])
rows.append(['Total', str(len(MEMBERS)), str(len(FEATURES)), str(TOTAL), pct(AUTO, TOTAL),
             str(len(demos)), ''])
fill_table(t82, rows)
fill_column(t83, [str(len(WORKFLOWS)), f'{len(WORKFLOWS)} / {len(WORKFLOWS)}', str(TOTAL), pct(AUTO, TOTAL)])
fill_column(t84, ['100 %', '100 % main; ≥ 80 % exception', f'≥ {TOTAL}', '≥ 90 %; 100 % main-path',
                  '≥ 50 % in CI', '0 open Critical / High', 'Yes'], col=2, start_row=1)
fill_table(t9, [f[:3] + [FULL_NAME[f[3]]] + f[4:] for f in FIXES + MINUTES_FIXES])
set_widths(t9, [1.2, 8.3, 2.0, 3.0, 2.5])
fill_column(t11, [None, 'Đỗ Phúc Thịnh', 'Nguyễn Trọng Tài', 'Đặng Ngọc Minh Đức', LEADER],
            col=1)
# All four members confirm: one row per other member, cloned from the Team leader row (same formatting).
leader_tr = t11.rows[-1]._tr
for name in [n for n in MEMBER_ORDER if n != LEADER]:
    t11._tbl.append(copy.deepcopy(leader_tr))
    role_cell, name_cell = t11.rows[-1].cells[:2]
    role_cell.paragraphs[0].runs[0].text = 'Team member'
    for r in role_cell.paragraphs[0].runs[1:]:
        r.text = ''
    name_cell.paragraphs[0].runs[0].text = name
    for r in name_cell.paragraphs[0].runs[1:]:
        r.text = ''

remove_grey_guidance(d)
keep_rows_together(d)
d.save(OUT)
print('saved', OUT, '| workflows', WF_TOTALS, '| total', TOTAL, '| fixes', len(FIXES))
