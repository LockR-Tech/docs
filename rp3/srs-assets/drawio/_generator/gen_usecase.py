"""Use case diagram, A4 portrait, in the style of the reference: grey system boundary, actors on both sides,
blue use cases; child use cases hang off their parent (generalization or «include»/«extend»).
Exported only when no line crosses another line or passes through a use case."""
import math
import os
from dio import Diagram
from geom import seg_cross, seg_ellipse

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the drawio/ folder
d = Diagram("02-use-case-diagram")

G, I, E = "gen", "include", "extend"
LEFT = [
    ("guest", "Sign Up", [("Verify Phone OTP", I), ("Complete Registration", I)]),
    ("guest", "Search Lockers &amp; Stores", [("View Locker Map", G), ("Get Directions", E), ("View Store Detail", G)]),
    ("reg", "Sign In", [("Sign In with Password", G), ("Sign In with Phone OTP", G), ("Sign In with Google", G)]),
    ("reg", "View Notifications", [("Mark as Read", E), ("View Notification Detail", E)]),
    ("reg", "Manage Profile", [("Update Profile", G), ("Register Face ID", G), ("Change Password", G)]),
    ("reg", "Ask AI Assistant", [("View Answer Citations", I), ("View Conversation History", E)]),
    ("cus", "Send Parcel via Locker", [("Choose Locker &amp; Box", I), ("Apply Voucher", E), ("Share Pickup Code", E)]),
    ("cus", "Make Payment", [("Pay by VietQR (SePay)", G), ("Redeem Loyalty Points", E), ("Pay by Wallet", G)]),
    ("cus", "Rent Locker by Hours", [("Extend Rental", E), ("Pay Overdue Fee", E), ("End Rental", E)]),
    ("cus", "Book Drone Delivery", [("Book Home Pickup", E), ("Track Drone Delivery", E), ("Cancel Drone Order", E)]),
    ("cus", "Manage My Orders", [("Delegate Pickup", E), ("Request Refund", E), ("Rate Order", E)]),
    ("cus", "Manage Wallet", [("Top Up Wallet", G), ("View Transactions", G), ("Withdraw to Bank", G)]),
    ("cus", "Report Locker Incident", [("Attach Photos", I), ("View My Reports", E)]),
    ("cus", "Manage Vouchers", [("Claim Voucher", G), ("Redeem Points for Voucher", G)]),
    ("cus", "Log in to Kiosk by QR", [("Scan Kiosk QR Code", I)]),
    ("cus", "Test Open Box via Bluetooth", [("Request Open Token", I), ("Connect to Locker via BLE", I)]),
    ("rec", "Pick Up Parcel", [("Enter PIN at Kiosk", G), ("View Incoming Orders", E), ("Scan QR at Kiosk", G)]),
]
RIGHT = [
    ("adm", "Manage Accounts", [("Create Staff Account", G), ("Assign Roles", G), ("Lock / Unlock Account", G)]),
    ("adm", "Manage Lockers &amp; Boxes", [("Assign Controller (Pi)", G), ("Grant Bluetooth Test", G), ("Assign Technician", G)]),
    ("adm", "Manage Drones", [("Register Drone Device", G), ("View Drone Logs", G)]),
    ("adm", "Monitor Orders &amp; Journeys", [("View Order Detail", G), ("Handle Parcel Incidents", G)]),
    ("adm", "Process Refunds &amp; Withdrawals", [("Approve Request", G), ("Upload Transfer Receipt", I), ("Reject Request", G)]),
    ("adm", "Manage Maintenance", [("Assign Ticket", G), ("Create Inspection Schedule", G)]),
    ("adm", "Manage Promotions &amp; Loyalty", [("Create Promotion", G), ("Set Voucher Point Price", G)]),
    ("adm", "View Dashboard &amp; Reports", [("View Revenue Report", G), ("View Order Statistics", G)]),
    ("adm", "Configure System", [("Update Business Settings", G), ("Manage Knowledge Base", G), ("Send Notifications", G)]),
    ("lt", "Manage Shift", [("Start Shift", G), ("End Shift", G)]),
    ("lt", "Handle Incident Ticket", [("Claim Ticket", I), ("Extend SLA", E), ("Resolve Ticket", I)]),
    ("lt", "Perform Periodic Inspection", [("Fill Checklist", I), ("Create Ticket from Inspection", E)]),
    ("lt", "Manage IoT Devices", [("Emergency Open Box", E), ("Control Sliding Lid", E), ("Restart Controller", E)]),
    ("lt", "Recover Dropped Parcel", [("View Recovery Queue", I), ("Return Parcel to Hub", I)]),
    ("dt", "Process Drone Order", [("Accept Drone Order", I), ("Launch Drone", I), ("Confirm Loading", I)]),
    ("dt", "Manage Drone Fleet", [("Update Drone Status", G), ("Plan Mission", G), ("View Flight Data", G)]),
    ("dt", "Report Parcel Drop", [("Attach Camera Evidence", I), ("Report Failed Flight", E)]),
    ("pi", "Execute Cabinet Command", [("Open Box Relay", I), ("Verify Bluetooth Token", E), ("Send Heartbeat", E)]),
    ("sch", "Run Scheduled Jobs", [("Expire Unpaid Orders", I), ("Escalate Overdue Tickets", I), ("Charge Overdue Fees", I)]),
]
ACTORS = {"guest": "Guest", "reg": "Registered User", "cus": "Customer", "rec": "Receiver",
          "adm": "Administrator", "lt": "Locker Technician", "dt": "Drone Technician",
          "pi": "Locker Controller (Pi)", "sch": "System Scheduler"}
