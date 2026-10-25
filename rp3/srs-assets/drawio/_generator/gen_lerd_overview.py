"""Logical ERD overview: every table with every column on one A4 portrait page. Tables are packed in seven columns
(top band → user_profiles → main area → locker_boxes → bottom band) following the planar layout of the conceptual ERD.
No line crosses, touches or runs alongside another and none passes through a table (audited before export).
The full FK graph is not planar, so references that cannot be drawn without a crossing are listed in a note."""
import json
import os
import random
import sys
from dio import Diagram
from erd_data import ENT, REL, M, OUT
from maze import Maze
from geom import polylines_cross, seg_box
from erd_legend import legend

HERE = os.path.dirname(os.path.abspath(__file__))
NOTNULL = json.load(open(os.path.join(HERE, "fk_notnull.json")))
SKIP = {("LockerOrder", "LockerUnit"), ("LockerOrder", "StoreLocation"), ("LockerReport", "LockerUnit"),
        ("PaymentRecord", "UserProfile"), ("BoxAccessLog", "LockerOrder"), ("DroneDeliverySession", "LockerOrder"),
        ("Promotion", "LockerUnit"), ("LockerReport", "MaintenanceSchedule")}

NCOL = 7
TOP = [["RefreshToken", "AuthAccount"], ["SocialIdentity", "AssistantMessage", "AssistantConversation"],
       ["FcmToken", "NotificationMessage"], ["WithdrawalRecord", "UserProfile"], ["TechnicianPresence"],
       ["DroneTechnicianPresence"], ["UserBankAccount"]]
MAIN = [["PromotionClaim", "Promotion", "PromotionUsage", "PaymentRecord", "RefundRecord", "LockerReport", "RepairLog"],
        ["LockerOrder", "ReportAttachment", "LockerReportRating"],
        ["LoyaltyAccount", "PointTransaction", "DroneMission", "OrderStatusHistory", "OrderDetail", "OrderRating",
         "OrderComplaint", "DronePickup"],
        ["Wallet", "WalletTransaction", "DroneDeliverySession", "DroneLockerCommLog", "DroneParcelIncident",
         "DronePickupOffer"],
        ["BleTestGrant", "MaintenanceSchedule", "MaintenanceInspectionLog", ("DroneIncidentTimeline", "DroneParcelIncident"),
         "DroneIncidentResolutionProposal", "DroneIncidentEvidence", "DroneDeliveryRequest"],
        ["LockerUnit", "DroneUnit", "DroneDevice", "DroneIotLog", "DroneMaintenanceLog"],
        ["GatewayDevice", "DeviceStatus", "CabinetControlLog", "StoreLocation", "EmailOtp", "BleSigningKey",
         "EvalCase", "KbDocument", "KbChunk"]]
BOTTOM = [[], [], ["BoxHardwareStatus", "AccessAttempt"], ["LockerBox"], ["BoxAccessLog"], [], []]
FIRST = {("LockerBox", "LockerUnit"): ("B", "T")}
EARLY = {("LockerReport", "UserProfile"): ("L", "L"), ("PromotionClaim", "UserProfile"): ("T", "B")}   # nested lines left of user_profiles          # long hub-to-hub line around the right margin

ROW, HEAD = 18, 24
KW, NW, TYW = 26, 172, 84
TW = KW + NW + TYW
HGAP, VGAP, GAP_TOP, GAP_BOTTOM = 76, 58, 230, 130
TABLE = {c: ENT[c]["table"] for c in ENT}
FKS = {}
for c, col, p, k in REL:
    FKS.setdefault(c, []).append(col)
ALIGN = {}                     # (name, other): start no higher than the top of `other` (placed in an earlier column)
for col in MAIN:
    for i, n in enumerate(col):
        if isinstance(n, tuple):
            ALIGN[n[0]] = n[1]
            col[i] = n[0]
placed = [n for band in (TOP, MAIN, BOTTOM) for col in band for n in col]
assert sorted(placed) == sorted(ENT), set(ENT) ^ set(placed)


def ordered(cls):
    fs = ENT[cls]["fields"]
    pk = [f for f in fs if f["pk"]]
    fk = [f for f in fs if f["name"] in FKS.get(cls, []) and not f["pk"]]
    return pk + fk + [f for f in fs if f not in pk and f not in fk]


def height(cls):
    return HEAD + len(ENT[cls]["fields"]) * ROW


