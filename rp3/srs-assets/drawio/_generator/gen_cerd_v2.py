"""Conceptual ERD v2 (04b): no Wallet / WalletTransaction / WithdrawalRecord, admin price settings (SystemSetting),
1 : 1 / 1 : N checked against the JPA entities + Flyway migrations, N : N shown through their associative entity.
Layout is hand-placed so almost every line is one straight segment; the rest are orthogonal. Audited before export:
no crossing, no line through an entity, bend count printed per line."""
import os
import sys
from dio import Diagram
from maze import Maze, mark_line
from geom import polylines_cross, seg_box

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "04b-conceptual-erd-v2"

# name: (col, row, col_span, row_span)
LAYOUT = {
    # above UserProfile
    "RefreshToken": (0, 0, 1, 1), "SocialIdentity": (1, 0, 1, 1), "EmailOtp": (2, 0, 1, 1),
    "AssistantMessage": (4, 0, 1, 1), "KbChunk": (5, 0, 1, 1), "SystemSettingAudit": (6, 0, 1, 1),
    "EvalCase": (7, 0, 1, 1), "BleSigningKey": (8, 0, 1, 1),
    "AuthAccount": (0, 1, 2, 1), "NotificationMessage": (2, 1, 1, 1), "FcmToken": (3, 1, 1, 1),
    "AssistantConversation": (4, 1, 1, 1), "KbDocument": (5, 1, 1, 1), "SystemSetting": (6, 1, 1, 1),
    "UserBankAccount": (7, 1, 1, 1), "TechnicianPresence": (8, 1, 1, 1),
    "UserProfile": (0, 2, 9, 1),
    # hubs
    "LockerOrder": (1, 3, 1, 12),
    "LockerUnit": (7, 3, 1, 10),
    "LockerBox": (2, 13, 6, 1),
    # left of LockerOrder
    "PromotionClaim": (0, 3, 1, 1), "Promotion": (0, 4, 1, 1), "PromotionUsage": (0, 5, 1, 1),
    "OrderStatusHistory": (0, 6, 1, 1), "OrderDetail": (0, 7, 1, 1), "OrderRating": (0, 8, 1, 1),
    "OrderComplaint": (0, 9, 1, 1), "PaymentRecord": (0, 10, 1, 1), "RefundRecord": (0, 11, 1, 1),
    "DroneFlightBlock": (0, 12, 1, 1),
    # right of LockerOrder
    "LoyaltyAccount": (2, 3, 1, 1), "PointTransaction": (2, 4, 1, 1),
    "DronePickup": (2, 5, 1, 1), "DronePickupOffer": (3, 5, 1, 1),
    "DroneMission": (2, 6, 1, 5),
    "DroneFlightTrackPoint": (3, 6, 1, 1),
    "DroneDeliverySession": (3, 7, 1, 1), "DroneLockerCommLog": (4, 7, 1, 1),
    "DroneParcelIncident": (3, 8, 2, 1), "DroneIncidentResolutionProposal": (5, 8, 1, 1),
    "DroneIncidentEvidence": (3, 9, 1, 1), "DroneIncidentTimeline": (4, 9, 1, 1),
    "DroneUnit": (3, 10, 4, 1),
    "DroneDeliveryRequest": (3, 11, 1, 2), "DroneDevice": (4, 11, 1, 1), "DroneIotLog": (5, 11, 1, 1),
    "DroneMaintenanceLog": (6, 11, 1, 1),
    "BoxAccessLog": (2, 12, 1, 1), "BoxHardwareStatus": (4, 12, 1, 1), "AccessAttempt": (5, 12, 1, 1),
    # left of LockerUnit
    "BleTestGrant": (6, 3, 1, 1), "GatewayDevice": (6, 4, 1, 1), "CabinetHardwareConfig": (6, 5, 1, 1),
    "DeviceStatus": (6, 6, 1, 1), "CabinetControlLog": (6, 7, 1, 1),
    "MaintenanceInspectionLog": (6, 8, 1, 1), "MaintenanceSchedule": (6, 9, 1, 1),
    # right of LockerUnit
    "DroneTechnicianPresence": (8, 3, 1, 1), "StoreLocation": (8, 4, 1, 1),
    "DroneStationSuspension": (8, 5, 1, 1), "DroneStationSuspensionLog": (8, 6, 1, 1),
    # below LockerBox
    "LockerReport": (2, 14, 4, 1), "LockerReportRating": (5, 15, 1, 1),
    "RepairLog": (3, 15, 1, 1), "ReportAttachment": (4, 15, 1, 1),
}
# associative entities that resolve an N : N
ASSOC = {"LockerOrder", "PromotionClaim", "PromotionUsage", "BleTestGrant", "DronePickupOffer"}