INCLUDES = [("Send Parcel via Locker", "Make Payment"), ("Rent Locker by Hours", "Make Payment")]

BX0, BX1, BY0, BY1 = 200, 1520, 70, 2392
MW, MH = 198, 58                       # main use case
CWD, CHT = 160, 40                     # child use case
LMX, RMX = 332, 1388                   # main column centres
ACT_W, ACT_H = 36, 76
LAX, RAX = 104, 1616                   # actor centres

UC = "ellipse;whiteSpace=wrap;html=1;fillColor=#6FA8DC;strokeColor=#1F4E79;fontColor=#000000;"
d.vertex("Lock.R - Smart Locker &amp; Drone Delivery System", BX0, BY0, BX1 - BX0, BY1 - BY0,
         "rounded=0;whiteSpace=wrap;html=1;fillColor=#F2F2F2;strokeColor=#666666;verticalAlign=top;fontStyle=1;fontSize=17;fontColor=#000000;")

ell = {}            # label -> (id, cx, cy, rx, ry)
lines = []          # (owner labels, polyline) for the audit


def uc(label, cx, cy, w, h, size):
    vid = d.vertex(label, cx - w / 2, cy - h / 2, w, h, UC + f"fontSize={size};")
    ell[label] = (vid, cx, cy, w / 2, h / 2)
    return vid


def clip(e, q):
    """point where the line from the ellipse centre toward q leaves the ellipse."""
    _, cx, cy, rx, ry = e
    dx, dy = q[0] - cx, q[1] - cy
    t = 1 / math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
    return cx + dx * t, cy + dy * t


EDGE_GEN = "endArrow=block;endFill=0;endSize=11;html=1;strokeColor=#000000;rounded=0;"
EDGE_DEP = ("endArrow=open;endSize=8;dashed=1;html=1;strokeColor=#000000;fontSize=10;fontColor=#000000;"
            "labelBackgroundColor=#F2F2F2;rounded=0;")