colx = [40 + i * (TW + HGAP) for i in range(NCOL)]
page_w = colx[-1] + TW
boxes = {}
top_h = max(sum(height(n) + VGAP for n in col) for col in TOP)
y_top = 100
for i, col in enumerate(TOP):                 # top band: bottom-aligned (user_profiles closes the middle column)
    y = y_top + top_h - sum(height(n) + VGAP for n in col)
    for n in col:
        boxes[n] = (colx[i], y, TW, height(n))
        y += height(n) + VGAP
y_main = y_top + top_h - VGAP + GAP_TOP
main_h = 0
for i, col in enumerate(MAIN):
    yy = y_main
    for n in col:
        if n in ALIGN:
            yy = max(yy, boxes[ALIGN[n]][1])
        boxes[n] = (colx[i], yy, TW, height(n))
        yy += height(n) + VGAP
    main_h = max(main_h, yy - y_main)
y_bottom = y_main + main_h - VGAP + GAP_BOTTOM
for i, col in enumerate(BOTTOM):
    yy = y_bottom
    for n in col:
        boxes[n] = (colx[i], yy, TW, height(n))
        yy += height(n) + VGAP

pairs, seen = [], set()
for child, col, parent, kind in REL:
    if (child, parent) in seen:
        continue
    seen.add((child, parent))
    pairs.append((child, parent, kind, (child, parent) in SKIP, NOTNULL[f"{child}.{col}"]))


def dist(t):
    a, b = boxes[t[0]], boxes[t[1]]
    return abs((a[0] + a[2] / 2) - (b[0] + b[2] / 2)) + abs((a[1] + a[3] / 2) - (b[1] + b[3] / 2))


WP = (max(b[0] + b[2] for b in boxes.values()) + 70, max(b[1] + b[3] for b in boxes.values()) + 60, 48, 48)


def attempt(order):
    # FIRST lines are forced around the outside of the page through a waypoint below the bottom-right corner
    mz = Maze({**boxes, "_wp": WP}, cell=6, margin=8, stub_cells=3, spacing=1, bend=8, pad=200)
    done, bad = [], []
    first = [t for t in order if (t[0], t[1]) in FIRST]
    for t in first:
        sa, sb = FIRST[(t[0], t[1])]
        leg1 = mz.route(t[0], "_wp", sides_a=sa, sides_b="L", max_pops=400000)
        leg2 = mz.route("_wp", t[1], sides_a="T", sides_b=sb, max_pops=400000) if leg1 else None
        if leg2 is None:
            bad.append(t)
            continue
        p1, p2 = leg1[0], leg2[0]
        pts = p1[:-1] + [(p2[0][0], p1[-1][1])] + p2[1:]
        done.append((t, (pts, leg1[1], leg2[2])))
    early = [next(t for t in order if (t[0], t[1]) == e) for e in EARLY if any((t[0], t[1]) == e for t in order)]
    for t in early:
        sa, sb = EARLY[(t[0], t[1])]
        res = mz.route(t[0], t[1], sides_a=sa, sides_b=sb, max_pops=400000)
        (bad if res is None else done).append(t if res is None else (t, res))
    for t in [t for t in order if t not in first and t not in early]:
        res = mz.route(t[0], t[1], max_pops=150000)
        (bad if res is None else done).append(t if res is None else (t, res))
    return mz, done, bad


core = sorted([p for p in pairs if not p[3] or (p[0], p[1]) in FIRST], key=dist)
extra = sorted([p for p in pairs if p[3] and (p[0], p[1]) not in FIRST], key=dist)
rng = random.Random(7)
order, best, priority = list(core), None, []
for it in range(int(sys.argv[1]) if len(sys.argv) > 1 else 16):
    mz, done, bad = attempt(order)
    print(f"attempt {it}: {len(bad)} failed {[(t[0], t[1]) for t in bad]}", flush=True)
    if best is None or len(bad) < len(best[2]):
        best = (order, done, bad)
    if not bad:
        break
    for t in bad:
        if t not in priority:
            priority.append(t)
    pri = list(priority)
    rng.shuffle(pri)
    near = [p for p in core if dist(p) <= 450 and p not in pri]
    rest = sorted([p for p in core if p not in near and p not in pri], key=lambda t: dist(t) * (0.7 + 0.6 * rng.random()))
    k = rng.randint(0, len(pri))
    order = near + pri[:k] + rest + pri[k:]
win_order, done, bad = best
debug = bool(bad)
if not debug:
    best_x = None
    for it in range(int(sys.argv[2]) if len(sys.argv) > 2 else 6):
        mz, done, bad = attempt(win_order)
        ex = list(extra)
        rng.shuffle(ex)
        for t in ex:
            res = mz.route(t[0], t[1], max_pops=900000)
            (bad if res is None else done).append(t if res is None else (t, res))
        print(f"extras pass {it}: omitted {[(t[0], t[1]) for t in bad]}", flush=True)
        if best_x is None or len(bad) < len(best_x[1]):
            best_x = (done, bad)
    done, bad = best_x
