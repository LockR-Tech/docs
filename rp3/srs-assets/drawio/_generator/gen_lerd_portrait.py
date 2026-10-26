"""Logical ERD split into four A4 portrait pages (three columns of stacked tables) by business area. Each page: tables with PK/FK, column names and
types; lines leave from the FK row; no line crosses, touches or runs alongside another, none passes a table."""
import random
import sys
from dio import Diagram
from erd_data import ENT, REL, M, OUT
from maze import Maze
from geom import polylines_cross, seg_box
from erd_legend import parent_end, legend

ROW, HEAD, TW = 24, 30, 344          # row height, header height, table width
KW, NW = 34, 205                     # key / name column widths (type column = rest)
MAX_ROWS = 14
VGAP, HGAP = 72, 150                 # gap between stacked tables / between columns

TABLE = {cls: ENT[cls]["table"] for cls in ENT}
FK_ORDER = {}
# relationships that must enter their parent on a given side to leave room for others
ENTRY = {}

# page: title, {class: (column, order in column)}, ghosts {class: (column, order[, rows])}, max rows per table
PAGES = [
    ("05a-logical-erd-account", "Logical ERD (1/4) — Accounts, Notifications &amp; AI Assistant", {
        "RefreshToken": (0, 0), "SocialIdentity": (0, 1), "EmailOtp": (0, 2), "KbDocument": (0, 3), "KbChunk": (0, 4), "EvalCase": (0, 5),
        "AuthAccount": (1, 0), "UserProfile": (1, 1), "AssistantConversation": (1, 2), "AssistantMessage": (1, 3),
        "TechnicianPresence": (2, 0), "DroneTechnicianPresence": (2, 1), "NotificationMessage": (2, 2), "FcmToken": (2, 3),
    }, {}, 30),
    ("05b-logical-erd-locker", "Logical ERD (2/4) — Stores, Lockers, IoT &amp; Maintenance", {
        "GatewayDevice": (0, 0), "CabinetControlLog": (0, 1), "BoxHardwareStatus": (0, 2), "AccessAttempt": (0, 3),
        "BoxAccessLog": (0, 4), "RepairLog": (0, 6), "BleSigningKey": (0, 7),
        "DeviceStatus": (1, 0), "LockerUnit": (1, 1), "LockerBox": (1, 2), "LockerReport": (1, 3), "ReportAttachment": (1, 4),
        "StoreLocation": (2, 1), "BleTestGrant": (2, 2), "MaintenanceSchedule": (2, 4),
        "MaintenanceInspectionLog": (2, 5), "LockerReportRating": (2, 7),
    }, {"UserProfile": (2, 6, 4), "LockerOrder": (0, 5), "DroneUnit": (2, 3)}, 14),
    ("05c-logical-erd-order", "Logical ERD (3/4) — Orders, Payments, Promotions &amp; Loyalty", {
        "OrderStatusHistory": (0, 0), "OrderDetail": (0, 1), "OrderRating": (0, 2), "OrderComplaint": (0, 3),
        "PaymentRecord": (0, 4), "RefundRecord": (0, 5),
        "LockerOrder": (1, 1), "Wallet": (1, 3), "WalletTransaction": (1, 4), "WithdrawalRecord": (1, 5),
        "Promotion": (2, 2), "PromotionUsage": (2, 3), "PointTransaction": (2, 4), "LoyaltyAccount": (2, 5),
        "PromotionClaim": (2, 6), "UserBankAccount": (2, 7),
    }, {"LockerBox": (1, 0), "UserProfile": (1, 2, 6), "StoreLocation": (2, 0), "LockerUnit": (2, 1)}, 14),
    ("05d-logical-erd-drone", "Logical ERD (4/4) — Drones, Missions &amp; Parcel Incidents", {
        "DroneMaintenanceLog": (0, 0), "DroneDevice": (0, 1), "DroneIotLog": (0, 2), "DronePickupOffer": (0, 3), "DronePickup": (0, 4),
        "DroneUnit": (1, 1), "DroneMission": (1, 2), "DroneDeliverySession": (1, 4), "DroneLockerCommLog": (1, 5),
        "DroneDeliveryRequest": (2, 1), "DroneParcelIncident": (2, 2), "DroneIncidentEvidence": (2, 3),
        "DroneIncidentTimeline": (2, 4), "DroneIncidentResolutionProposal": (2, 5),
    }, {"LockerUnit": (1, 0), "LockerOrder": (1, 3), "LockerBox": (2, 0)}, 14),
]