M, O = "many", "one"   # child-side cardinality: 1 : N or 1 : 1
# (child, parent, child side, FK NOT NULL?, label, fk column(s) — from the entities / migrations)
REL = [
    ("AuthAccount", "UserProfile", O, True, "", "user_id UNIQUE"),
    ("RefreshToken", "AuthAccount", M, True, "", "account_id"),
    ("SocialIdentity", "AuthAccount", M, True, "", "account_id"),
    ("NotificationMessage", "UserProfile", M, True, "", "user_id"),
    ("FcmToken", "UserProfile", M, True, "", "user_id"),
    ("AssistantConversation", "UserProfile", M, True, "", "user_id"),
    ("AssistantMessage", "AssistantConversation", M, True, "", "conversation_id"),
    ("KbDocument", "UserProfile", M, False, "", "created_by"),
    ("KbChunk", "KbDocument", M, True, "", "document_id"),
    ("SystemSetting", "UserProfile", M, False, "admin sets", "updated_by_user_id"),
    ("SystemSettingAudit", "SystemSetting", M, True, "", "setting_key"),
    ("UserBankAccount", "UserProfile", O, True, "", "user_id UNIQUE"),
    ("TechnicianPresence", "UserProfile", O, True, "", "user_id PK"),
    ("DroneTechnicianPresence", "UserProfile", O, True, "", "user_id PK"),
    ("LoyaltyAccount", "UserProfile", O, True, "", "user_id UNIQUE"),
    ("PointTransaction", "LoyaltyAccount", M, True, "", "user_id"),
    ("PointTransaction", "LockerOrder", M, False, "", "order_id"),
    # N : N  UserProfile — LockerBox through LockerOrder (a box is booked by many users at different times,
    # a user books many boxes)
    ("LockerOrder", "UserProfile", M, True, "places", "user_id"),
    ("LockerOrder", "UserProfile", M, False, "receives", "receiver_user_id"),
    ("LockerOrder", "LockerBox", M, False, "", "reserved_box_id / send_box_id / receive_box_id"),
    # N : N  UserProfile — Promotion through PromotionClaim, Promotion — LockerOrder through PromotionUsage
    ("PromotionClaim", "UserProfile", M, True, "", "user_id"),
    ("PromotionClaim", "Promotion", M, True, "", "promotion_id"),
    ("PromotionUsage", "Promotion", M, True, "", "promotion_id"),
    ("PromotionUsage", "LockerOrder", M, False, "", "order_id"),
    ("OrderStatusHistory", "LockerOrder", M, True, "", "order_id"),
    ("OrderDetail", "LockerOrder", M, True, "", "order_id"),
    ("OrderRating", "LockerOrder", O, True, "", "order_id UNIQUE"),
    ("OrderComplaint", "LockerOrder", M, True, "", "order_id"),
    ("PaymentRecord", "LockerOrder", M, True, "", "order_id"),
    ("RefundRecord", "PaymentRecord", M, True, "", "payment_id"),
    ("DroneFlightBlock", "LockerOrder", M, False, "", "order_id"),
    # locker
    ("LockerUnit", "StoreLocation", M, False, "", "store_id"),
    ("LockerUnit", "UserProfile", M, False, "manages", "assigned_technician_id"),
    ("LockerBox", "LockerUnit", M, True, "", "locker_id"),
    ("BleTestGrant", "UserProfile", M, True, "", "user_id"),          # N : N technician — locker
    ("BleTestGrant", "LockerUnit", M, True, "", "locker_id"),
    ("GatewayDevice", "LockerUnit", O, False, "", "locker_id UNIQUE"),
    ("CabinetHardwareConfig", "LockerUnit", O, True, "", "locker_id PK"),
    ("DeviceStatus", "LockerUnit", M, False, "", "locker_id"),
    ("CabinetControlLog", "LockerUnit", M, True, "", "locker_id"),
    ("DroneStationSuspension", "LockerUnit", O, True, "", "locker_id PK"),
    ("DroneStationSuspensionLog", "LockerUnit", M, True, "", "locker_id"),
    ("MaintenanceSchedule", "LockerUnit", M, False, "", "locker_id"),
    ("MaintenanceSchedule", "DroneUnit", M, False, "", "drone_unit_id"),
    ("MaintenanceInspectionLog", "MaintenanceSchedule", M, True, "", "schedule_id"),
    ("BoxHardwareStatus", "LockerBox", O, True, "", "box_id PK"),
    ("AccessAttempt", "LockerBox", M, True, "", "box_id"),
    ("BoxAccessLog", "LockerBox", M, True, "", "box_id"),
    ("BoxAccessLog", "LockerOrder", M, False, "", "order_id"),
    ("LockerReport", "LockerBox", M, False, "", "box_id"),
    ("LockerReport", "LockerOrder", M, False, "", "order_id"),
    ("LockerReport", "UserProfile", M, True, "reports", "user_id"),
    ("RepairLog", "LockerReport", M, True, "", "report_id"),
    ("ReportAttachment", "LockerReport", M, True, "", "report_id"),
    ("LockerReportRating", "LockerReport", O, True, "", "report_id UNIQUE"),
    # drone
    ("DroneUnit", "LockerUnit", M, True, "", "locker_id"),
    ("DroneDevice", "DroneUnit", O, False, "", "drone_id UNIQUE"),
    ("DroneIotLog", "DroneUnit", M, True, "", "drone_id"),
    ("DroneMaintenanceLog", "DroneUnit", M, True, "", "drone_unit_id"),
    ("DroneDeliveryRequest", "DroneUnit", M, False, "", "drone_unit_id"),
    ("DroneDeliveryRequest", "LockerBox", M, False, "", "box_id"),
    ("DroneMission", "LockerOrder", O, True, "", "order_id UNIQUE"),
    ("DroneMission", "DroneUnit", M, False, "", "drone_unit_id"),
    ("DronePickup", "LockerOrder", O, True, "", "order_id UNIQUE"),
    ("DronePickupOffer", "DronePickup", M, True, "", "pickup_id"),
    ("DronePickupOffer", "UserProfile", M, True, "", "technician_id"),  # N : N drone technician — pickup
    ("DroneFlightTrackPoint", "DroneMission", M, False, "", "mission_id"),
    ("DroneDeliverySession", "DroneMission", M, True, "", "mission_id"),
    ("DroneLockerCommLog", "DroneDeliverySession", M, False, "", "session_id"),
    ("DroneParcelIncident", "DroneMission", O, True, "", "mission_id UNIQUE"),
    ("DroneIncidentEvidence", "DroneParcelIncident", M, True, "", "incident_id"),
    ("DroneIncidentTimeline", "DroneParcelIncident", M, True, "", "incident_id"),
    ("DroneIncidentResolutionProposal", "DroneParcelIncident", M, True, "", "incident_id"),
]
assert not {"Wallet", "WalletTransaction", "WithdrawalRecord"} & (set(LAYOUT) | {n for r in REL for n in r[:2]})
assert set(LAYOUT) >= {n for r in REL for n in r[:2]}, {n for r in REL for n in r[:2]} - set(LAYOUT)