else:
    print("DEBUG: core failed", [(t[0], t[1]) for t in bad])

polys = [r[1][0] for r in done]
names = [(r[0][0], r[0][1]) for r in done]
cross = sum(1 for i in range(len(polys)) for j in range(i + 1, len(polys)) if polylines_cross(polys[i], polys[j]))
thru = sum(1 for (a, b), pts in zip(names, polys) for n, bx in boxes.items() if n not in (a, b)
           for q in range(len(pts) - 1) if seg_box(pts[q], pts[q + 1], bx, 0))
print(f"audit crossings={cross} through-tables={thru}, drawn {len(done)} of {len(pairs)}")
assert cross == 0 and thru == 0

d = Diagram("05-logical-erd-overview" if not debug else "_debug-overview")
d.vertex("Logical ERD — Overview (all tables, all columns)", 40, 30, 1600, 44,
         "text;html=1;align=left;verticalAlign=middle;fontSize=30;fontStyle=1;fontColor=#000000;")
ids = {}
cell = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;html=1;"
for n, (x, y0, w, h) in boxes.items():
    tid = d.vertex(TABLE[n], x, y0, w, h,
                   "shape=table;startSize=24;container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;"
                   "fontStyle=1;align=center;resizeLast=1;html=1;fontSize=14;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;")
    ids[n] = tid
    g, gw = 1, w
    fs = ordered(n)
    lines = -(-len(fs) // g)
    for i in range(lines):
        rid = d.vertex("", 0, HEAD + i * ROW, w, ROW,
                       "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;"
                       "dropTarget=0;top=0;left=0;right=0;bottom=0;", parent=tid)
        for j in range(g):
            idx = i + j * lines
            f = fs[idx] if idx < len(fs) else {"name": "", "type": "", "pk": False}
            key = "PK" if f["pk"] else ("FK" if f["name"] in FKS.get(n, []) else "")
            x0 = j * gw
            d.vertex(key, x0, 0, KW, ROW, cell + "align=center;fontStyle=1;fontColor=#000000;", parent=rid)
            d.vertex(f["name"], x0 + KW, 0, NW, ROW,
                     cell + "align=left;spacingLeft=3;fontColor=#000000;" + ("fontStyle=4;" if f["pk"] else ""), parent=rid)
            d.vertex(f["type"], x0 + KW + NW, 0, gw - KW - NW, ROW, cell + "align=left;spacingLeft=3;fontColor=#444444;", parent=rid)
EDGE = "edgeStyle=none;rounded=0;html=1;strokeColor=#000000;endFill=0;startFill=0;endSize=9;startSize=9;"


def anchor(prefix, n, p):
    x, y0, w, h = boxes[n]
    return f"{prefix}X={(p[0] - x) / w:.4f};{prefix}Y={(p[1] - y0) / h:.4f};{prefix}Dx=0;{prefix}Dy=0;{prefix}Perimeter=0;"


for (child, parent, kind, _, nn), (pts, sa, sb) in done:
    st = EDGE + ("startArrow=ERzeroToMany;" if kind == M else "startArrow=ERzeroToOne;")
    st += "endArrow=ERone;" if nn else "endArrow=ERzeroToOne;"
    d.edge(ids[child], ids[parent], st + anchor("exit", child, pts[0]) + anchor("entry", parent, pts[-1]), points=pts[1:-1])
bottom = max([b[1] + b[3] for b in boxes.values()] + [p[1] for r in done for p in r[1][0]])
note = ("PK = primary key · FK = reference column. Parent end: | = exactly one (FK NOT NULL), o| = zero or one (FK nullable). "
        "Child end: o< = zero or many, o| = zero or one. Each microservice owns its schema, so cross-service references are logical IDs.")
if bad:
    refs = ", ".join(f"{TABLE[c]} → {TABLE[p]}" for c, p, *_ in bad)
    note += (" The full reference graph is not planar, so these references are not drawn here to keep lines from crossing "
             f"(they are drawn on pages 1/4–4/4): {refs}.")
d.vertex(note, 40, bottom + 24, page_w - 40, 48, "text;html=1;align=left;verticalAlign=top;fontSize=15;fontColor=#555555;whiteSpace=wrap;")
legend(d, 40, bottom + 80, font=16)
print(d.save(OUT if not debug else HERE, scale=2.0 if not debug else 0.5))
