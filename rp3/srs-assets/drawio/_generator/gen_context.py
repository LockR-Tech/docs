"""Context diagram (DFD level 0). Exported only when no flow line crosses another line or an entity."""
import math
import os
from dio import Diagram
from geom import seg_cross, seg_box, bezier, polylines_cross

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the drawio/ folder
d = Diagram("01-context-diagram")
CX, CY, R = 900, 640, 215
SPAN = 128          # straight left/right flows hit the circle within CY ± SPAN
ENT = "rounded=0;whiteSpace=wrap;html=1;fontSize=14;strokeColor=#000000;fillColor=#FFFFFF;fontColor=#000000;"
STRAIGHT = ("endArrow=classic;endFill=1;html=1;rounded=0;fontSize=12;strokeColor=#000000;fontColor=#000000;"
            "verticalAlign=bottom;labelBackgroundColor=none;spacingBottom=1;")
CURVED = "curved=1;endArrow=classic;endFill=1;html=1;fontSize=12;strokeColor=#000000;fontColor=#000000;labelBackgroundColor=#FFFFFF;"

sys_id = d.vertex("Lock.R - Smart Locker &amp; Drone<br>Delivery System<br>(LockR)", CX - R, CY - R, 2 * R, 2 * R,
                  "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fontSize=19;fontStyle=1;strokeColor=#000000;fillColor=#FFFFFF;")
labels = []     # label rectangles already placed
lines = []      # every drawn line as a polyline, for the crossing check
boxes = []      # (id, (x, y, w, h))


def rel(px, py):
    return (px - (CX - R)) / (2 * R), (py - (CY - R)) / (2 * R)


def side(name, x, flows, left):
    top, height, w = CY - 300, 600, 160
    eid = d.vertex(name, x, top, w, height, ENT + "fontSize=15;")
    boxes.append((eid, (x, top, w, height)))
    n = len(flows)
    for i, (label, inbound) in enumerate(flows):
        y = CY - SPAN + i * (2 * SPAN) / (n - 1)
        dx = math.sqrt(R * R - (y - CY) ** 2)
        px = CX - dx if left else CX + dx
        ex = 1 if left else 0
        ey = (y - top) / height
        rx, ry = rel(px, y)
        ent = (x + w, y) if left else (x, y)
        lines.append((eid, [ent, (px, y)]))
        if inbound:
            st = STRAIGHT + f"exitX={ex};exitY={ey:.4f};exitDx=0;exitDy=0;entryX={rx:.4f};entryY={ry:.4f};entryDx=0;entryDy=0;entryPerimeter=0;"
            d.edge(eid, sys_id, st, label)
        else:
            st = STRAIGHT + f"exitX={rx:.4f};exitY={ry:.4f};exitDx=0;exitDy=0;exitPerimeter=0;entryX={ex};entryY={ey:.4f};entryDx=0;entryDy=0;"
            d.edge(sys_id, eid, st, label)


side("Customer", 40, [
    ("Login Credentials (Email, Google, Phone)", True), ("Account Profile", False),
    ("Locker Search Criteria", True), ("Locker Map &amp; Available Boxes", False),
    ("Send / Rental Order Details", True), ("Drone Delivery Booking", True), ("VietQR Payment Information", False),
    ("Locker Access Code (PIN)", False), ("Order &amp; Drone Tracking Status", False), ("Pickup Delegation &amp; Code Reset", True),
    ("Locker Incident Report", True), ("Refund Request", True), ("Assistant Question", True),
    ("Answer with Citations", False), ("Ratings &amp; Complaints", True),
], left=True)
side("Administrator", 1600, [
    ("Login Credentials &amp; Email OTP", True), ("Dashboard &amp; Revenue Reports", False),
    ("User &amp; Staff Account Data", True), ("Store, Locker &amp; Box Data", True),
    ("Controller &amp; Technician Assignments", True), ("Drone &amp; Device Data", True), ("Orders &amp; Drone Journeys", False),
    ("Refund Decisions", True), ("Drone Incident Decisions", True), ("Promotion &amp; Loyalty Data", True),
    ("Business Settings", True), ("Bluetooth Test Permissions", True), ("Knowledge Base Documents", True),
    ("Cabinet Control Logs", False), ("Feedback &amp; Complaints", False),
], left=False)

# safe arc for curved flows: away from where the straight flows land
LIMIT = math.degrees(math.asin(SPAN / R)) + 9