CW, RH, BW, BH = 262, 126, 184, 52
X0, Y0 = 40, 40
boxes = {}
for name, (c, r, sc, sr) in LAYOUT.items():
    w = BW if sc == 1 else sc * CW - (CW - BW)
    h = BH if sr == 1 else sr * RH - (RH - BH)
    boxes[name] = (X0 + c * CW + sc * CW / 2 - w / 2, Y0 + r * RH + sr * RH / 2 - h / 2, w, h)
for a, ba in boxes.items():
    for b, bb in boxes.items():
        if a < b:
            assert not (ba[0] < bb[0] + bb[2] and bb[0] < ba[0] + ba[2] and ba[1] < bb[1] + bb[3] and bb[1] < ba[1] + ba[3]), (a, b)


def straight_ports(a, b):
    """if a and b face each other with an overlap wider than one port, the straight segment between them"""
    ax, ay, aw, ah = boxes[a]
    bx, by, bw, bh = boxes[b]
    lo, hi = max(ax, bx) + 14, min(ax + aw, bx + bw) - 14
    if hi > lo:
        if ay + ah <= by:
            return "B", "T", (lo + hi) / 2
        if by + bh <= ay:
            return "T", "B", (lo + hi) / 2
    lo, hi = max(ay, by) + 10, min(ay + ah, by + bh) - 10
    if hi > lo:
        if ax + aw <= bx:
            return "R", "L", (lo + hi) / 2
        if bx + bw <= ax:
            return "L", "R", (lo + hi) / 2
    return None