def visible(cls, fks, parent_pos=None, max_rows=MAX_ROWS):
    fields = ENT[cls]["fields"]
    pk = [f for f in fields if f["pk"]]
    fk = [f for f in fields if f["name"] in fks and not f["pk"]]
    if cls in FK_ORDER:
        fk.sort(key=lambda f: FK_ORDER[cls].index(f["name"]) if f["name"] in FK_ORDER[cls] else 99)
    elif parent_pos:
        fk.sort(key=lambda f: parent_pos.get(f["name"], (0, 0))[::-1])
    rest = [f for f in fields if not f["pk"] and f["name"] not in fks]
    if len(pk) + len(fk) + len(rest) > max_rows:
        def score(f):
            n = f["name"]
            if n in ("created_at", "updated_at"):
                return 3
            if n in ("status", "order_type", "type", "code", "order_code", "name") or n.endswith("_status"):
                return 0
            if any(k in n for k in ("price", "amount", "total", "fee", "pin", "paid", "weight", "balance", "points")):
                return 1
            return 2
        rest = sorted(rest, key=score)
    keep = pk + fk + rest
    hidden = max(0, len(keep) - max_rows)
    return keep[:max_rows], hidden


def build(page_id, title, place, ghosts, max_rows, attempts):
    on_page = set(place) | set(ghosts)
    rels = [(c, col, p, k) for c, col, p, k in REL if c in place and p in on_page]
    fks = {}
    for c, col, p, k in rels:
        fks.setdefault(c, set()).add(col)
    rows_of, height = {}, {}
    allpos0 = {**place, **ghosts}
    for cls in place:
        ppos = {col: allpos0[p] for c, col, p, k in rels if c == cls}
        vis, hidden = visible(cls, fks.get(cls, set()), ppos, max_rows)
        rows_of[cls] = vis + ([{"name": f"… +{hidden} more columns", "type": "", "pk": False}] if hidden else [])
        height[cls] = HEAD + len(rows_of[cls]) * ROW
    for cls in ghosts:
        pk = next(f for f in ENT[cls]["fields"] if f["pk"])
        extra = ghosts[cls][2] - 1 if len(ghosts[cls]) > 2 else 1
        rows_of[cls] = [pk] + [{"name": "…" if k == 0 else "", "type": "", "pk": False} for k in range(extra)]
        height[cls] = HEAD + len(rows_of[cls]) * ROW
    allpos = {n: tuple(v[:2]) for n, v in {**place, **ghosts}.items()}
    X0, Y0 = 40, 90
    boxes, row_y, stacked = {}, {}, set()
    for col in sorted({c for c, r in allpos.values()}):
        y, prev = Y0, None
        for n in sorted([n for n, (c, r) in allpos.items() if c == col], key=lambda n: allpos[n][1]):
            boxes[n] = (X0 + col * (TW + HGAP), y, TW, height[n])
            for i, f in enumerate(rows_of[n]):
                row_y[(n, f["name"])] = y + HEAD + i * ROW + ROW / 2
            if prev:
                stacked |= {(prev, n), (n, prev)}
            y += height[n] + VGAP
            prev = n

    def dist(t):
        a, b = boxes[t[0]], boxes[t[2]]
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def attempt(order):
        mz = Maze(boxes, cell=5, margin=8, stub_cells=5, spacing=1, bend=8, port_gap=2)
        done, bad = [], []
        order = [r for r in order if (r[0], r[2]) in stacked] + [r for r in order if (r[0], r[2]) not in stacked]
        for c, col, p, k in order:
            res = None
            r1, r2 = allpos[c][1], allpos[p][1]
            if (c, p) in stacked:
                # stacked neighbours: one straight vertical line between facing edges
                res = mz.route(c, p, sides_a="B" if r2 > r1 else "T", sides_b="T" if r2 > r1 else "B")
                if res is None:
                    res = mz.route(c, p, sides_a="LR", sides_b="LRTB", fixed_a=row_y[(c, col)])
            if res is None and (c, col) in ENTRY:
                res = mz.route(c, p, sides_a="LR", sides_b=ENTRY[(c, col)], fixed_a=row_y[(c, col)])
            if res is None:
                res = mz.route(c, p, sides_a="LR", sides_b="LR", fixed_a=row_y[(c, col)])
            if res is None:
                res = mz.route(c, p, sides_a="LR", sides_b="LRTB", fixed_a=row_y[(c, col)])
            if res is None:
                bad.append((c, col, p, k))
            else:
                done.append((c, col, p, k, res))
        return done, bad

    rels.sort(key=dist)
    rng = random.Random(11)
    order, best, priority = list(rels), None, []
    for it in range(attempts):
        done, bad = attempt(order)
        print(f"  {page_id} attempt {it}: {len(bad)} failed {[(c, p) for c, _, p, _ in bad]}", flush=True)
        if best is None or len(bad) < len(best[1]):
            best = (done, bad)
        if not bad:
            break
        for f in bad:
            if f not in priority:
                priority.append(f)
        pri = list(priority)
        rng.shuffle(pri)
        noise = 0.6 if it % 4 else 1.6
        rest = sorted([r for r in rels if r not in pri], key=lambda t: dist(t) * (1 - noise / 2 + noise * rng.random()))
        k = rng.randint(0, len(pri))
        order = pri[:k] + rest[:rng.randint(0, len(rest))] + pri[k:]
        order += [r for r in rels if r not in order]
    done, bad = best
    debug = bool(bad)
    if bad:
        print("  FAILED", page_id, [(c, p) for c, _, p, _ in bad])

    polys = [r[4][0] for r in done]
    names = [(r[0], r[2]) for r in done]
    cross = sum(1 for i in range(len(polys)) for j in range(i + 1, len(polys)) if polylines_cross(polys[i], polys[j]))
    thru = sum(1 for (a, b), pts in zip(names, polys) for n, bx in boxes.items() if n not in (a, b)
               for q in range(len(pts) - 1) if seg_box(pts[q], pts[q + 1], bx, 0))
    print(f"  {page_id}: audit crossings={cross} through-tables={thru}")
    assert cross == 0 and thru == 0

    d = Diagram(page_id if not debug else "_debug-" + page_id)
    d.vertex(title, X0, 30, 1200, 36, "text;html=1;align=left;verticalAlign=middle;fontSize=22;fontStyle=1;fontColor=#000000;")
    ids = {}
    for n, (x, y, w, h) in boxes.items():
        ghost = n in ghosts
        tst = ("shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
               "align=center;resizeLast=1;html=1;fontSize=15;" +
               ("fillColor=#F5F5F5;strokeColor=#999999;dashed=1;fontColor=#666666;" if ghost else "fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;"))
        label = TABLE[n] + (" (see other page)" if ghost else "")
        tid = d.vertex(label, x, y, w, h, tst)
        ids[n] = tid
        for i, f in enumerate(rows_of[n]):
            rid = d.vertex("", 0, HEAD + i * ROW, w, ROW,
                           "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;"
                           "dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;", parent=tid)
            key = "PK" if f["pk"] else ("FK" if f["name"] in fks.get(n, ()) else "")
            col = "#666666" if ghost else "#000000"
            cell = f"shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=13;fontColor={col};html=1;"
            d.vertex(key, 0, 0, KW, ROW, cell + "align=center;fontStyle=1;", parent=rid)
            d.vertex(f["name"], KW, 0, NW, ROW, cell + "align=left;spacingLeft=4;" + ("fontStyle=4;" if f["pk"] else ""), parent=rid)
            d.vertex(f["type"], KW + NW, 0, w - KW - NW, ROW, cell + "align=left;spacingLeft=4;fontColor=#444444;", parent=rid)
    EDGE = "edgeStyle=none;rounded=0;html=1;strokeColor=#000000;endFill=0;startFill=0;endSize=10;startSize=10;"

    def anchor(prefix, n, p):
        x, y, w, h = boxes[n]
        return f"{prefix}X={(p[0] - x) / w:.4f};{prefix}Y={(p[1] - y) / h:.4f};{prefix}Dx=0;{prefix}Dy=0;{prefix}Perimeter=0;"

    for c, col, p, k, (pts, sa, sb) in done:
        st = EDGE + ("startArrow=ERzeroToMany;" if k == M else "startArrow=ERzeroToOne;") + parent_end(c, col)
        if p in ghosts:
            st += "strokeColor=#777777;dashed=1;"
        d.edge(ids[c], ids[p], st + anchor("exit", c, pts[0]) + anchor("entry", p, pts[-1]), points=pts[1:-1])
    bottom = max(b[1] + b[3] for b in boxes.values())
    d.vertex("PK = primary key · FK = reference column. Grey dashed tables belong to another page. Each microservice owns its "
             "schema, so references across services are logical IDs checked by the services, not database foreign keys.",
             X0, bottom + 20, 3 * TW + 2 * HGAP, 40, "text;html=1;align=left;verticalAlign=middle;fontSize=13;fontColor=#555555;whiteSpace=wrap;")
    legend(d, X0, bottom + 66, font=14)
    import os
    print(d.save(OUT if not debug else os.path.dirname(os.path.abspath(__file__)), scale=2.0 if not debug else 0.6))
    return not debug


want = sys.argv[1:] or [p[0] for p in PAGES]
ok = True
for page in PAGES:
    if page[0] in want:
        ok &= build(*page, attempts=int(__import__('os').environ.get('ATTEMPTS', '30')))
sys.exit(0 if ok else 1)