def ring(entities, y, top):
    flows = []
    for name, x, w, fl in entities:
        eid = d.vertex(name, x, y, w, 64, ENT)
        boxes.append((eid, (x, y, w, 64)))
        for j, f in enumerate(fl):
            flows.append((eid, x, w, len(fl), j, f))
    n = len(flows)
    a0, a1 = (180 + LIMIT, 360 - LIMIT) if top else (180 - LIMIT, LIMIT)
    for k, (eid, x, w, cnt, j, (label, inbound)) in enumerate(flows):
        ang = math.radians(a0 + (a1 - a0) * k / (n - 1))
        px, py = CX + R * math.cos(ang), CY + R * math.sin(ang)
        exr = (j + 1) / (cnt + 1)
        sx, sy = x + w * exr, y + (64 if top else 0)
        dist = math.hypot(px - sx, py - sy)
        best = None
        # control point on the radial line through the landing point: the flow arrives square to the circle
        for f in (0.45, 0.35, 0.55, 0.25, 0.65, 0.15, 0.75, 0.05):
            c = (CX + (R + f * dist) * math.cos(ang), CY + (R + f * dist) * math.sin(ang))
            poly = bezier((sx, sy), c, (px, py))
            clash = any(polylines_cross(poly, other) for _, other in lines)
            clash = clash or any(seg_box(poly[i], poly[i + 1], bx, 1.0)
                                 for i in range(len(poly) - 1) for bid, bx in boxes if bid != eid)
            if not clash:
                best = (c, poly)
                break
        if best is None:
            raise SystemExit(f"cannot place flow '{label}' without a crossing")
        c, poly = best
        lines.append((eid, poly))
        cr = rel(px, py)
        ey = 1 if top else 0
        # label: first spot along the curve (from the entity end) that hits no other label or box
        text = label.replace("&amp;", "&")
        lw, lh = 6.6 * len(text) + 8, 17
        pts_from_entity = poly if True else poly
        chosen = None
        for frac in (0.82, 0.7, 0.58, 0.46, 0.34, 0.25, 0.9, 0.76, 0.64, 0.52, 0.4):
            # poly runs entity -> circle
            q = pts_from_entity[int(round((1 - frac) * (len(poly) - 1)))]
            rect = (q[0] - lw / 2, q[1] - lh / 2, lw, lh)
            if not any(r[0] < rect[0] + rect[2] and rect[0] < r[0] + r[2] and r[1] < rect[1] + rect[3] and rect[1] < r[1] + r[3]
                       for r in labels) and not any(seg_box((rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), bx, 0) for _, bx in boxes):
                chosen = frac
                labels.append(rect)
                break
        if chosen is None:
            raise SystemExit(f"no free spot for label '{label}'")
        # draw.io label x: -1 = source end, +1 = target end
        lx = 1 - 2 * (1 - chosen)
        if inbound:
            st = CURVED + f"exitX={exr:.4f};exitY={ey};exitDx=0;exitDy=0;entryX={cr[0]:.4f};entryY={cr[1]:.4f};entryDx=0;entryDy=0;entryPerimeter=0;"
            d.edge(eid, sys_id, st, label, points=[c], label_x=-lx)  # source = entity
        else:
            st = CURVED + f"exitX={cr[0]:.4f};exitY={cr[1]:.4f};exitDx=0;exitDy=0;exitPerimeter=0;entryX={exr:.4f};entryY={ey};entryDx=0;entryDy=0;"
            d.edge(sys_id, eid, st, label, points=[c], label_x=lx)


ring([
    ("Receiver", 305, 160, [("Pickup Code (at Kiosk)", True), ("Pickup Code Email", False), ("Incoming Order Notifications", False)]),
    ("Locker Technician", 500, 170, [("Ticket Claims &amp; Resolutions", True), ("Inspection Checklists", True),
                                    ("Emergency Open &amp; Restart Commands", True), ("Assigned Tickets &amp; Schedules", False)]),
    ("Drone Technician", 700, 170, [("Order Acceptance &amp; Loading Confirmation", True), ("Launch &amp; Stage Updates", True),
                                   ("Drone Status &amp; Battery Updates", True), ("Dispatch Queue &amp; Missions", False)]),
    ("Firebase<br>(Auth &amp; Cloud Messaging)", 900, 185, [("Firebase ID Token", False), ("Verified Identity", True),
                                                          ("Push Notifications", False)]),
    ("Cloudinary<br>(Image Storage)", 1115, 165, [("Signed Image Upload", False), ("Image URL", True)]),
    ("Weather Service<br>(Open-Meteo)", 1310, 180, [("Station Coordinates", False), ("Weather Forecast", True)]),
], 40, top=True)
ring([
    ("Smart Locker<br>(Raspberry Pi + Kiosk)", 250, 185, [("Box &amp; Lid Commands (MQTT)", False), ("Heartbeats &amp; Door Events", True),
                                                   ("Command Results &amp; Control Logs", True), ("Bluetooth Public Key", False)]),
    ("Drone<br>(Pi + Pixhawk + Camera)", 515, 180, [("Delivery Commands", False), ("Signed Telemetry &amp; Events", True),
                                                   ("Camera Stream", True)]),
    ("Payment Gateway<br>(SePay VietQR)", 760, 170, [("Checkout Request", False), ("Payment Webhook", True)]),
    ("Email Service<br>(Gmail SMTP)", 990, 170, [("OTP &amp; Pickup Code Emails", False)]),
    ("AI Engine<br>(Claude + Voyage AI)", 1215, 170, [("Question &amp; Retrieved Chunks", False), ("Embeddings &amp; Answer", True)]),
    ("Map Services<br>(OpenStreetMap, Nominatim, OSRM)", 1440, 185, [("Addresses &amp; Coordinates", False), ("Map Tiles, Locations &amp; Routes", True)]),
], CY + R + 300, top=False)

# final audit over every pair of lines
bad = sum(1 for i in range(len(lines)) for j in range(i + 1, len(lines)) if polylines_cross(lines[i][1], lines[j][1]))
print("crossings:", bad)
assert bad == 0
print(d.save(OUT, scale=1.95))
