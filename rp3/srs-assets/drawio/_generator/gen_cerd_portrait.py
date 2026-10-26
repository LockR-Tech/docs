"""Conceptual ERD (A4 landscape): entity names + crow's-foot relationships; no line crosses, touches or
runs alongside another line, and no line passes through an entity (audited before export)."""
import random
import sys
from dio import Diagram
from erd_data import REL, M, OUT
from maze import Maze
from geom import polylines_cross, seg_box
from erd_legend import parent_end, legend

# name: (col, row, col_span, row_span) on a 10 × 10 grid — hubs are big so their neighbours connect straight
LAYOUT = {
    "RefreshToken": (0, 0, 1, 1),
    "SocialIdentity": (1, 0, 1, 1),
    "AssistantMessage": (2, 0, 1, 1),
    "UserBankAccount": (3, 0, 1, 1),
    "WithdrawalRecord": (4, 0, 1, 1),
    "EvalCase": (5, 0, 1, 1),
    "AuthAccount": (0, 1, 1, 1),
    "NotificationMessage": (1, 1, 1, 1),
    "AssistantConversation": (2, 1, 1, 1),
    "FcmToken": (3, 1, 1, 1),
    "TechnicianPresence": (4, 1, 1, 1),
    "DroneTechnicianPresence": (5, 1, 1, 1),
    "UserProfile": (0, 2, 6, 1),
    "LockerOrder": (1, 3, 1, 10),
    "LockerUnit": (5, 3, 1, 10),
    "LockerBox": (1, 13, 5, 1),
    "PromotionClaim": (0, 3, 1, 1),
    "Promotion": (0, 4, 1, 1),
    "PromotionUsage": (0, 5, 1, 1),
    "OrderStatusHistory": (0, 6, 1, 1),
    "OrderDetail": (0, 7, 1, 1),
    "PaymentRecord": (0, 8, 1, 1),
    "RefundRecord": (0, 9, 1, 1),
    "LockerReport": (0, 10, 1, 1),
    "RepairLog": (0, 11, 1, 1),
    "ReportAttachment": (0, 12, 1, 1),
    "LockerReportRating": (0, 13, 1, 1),
    "LoyaltyAccount": (2, 3, 1, 1),
    "Wallet": (3, 3, 1, 1),
    "BleTestGrant": (4, 3, 1, 1),
    "PointTransaction": (2, 4, 1, 1),
    "WalletTransaction": (3, 4, 1, 1),
    "GatewayDevice": (4, 4, 1, 1),
    "DronePickup": (2, 5, 1, 1),
    "DronePickupOffer": (3, 5, 1, 1),
    "DeviceStatus": (4, 5, 1, 1),
    "OrderRating": (2, 6, 1, 1),
    "EmailOtp": (3, 6, 1, 1),
    "CabinetControlLog": (4, 6, 1, 1),
    "OrderComplaint": (2, 7, 1, 1),
    "MaintenanceInspectionLog": (3, 7, 1, 1),
    "StoreLocation": (4, 7, 1, 1),
    "DroneMission": (2, 8, 1, 1),
    "MaintenanceSchedule": (4, 8, 1, 1),
    "DroneParcelIncident": (2, 9, 1, 1),
    "DroneDeliverySession": (3, 9, 1, 1),
    "DroneUnit": (4, 9, 1, 1),
    "DroneIncidentEvidence": (2, 10, 1, 1),
    "DroneLockerCommLog": (3, 10, 1, 1),
    "DroneDevice": (4, 10, 1, 1),
    "DroneIncidentTimeline": (2, 11, 1, 1),
    "DroneMaintenanceLog": (3, 11, 1, 1),
    "DroneIotLog": (4, 11, 1, 1),
    "DroneIncidentResolutionProposal": (2, 12, 1, 1),
    "DroneDeliveryRequest": (3, 12, 1, 1),
    "BleSigningKey": (0, 14, 1, 1),
    "BoxHardwareStatus": (1, 14, 1, 1),
    "AccessAttempt": (2, 14, 1, 1),
    "BoxAccessLog": (3, 14, 1, 1),
    "KbDocument": (4, 14, 1, 1),
    "KbChunk": (5, 14, 1, 1),
}
# derivable relationships left out of the conceptual view (all of them stay in the logical ERD)
SKIP = {("LockerOrder", "LockerUnit"), ("LockerOrder", "StoreLocation"), ("LockerReport", "LockerUnit"),
        ("PaymentRecord", "UserProfile"), ("BoxAccessLog", "LockerOrder"), ("DroneDeliverySession", "LockerOrder"),
        ("Promotion", "LockerUnit"), ("LockerReport", "MaintenanceSchedule")}