def gap_between(a, b):
    ax, ay, aw, ah = boxes[a]
    bx, by, bw, bh = boxes[b]
    return max(bx - (ax + aw), ax - (bx + bw), by - (ay + ah), ay - (by + bh))


# long lines: leave from the free bottom-left of LockerReport, run up the left margin into UserProfile's left side
SIDES = {("LockerReport", "UserProfile"): ("B", "L")}


def attempt(order, bend):
    """facing pairs: one straight segment drawn directly; the rest: orthogonal maze route around them"""
    mz = Maze(boxes, cell=6, margin=8, stub_cells=2, spacing=1, bend=bend)
    done, bad, later = [], [], []
    dup = {}
    for rel in order:
        dup.setdefault(rel[:2], []).append(rel)
    for rel in order:
        child, parent = rel[0], rel[1]
        sp = straight_ports(child, parent)
        if not sp:
            later.append(rel)
            continue
        sa, sb, _ = sp
        ax, ay, aw, ah = boxes[child]
        bx, by, bw, bh = boxes[parent]
        same = dup[rel[:2]]
        k, n = same.index(rel), len(same)
        if sa in "TB":
            lo, hi = max(ax, bx) + 14, min(ax + aw, bx + bw) - 14
            x = lo + (hi - lo) * (k + 1) / (n + 1)
            pts = [(x, ay + ah), (x, by)] if sa == "B" else [(x, ay), (x, by + bh)]
        else:
            lo, hi = max(ay, by) + 10, min(ay + ah, by + bh) - 10
            y = lo + (hi - lo) * (k + 1) / (n + 1)
            pts = [(ax + aw, y), (bx, y)] if sa == "R" else [(ax, y), (bx + bw, y)]
        if any(seg_box(pts[0], pts[1], bb, 0) for nm, bb in boxes.items() if nm not in (child, parent)) or                 any(polylines_cross(pts, r[1][0]) for r in done):
            later.append(rel)
            continue
        mark_line(mz, pts)
        for nm, side, p in ((child, sa, pts[0]), (parent, sb, pts[1])):
            mz.used_ports.setdefault((nm, side), []).append(mz._ci(p[0]) if side in "TB" else mz._cj(p[1]))
        done.append((rel, (pts, sa, sb)))
    for rel in later:
        sa, sb = SIDES.get(rel[:2], ("LRTB", "LRTB"))
        res = mz.route(rel[0], rel[1], sides_a=sa, sides_b=sb, max_pops=4_000_000, max_ports=400)
        if res is None:
            bad.append(rel)
        else:
            done.append((rel, res))
    return done, bad


# straight neighbours first (shortest gap), then the long lines
order = sorted(REL, key=lambda r: (straight_ports(r[0], r[1]) is None, gap_between(r[0], r[1])))
routes, failed = attempt(order, bend=60)
print("failed:", [(r[0], r[1]) for r in failed])
assert not failed

polys = [(rel, res[0]) for rel, res in routes]
cross = [(a[0][:2], b[0][:2]) for k, a in enumerate(polys) for b in polys[k + 1:] if polylines_cross(a[1], b[1])]
thru = [(rel[:2], n) for rel, pts in polys for n, bx in boxes.items() if n not in rel[:2]
        for q in range(len(pts) - 1) if seg_box(pts[q], pts[q + 1], bx, 0)]
diag = [rel[:2] for rel, pts in polys for p, q in zip(pts, pts[1:]) if abs(p[0] - q[0]) > 0.01 and abs(p[1] - q[1]) > 0.01]
print("audit — crossings:", cross, "through entities:", thru, "diagonal segments:", diag)
assert not cross and not thru and not diag
bends = sorted(((len(pts) - 2, rel[0], rel[1]) for rel, pts in polys), reverse=True)
print(f"{sum(1 for b in bends if b[0] == 0)}/{len(bends)} straight;", "bent:", [b for b in bends if b[0]])

d = Diagram(NAME)


def font(n, w):
    return 16 if len(n) * 8.9 <= w - 8 else max(10, int((w - 8) / (len(n) * 0.56)))