def place(items, side):
    n = len(items)
    band = (BY1 - BY0 - 70) / n
    mains = []
    for k, (actor, main, kids) in enumerate(items):
        cy = BY0 + 60 + band * (k + 0.5)
        mx = LMX if side == "L" else RMX
        uc(main, mx, cy, MW, MH, 13)
        mains.append((actor, main, cy))
        sgn = 1 if side == "L" else -1
        if len(kids) == 1:
            spots = [(250, 0)]
        elif len(kids) == 2:
            spots = [(250, -30), (250, 30)]
        else:
            spots = [(235, -37), (410, 0), (235, 37)]
        for (lab, kind), (dx, dy) in zip(kids, spots):
            uc(lab, mx + sgn * dx, cy + dy, CWD, CHT, 11)
            a, b = ell[lab], ell[main]
            if kind == G:
                d.edge(a[0], b[0], EDGE_GEN)
            elif kind == I:
                d.edge(b[0], a[0], EDGE_DEP, "&lt;&lt;include&gt;&gt;")
            else:
                d.edge(a[0], b[0], EDGE_DEP, "&lt;&lt;extend&gt;&gt;")
            lines.append(({lab, main}, [clip(a, (b[1], b[2])), clip(b, (a[1], a[2]))]))
    return mains


left_mains = place(LEFT, "L")
right_mains = place(RIGHT, "R")
for a, b in INCLUDES:
    ea, eb = ell[a], ell[b]
    d.edge(ea[0], eb[0], EDGE_DEP, "&lt;&lt;include&gt;&gt;")
    lines.append(({a, b}, [clip(ea, (eb[1], eb[2])), clip(eb, (ea[1], ea[2]))]))

# actors in the middle of their block; each association leaves the actor at its own height and runs in its
# own lane (farther use case = outer exit + lane nearer the actor), so the fan never crosses itself
ASSOC = "endArrow=none;html=1;strokeColor=#000000;rounded=0;edgeStyle=none;"
ACTOR = ("shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#FFFFFF;"
         "strokeColor=#000000;fontColor=#000000;fontSize=13;")
actor_pos = {}


def actors(mains, side):
    by_actor = {}
    for actor, main, cy in mains:
        by_actor.setdefault(actor, []).append((main, cy))
    for actor, lst in by_actor.items():
        ay = sum(cy for _, cy in lst) / len(lst)
        ax = LAX if side == "L" else RAX
        aid = d.vertex(ACTORS[actor], ax - ACT_W / 2, ay - ACT_H / 2, ACT_W, ACT_H, ACTOR)
        d._grow(ax - 80, ay - ACT_H / 2, 160, ACT_H + 40)
        actor_pos[actor] = (aid, ax, ay)
        edge_x = ax + ACT_W / 2 if side == "L" else ax - ACT_W / 2
        main_edge = (LMX - MW / 2) if side == "L" else (RMX + MW / 2)
        ups = sorted([m for m in lst if m[1] < ay - 1], key=lambda m: m[1])           # farthest first
        downs = sorted([m for m in lst if m[1] > ay + 1], key=lambda m: -m[1])        # farthest first
        level = [m for m in lst if abs(m[1] - ay) <= 1]
        span = (ACT_H - 14) / 2
        sgn_x = 1 if side == "L" else -1
        for group, sgn in ((ups, -1), (downs, 1)):
            for k, (main, cy) in enumerate(group):
                ey = ay + sgn * (span - k * span / max(1, len(group)))
                lane = edge_x + sgn_x * (14 + k * (abs(main_edge - edge_x) - 34) / max(1, len(group)))
                pts = [(lane, ey), (lane, cy)]
                st = ASSOC + (f"exitX={1 if side == 'L' else 0};exitY={(ey - (ay - ACT_H / 2)) / ACT_H:.4f};exitDx=0;exitDy=0;"
                              f"entryX={0 if side == 'L' else 1};entryY=0.5;entryDx=0;entryDy=0;")
                d.edge(aid, ell[main][0], st, points=pts)
                lines.append(({main}, [(edge_x, ey), (lane, ey), (lane, cy), (main_edge, cy)]))
        for main, cy in level:
            st = ASSOC + (f"exitX={1 if side == 'L' else 0};exitY=0.5;exitDx=0;exitDy=0;"
                          f"entryX={0 if side == 'L' else 1};entryY=0.5;entryDx=0;entryDy=0;")
            d.edge(aid, ell[main][0], st)
            lines.append(({main}, [(edge_x, ay), (main_edge, cy)]))