CW, RH, BW, BH = 222, 126, 184, 52
X0, Y0 = 40, 40
boxes = {}
for name, (c, r, sc, sr) in LAYOUT.items():
    w = BW if sc == 1 else sc * CW - (CW - BW)
    h = BH if sr == 1 else sr * RH - (RH - BH)
    cx = X0 + c * CW + sc * CW / 2
    cy = Y0 + r * RH + sr * RH / 2
    boxes[name] = (cx - w / 2, cy - h / 2, w, h)

pairs, seen, fkcol = [], set(), {}
for child, col, parent, kind in REL:
    if (child, parent) in seen or (child, parent) in SKIP:
        continue
    seen.add((child, parent))
    fkcol[(child, parent)] = col
    pairs.append((child, parent, kind))
assert set(LAYOUT) >= {n for p in pairs for n in p[:2]}


def dist(t):
    a, b = boxes[t[0]], boxes[t[1]]
    return abs((a[0] + a[2] / 2) - (b[0] + b[2] / 2)) + abs((a[1] + a[3] / 2) - (b[1] + b[3] / 2))


def attempt(order):
    mz = Maze(boxes, cell=6, margin=8, stub_cells=4, spacing=1, bend=8)
    done, bad = [], []
    for child, parent, kind in order:
        res = mz.route(child, parent)
        if res is None:
            bad.append((child, parent, kind))
        else:
            done.append((child, parent, kind, res))
    return done, bad


pairs.sort(key=dist)
order, best, priority = list(pairs), None, []
rng = random.Random(3)
for it in range(int(sys.argv[1]) if len(sys.argv) > 1 else 12):
    routes, failed = attempt(order)
    print(f"attempt {it}: {len(failed)} failed {[(c, p) for c, p, _ in failed]}", flush=True)
    if best is None or len(failed) < len(best[1]):
        best = (routes, failed)
    if not failed:
        break
    for f in failed:
        if f not in priority:
            priority.append(f)
    near_pairs = [p for p in pairs if dist(p) <= 1.05 * max(CW, RH) * 1.6]
    far = [p for p in pairs if p not in near_pairs]
    # failed ones first (random order), the rest by distance with a little noise
    pri = [p for p in priority if p in far]
    rng.shuffle(pri)
    rest = sorted([p for p in far if p not in pri], key=lambda t: dist(t) * (0.7 + 0.6 * rng.random()))
    k = rng.randint(0, len(pri))
    order = near_pairs + pri[:k] + rest + pri[k:]
routes, failed = best
DEBUG = bool(failed)
if failed:
    print("DEBUG render without:", [(c, p) for c, p, _ in failed])

polys = [(c, p, r[0]) for c, p, _, r in routes]
bad = [(a[0], a[1], b[0], b[1]) for k, a in enumerate(polys) for b in polys[k + 1:] if polylines_cross(a[2], b[2])]
thru = [(c, p, n) for c, p, pts in polys for n, bx in boxes.items() if n not in (c, p)
        for q in range(len(pts) - 1) if seg_box(pts[q], pts[q + 1], bx, 0)]
print("audit — crossings:", len(bad), "through entities:", len(thru))
assert not bad and not thru

d = Diagram("04-conceptual-erd" if not DEBUG else "_debug-cerd-portrait")
def font(n, w):
    return 16 if len(n) * 8.9 <= w - 8 else max(10, int((w - 8) / (len(n) * 0.56)))


ids = {n: d.vertex(n, *bx, f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize={font(n, bx[2])};")
       for n, bx in boxes.items()}
EDGE = "edgeStyle=none;rounded=0;html=1;strokeColor=#000000;endFill=0;startFill=0;endSize=10;startSize=10;"


def anchor(prefix, name, p):
    x, y, w, h = boxes[name]
    return f"{prefix}X={(p[0] - x) / w:.4f};{prefix}Y={(p[1] - y) / h:.4f};{prefix}Dx=0;{prefix}Dy=0;{prefix}Perimeter=0;"


for child, parent, kind, (pts, sa, sb) in routes:
    st = EDGE + ("startArrow=ERzeroToMany;" if kind == M else "startArrow=ERzeroToOne;") + parent_end(child, fkcol[(child, parent)])
    d.edge(ids[child], ids[parent], st + anchor("exit", child, pts[0]) + anchor("entry", parent, pts[-1]), points=pts[1:-1])
print(len(routes), "relationships")
legend(d, X0, max(b[1] + b[3] for b in boxes.values()) + 30, font=16)
import os
print(d.save(OUT if not DEBUG else os.path.dirname(os.path.abspath(__file__)), scale=2.0 if not DEBUG else 0.8))