ids = {}
for n, bx in boxes.items():
    fill = "#FFF2CC" if n in ASSOC else ("#DAE8FC" if n == "SystemSetting" or n == "SystemSettingAudit" else "#FFFFFF")
    ids[n] = d.vertex(n, *bx, f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#000000;"
                              f"fontColor=#000000;fontSize={font(n, bx[2])};")
EDGE = ("edgeStyle=none;rounded=0;html=1;strokeColor=#000000;endFill=0;startFill=0;endSize=10;startSize=10;"
        "fontSize=10;fontColor=#333333;labelBackgroundColor=#FFFFFF;")


def anchor(prefix, name, p):
    x, y, w, h = boxes[name]
    return f"{prefix}X={(p[0] - x) / w:.4f};{prefix}Y={(p[1] - y) / h:.4f};{prefix}Dx=0;{prefix}Dy=0;{prefix}Perimeter=0;"


for (child, parent, kind, notnull, label, col), (pts, sa, sb) in routes:
    st = (EDGE + ("startArrow=ERzeroToMany;" if kind == M else "startArrow=ERzeroToOne;")
          + ("endArrow=ERmandOne;" if notnull else "endArrow=ERzeroToOne;"))
    d.edge(ids[child], ids[parent], st + anchor("exit", child, pts[0]) + anchor("entry", parent, pts[-1]),
           label=label, points=pts[1:-1])
print(len(routes), "relationships,", len(boxes), "entities")

# legend + N : N note under the diagram
ly = max(b[1] + b[3] for b in boxes.values()) + 40
lx = X0 + 4 * CW + 20
dot = "text;html=1;strokeColor=none;fillColor=none;"
items = [("ERmandOne", "exactly one (parent side, FK NOT NULL)"),
         ("ERzeroToOne", "zero or one (parent side when the FK is nullable · child side of a 1 : 1)"),
         ("ERzeroToMany", "zero or many (child side of a 1 : N)")]
for i, (arrow, text) in enumerate(items):
    yy = ly + i * 30 + 15
    a = d.vertex("", lx, yy - 1, 2, 2, dot)
    b = d.vertex("", lx + 70, yy - 1, 2, 2, dot)
    d.edge(a, b, "edgeStyle=none;html=1;strokeColor=#000000;startArrow=none;endFill=0;endSize=12;"
                 f"endArrow={arrow};exitX=0.5;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0.5;entryDx=0;entryDy=0;")
    d.vertex(text, lx + 84, yy - 15, 640, 30, "text;html=1;align=left;verticalAlign=middle;fontSize=14;fontColor=#333333;")
yy = ly + 3 * 30 + 10
d.vertex("", lx, yy + 5, 40, 20, "rounded=0;html=1;fillColor=#FFF2CC;strokeColor=#000000;")
d.vertex("associative entity resolving an N : N relationship", lx + 84, yy, 640, 30,
         "text;html=1;align=left;verticalAlign=middle;fontSize=14;fontColor=#333333;")
yy += 32
d.vertex("", lx, yy + 5, 40, 20, "rounded=0;html=1;fillColor=#DAE8FC;strokeColor=#000000;")
d.vertex("admin-configurable settings: unit prices (send base fee, rental hourly / daily rate standard · XL, "
         "drone delivery fee, overtime fee per hour, weight-step fee …) and business rules", lx + 84, yy, 760, 44,
         "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontSize=14;fontColor=#333333;")
nn = ("<b>N : N relationships</b><br>"
      "• UserProfile N : N LockerBox — through <b>LockerOrder</b> (a box is booked by many users at different times; "
      "a user books many boxes)<br>"
      "• UserProfile N : N Promotion — through <b>PromotionClaim</b> (UNIQUE promotion_id, user_id)<br>"
      "• Promotion N : N LockerOrder — through <b>PromotionUsage</b><br>"
      "• UserProfile (locker technician) N : N LockerUnit — through <b>BleTestGrant</b> (UNIQUE locker_id, user_id)<br>"
      "• UserProfile (drone technician) N : N DronePickup — through <b>DronePickupOffer</b>")
d.vertex(nn, X0, ly, 4 * CW - 30, 150,
         "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=14;fontColor=#000000;"
         "strokeColor=#999999;fillColor=#FAFAFA;spacing=10;")
print(d.save(OUT, scale=2.0))