actors(left_mains, "L")
actors(right_mains, "R")

# actor generalizations, routed outside the system boundary (nested so they never cross)
GEN = "endArrow=block;endFill=0;endSize=12;html=1;strokeColor=#000000;rounded=0;edgeStyle=none;"


def a_xy(a):
    return actor_pos[a][1], actor_pos[a][2]


def gen(child, parent, pts, exit_, entry):
    d.edge(actor_pos[child][0], actor_pos[parent][0], GEN + exit_ + entry, points=pts)
    for p in pts:
        d._grow(p[0] - 4, p[1] - 4, 8, 8)


gx, gy = a_xy("guest")
rx_, ry_ = a_xy("reg")
cx_, cy_ = a_xy("cus")
gen("reg", "guest", [(44, ry_ - 20), (44, gy)], "exitX=0;exitY=0.24;exitDx=0;exitDy=0;", "entryX=0;entryY=0.5;entryDx=0;entryDy=0;")
gen("cus", "reg", [(44, cy_), (44, ry_ + 30)], "exitX=0;exitY=0.5;exitDx=0;exitDy=0;", "entryX=0;entryY=0.9;entryDx=0;entryDy=0;")
for k, a in enumerate(["adm", "lt", "dt"]):
    ax, ay = a_xy(a)
    xr = RAX + ACT_W / 2 + 26 + 13 * k
    yt = BY0 - 22 - 12 * k
    xl = 30 - 9 * k
    ye = ry_ - 6 + 9 * k
    gen(a, "reg", [(xr, ay), (xr, yt), (xl, yt), (xl, ye)], "exitX=1;exitY=0.5;exitDx=0;exitDy=0;",
        f"entryX=0;entryY={(ye - (ry_ - ACT_H / 2)) / ACT_H:.4f};entryDx=0;entryDy=0;")

# ── audit ──
bad = 0
for i in range(len(lines)):
    for j in range(i + 1, len(lines)):
        a, b = lines[i][1], lines[j][1]
        if any(seg_cross(a[p], a[p + 1], b[q], b[q + 1]) for p in range(len(a) - 1) for q in range(len(b) - 1)):
            bad += 1
            print("cross:", lines[i][0], lines[j][0])
thru = 0
for owners, pts in lines:
    for lab, (_, cx, cy, rx, ry) in ell.items():
        if lab in owners:
            continue
        if any(seg_ellipse(pts[p], pts[p + 1], cx, cy, rx, ry) for p in range(len(pts) - 1)):
            thru += 1
            print("through:", owners, lab)
overlap = 0
vals = list(ell.values())
for i in range(len(vals)):
    for j in range(i + 1, len(vals)):
        a, b = vals[i], vals[j]
        if abs(a[1] - b[1]) < a[3] + b[3] and abs(a[2] - b[2]) < a[4] + b[4]:
            if any(((a[1] + a[3] * math.cos(t) - b[1]) / b[3]) ** 2 + ((a[2] + a[4] * math.sin(t) - b[2]) / b[4]) ** 2 < 1
                   for t in (k * math.pi / 36 for k in range(72))):
                overlap += 1
                print("overlap:", a[0], b[0])
print(f"audit — crossings: {bad}, lines through use cases: {thru}, overlapping use cases: {overlap}")
assert bad == 0 and thru == 0 and overlap == 0
print(d.save(OUT, scale=1.45))
