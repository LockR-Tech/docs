"""Screen flows in the reference style: equal rounded boxes (about 2 : 1); a parent's children flow left to right in
rows, each row fed by a bus line from the parent's trunk; double-headed arrows where the user can go back.
Lines only overlap where they share a source; none crosses another or passes through a screen (audited)."""
import os
import sys
from dio import Diagram
from geom import seg_box, polylines_cross

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the drawio/ folder
GREEN = "rounded=1;whiteSpace=wrap;html=1;arcSize=14;fillColor=#D5E8D4;strokeColor=#82B366;fontColor=#000000;fontSize=18;"
BLUE = "rounded=1;whiteSpace=wrap;html=1;arcSize=14;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontColor=#000000;fontSize=18;"
EDGE = "edgeStyle=none;rounded=0;html=1;strokeColor=#82B366;strokeWidth=1.6;endArrow=classic;endFill=1;endSize=8;"
BOTH = "startArrow=classic;startFill=1;startSize=8;"
W, H = 160, 80                 # every screen box (the reference boxes are about 2 : 1)
TRUNK, DX = 16, 32             # trunk offset inside the parent, indent of the children
BUS, ARR, ROWGAP, GX, DOWN = 16, 24, 14, 22, 36
A4 = (16.0, 24.7)              # usable width × height (cm) of a portrait A4 page in the report
# navigation that does not come back to the previous screen (everything else is two-way: back / close)
ONE_WAY = {("Splash Screen", "Login Screen"), ("Login Screen", "Home (Main Navigation)"),
           ("Login Screen", "Technician Home"), ("Login Screen", "Drone Technician Home"),
           ("Admin Login", "2FA Email OTP"), ("2FA Email OTP", "Admin Sidebar Menu"),
           ("Phone OTP (dialog)", "Complete Profile (dialog)"), ("Drone Locker Picker (sheet)", "Drone Booking"),
           ("Drone Booking", "Drone Tracking"), ("Location Services (sheet)", "Send Parcel"),
           ("Location Services (sheet)", "Rent Locker"), ("More Services (sheet)", "Create Report"),
           ("More Services (sheet)", "My Reports"), ("More Services (sheet)", "Favorite Stores"),
           ("Withdraw", "Withdrawal Requests"), ("Technician Profile", "Logout (dialog)")}


def T(name, *kids):
    return (name, list(kids))


class Page:
    def __init__(self):
        self.boxes, self.edges = {}, []


def flow(kids, avail):
    """greedy rows of child blocks that fit in avail; returns [[(kid, (w, h)), ...], ...]"""
    rows, cur, cw = [], [], 0
    for k in kids:
        size = block(k, 0, 0, avail)
        if cur and cw + GX + size[0] > avail:
            rows.append(cur)
            cur, cw = [], 0
        cur.append((k, size))
        cw += (GX if cw else 0) + size[0]
    return rows + [cur]


def place_rows(pg, parent, rows, avail, x0, top, tx):
    """children rows starting at (x0, top); every child hangs from a bus at its row top - ARR; returns (w, bottom)"""
    width, yy = 0, top
    for row in rows:
        bus = yy - ARR
        cx, rh = x0, 0
        for k, (kw, kh) in row:
            if pg is not None:
                block(k, cx, yy, avail, pg)
                pg.edges.append((parent, k[0], ("bus", tx, bus)))
            cx += kw + GX
            rh = max(rh, kh)
        width = max(width, cx - GX - x0)
        yy += rh + ROWGAP + ARR
    return width, yy - ROWGAP - ARR


def block(t, x, y, maxw, pg=None):
    """lay out tree t with its root box at (x, y) inside width maxw; returns (w, h). pg=None only measures."""
    name, kids = t
    if pg is not None:
        assert name not in pg.boxes, name
        pg.boxes[name] = (x, y, W, H)
    if not kids:
        return W, H
    if len(kids) == 1:
        if pg is not None:
            pg.edges.append((name, kids[0][0], ("down",)))
        kw, kh = block(kids[0], x, y + H + DOWN, maxw, pg)
        return max(W, kw), H + DOWN + kh
    avail = max(W, maxw - DX)
    w, bottom = place_rows(pg, name, flow(kids, avail), avail, x + DX, y + H + BUS + ARR, x + TRUNK)
    return max(W, DX + w), bottom - y


def inner_of(slots):
    return slots * W + (slots - 1) * GX + DX            # room for a root's children rows


def header(pg, hub, chain):
    x, y0, bottom = 40, 100, 100 + H
    prev = None
    for t in chain:
        w, h = block(t, x, y0, 10 ** 6, pg)
        bottom = max(bottom, y0 + h)
        if prev:
            pg.edges.append((prev, t[0], ("right",)))
        prev = t[0]
        x += w + 70
    if pg is not None:
        pg.boxes[hub] = (x, y0, W, H)
        if prev:
            pg.edges.append((prev, hub, ("right",)))
    return bottom + BUS + 6, x + W


def plan(blocks, slots_per_col):
    """contiguous split of blocks into len(slots_per_col) columns minimising the tallest column"""
    n, k = len(blocks), len(slots_per_col)
    hs = [[block(t, 0, 0, inner_of(s))[1] + ROWGAP + 8 for t in blocks] for s in slots_per_col]
    memo = {}

    def split(i, c):
        if (i, c) in memo:
            return memo[(i, c)]
        if c == k - 1:
            res = (sum(hs[c][i:]), [n])
        else:
            res = (float("inf"), None)
            for j in range(i + 1, n - (k - 1 - c) + 1):
                tail = split(j, c + 1)
                cand = (max(sum(hs[c][i:j]), tail[0]), [j] + (tail[1] or []))
                if cand[0] < res[0]:
                    res = cand
        memo[(i, c)] = res
        return res

    return [0] + split(0, 0)[1]


def layout(hub, chain, blocks, slots_per_col, cuts=None):
    """header chain → hub; blocks stacked in columns; inside a block children flow in rows. Each column has a trunk
    fed by the hub bus and block roots branch off it."""
    pg = Page()
    y_hub_bus, _ = header(pg, hub, chain)
    cuts = cuts or plan(blocks, slots_per_col)
    cx, top = 40, y_hub_bus + ARR
    for c, slots in enumerate(slots_per_col):
        tx, yy, cw = cx + TRUNK, top, W
        for t in blocks[cuts[c]:cuts[c + 1]]:
            w, h = block(t, cx + DX, yy, inner_of(slots), pg)
            pg.edges.append((hub, t[0], ("col", tx)))
            yy += h + ROWGAP + 8
            cw = max(cw, w)
        cx += DX + cw + 34
    width = max(b[0] + b[2] for b in pg.boxes.values()) + 40
    height = max(b[1] + b[3] for b in pg.boxes.values()) + 40
    return pg, y_hub_bus, width, height


def build(page_id, title, hub, chain, blocks):
    import itertools
    best = None
    for ncols in range(1, min(5, len(blocks)) + 1):       # biggest boxes on a portrait A4 page wins
        for slots in itertools.product(range(1, 7), repeat=ncols):
            _, _, width, height = layout(hub, chain, blocks, list(slots))
            score = W * min(A4[0] / width, A4[1] / height)
            if best is None or score > best[0] + 1e-9:
                best = (score, list(slots))
    pg, y_hub_bus, width, height = layout(hub, chain, blocks, best[1])
    print(f"  {page_id}: columns of {best[1]} boxes, {width:.0f}x{height:.0f} (ratio {width / height:.2f}), "
          f"box on A4 = {best[0]:.2f} cm wide")

    d = Diagram(page_id)
    d.vertex(title, 40, 34, 1200, 40, "text;html=1;align=left;verticalAlign=middle;fontSize=24;fontStyle=1;fontColor=#000000;")
    ids = {n: d.vertex(n, *b, BLUE if n == hub else GREEN) for n, b in pg.boxes.items()}
    polys = []
    for a, b, kind in pg.edges:
        ax, ay, aw, ah = pg.boxes[a]
        bx, by, bw, bh = pg.boxes[b]
        if kind[0] == "down":
            pts = [(ax + aw / 2, ay + ah), (bx + bw / 2, by)]
        elif kind[0] == "right":
            pts = [(ax + aw, ay + ah / 2), (bx, by + bh / 2)]
        elif kind[0] == "col":
            tx = kind[1]
            hx = ax + aw / 2
            pts = [(hx, ay + ah), (hx, y_hub_bus), (tx, y_hub_bus), (tx, by + bh / 2), (bx, by + bh / 2)]
        else:
            _, tx, bus = kind
            pts = [(tx, ay + ah), (tx, bus), (bx + bw / 2, bus), (bx + bw / 2, by)]
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        polys.append((a, b, pts))
        ex = f"exitX={(pts[0][0] - ax) / aw:.4f};exitY={(pts[0][1] - ay) / ah:.4f};exitDx=0;exitDy=0;exitPerimeter=0;"
        en = f"entryX={(pts[-1][0] - bx) / bw:.4f};entryY={(pts[-1][1] - by) / bh:.4f};entryDx=0;entryDy=0;entryPerimeter=0;"
        style = EDGE + ("" if (a, b) in ONE_WAY else BOTH)
        d.edge(ids[a], ids[b], style + ex + en, points=pts[1:-1])
    thru = [(a, b, n) for a, b, pts in polys for n, bx in pg.boxes.items() if n not in (a, b)
            for q in range(len(pts) - 1) if seg_box(pts[q], pts[q + 1], bx, 0)]
    cross = [(p[0], p[1], q[0], q[1]) for i, p in enumerate(polys) for q in polys[i + 1:]
             if p[0] != q[0] and p[1] != q[0] and q[1] != p[0] and polylines_cross(p[2], q[2])]
    print(f"  audit through-screens={len(thru)} crossings={len(cross)}", thru[:3], cross[:3])
    assert not thru and not cross
    print(d.save(OUT, scale=2.0))


AUTH_KIDS = [T("Phone OTP (dialog)", T("Complete Profile (dialog)")), T("Forgot Password"), T("Face Verify Login"),
             T("Terms &amp; Policy")]
HOME_TAB = T("Home (tab)",
             T("QR Scan / Kiosk Login", T("Kiosk Login Confirm (sheet)"), T("Manual Kiosk Code (sheet)")),
             T("Notifications"),
             T("Promotions", T("Promotion Detail")),
             T("More Services (sheet)", T("Create Report"), T("My Reports"), T("Favorite Stores")),
             T("Drone Locker Picker (sheet)",
               T("Drone Booking", T("Pickup Location Picker"),
                 T("Drone Tracking", T("Drone Live Map"), T("Drone Pickup (sheet)"), T("Cancel Drone Order (dialog)")))))
LOCKERS_TAB = T("Lockers (tab)",
                T("Locker Map", T("Locker Detail Map", T("Directions Map"),
                                  T("Location Services (sheet)", T("Send Parcel"),
                                    T("Rent Locker", T("VietQR Payment (sheet)", T("Bank App Picker (sheet)")))))),
                T("Stores List", T("Store Detail",
                                   T("Store Locker Grid", T("Box Booking (sheet)"), T("Kiosk Screen Detail (sheet)")))))
AI_TAB = T("AI Assistant (tab)", T("Assistant History"))
ORDERS_TAB = T("Orders (tab)",
               T("My Order Detail",
                 T("Unlock Locker (sheet)", T("Locker QR Scanner")), T("Delegate Pickup (dialog)"), T("Extend Rental (dialog)"),
                 T("Pay Overtime (sheet)"), T("Reset PIN (dialog)"), T("Report Problem (dialog)")),
               T("Incoming Order Detail"),
               T("Locker Reports", T("Report Detail (sheet)")))
PROFILE_TAB = T("Profile (tab)",
                T("Profile Detail", T("Edit Profile"), T("Security")),
                T("Face Registration"), T("Refund Bank Account"),
                T("Refund Requests", T("Create Refund (sheet)"), T("Refund Detail (sheet)")),
                T("Loyalty"), T("Plans"),
                T("My Vouchers", T("Voucher Detail")),
                T("Transactions", T("Top Up", T("Top Up Payment")), T("Withdraw", T("Withdrawal Requests")),
                  T("Transaction Detail (sheet)")),
                T("My Delegations"), T("Bluetooth Open Test"), T("Location Permission"))

TECH_LOGIN = T("Login Screen", T("Face Verify Login"), T("Forgot Password"))
SHIFT = T("Shift Card (Start / End)", T("Location Permission (sheet)"), T("End Shift Confirm (dialog)"))
PROFILE_TECH = T("Technician Profile", T("Face Registration"), T("Logout (dialog)"))

PAGES = {
    "03a-screen-flow-mobile-customer": dict(
        title="Screen Flow — Mobile App · Customer", hub="Home (Main Navigation)",
        chain=[T("Splash Screen"), T("Login Screen", *AUTH_KIDS)],
        blocks=[HOME_TAB, LOCKERS_TAB, ORDERS_TAB, PROFILE_TAB, AI_TAB]),
    "03b-screen-flow-mobile-locker-technician": dict(
        title="Screen Flow — Mobile App · Locker Technician", hub="Technician Home", chain=[TECH_LOGIN],
        blocks=[SHIFT,
                T("Locker Check (tab)", T("Report Whole Locker (dialog)"), T("Landing Pad Reason (dialog)"),
                  T("Cell Actions (sheet)", T("Report Box Fault (dialog)"), T("Out of Service (dialog)"),
                    T("Emergency Open (dialog)"), T("Mark Fixed / Reopen Box"), T("Clean / Restore Box"))),
                T("Periodic (tab)", T("Schedule Detail (sheet)", T("Inspection Checklist (sheet)"))),
                T("IoT Devices (tab)", T("IoT Device (sheet)", T("Change Device Status (dialog)"), T("Restart Controller"))),
                T("Notifications"),
                T("Incidents (tab)", T("Claim Ticket (dialog)"),
                  T("Ticket Detail (sheet)",
                    T("Box Incident Resolution (sheet)", T("Relocate Parcel"), T("Hand Over to Customer (OTP)"),
                      T("Seal to Hub"), T("Quick Fix"), T("Lock Only")),
                    T("Resolve Verification (sheet)"), T("Reject Ticket (dialog)"), T("Return Ticket (dialog)"),
                    T("Extend SLA (sheet)"), T("Report Logs &amp; Photos"))),
                T("My Tasks (tab)", T("My Ticket Detail (sheet)")),
                T("Parcel Recovery (tab)",
                  T("Recovery Detail (sheet)", T("Accept Recovery Mission"), T("Record Search Result"),
                    T("Confirm Hub Handover"), T("GPS Fallback (dialog)"))),
                T("AI Assistant"), PROFILE_TECH]),
    "03c-screen-flow-mobile-drone-technician": dict(
        title="Screen Flow — Mobile App · Drone Technician", hub="Drone Technician Home", chain=[TECH_LOGIN],
        blocks=[SHIFT,
                T("Dispatch (tab)",
                  T("Home Pickup Queue", T("Accept / Reject Pickup"), T("Confirm Picked Up (dialog)"),
                    T("Pickup Failed (dialog)"), T("Assign Drone")),
                  T("Drone Order Card", T("Accept Order (dialog)"), T("Loading Confirmation (dialog)"), T("Launch Mission"),
                    T("Advance Stage (dialog)"), T("Change Drone (dialog)"), T("Report Failed Flight (dialog)"),
                    T("Cancel Before Flight (dialog)"), T("Confirm Parcel Returned (dialog)")),
                  T("Drone Order Detail (sheet)", T("Journey Camera Panel", T("Report Parcel Drop (dialog)")))),
                T("AI Assistant"), PROFILE_TECH,
                T("Fleet (tab)",
                  T("Drone Actions (sheet)", T("Claim / Release Drone"), T("Change Drone Status (dialog)"),
                    T("Update Battery (dialog)"), T("Maintenance Log (sheet)"))),
                T("Incidents (tab)",
                  T("Drone Report Detail (sheet)", T("Claim (dialog)"), T("Resolve (sheet)"), T("Extend SLA (dialog)"),
                    T("Return Ticket (dialog)"), T("Orders by Ticket")),
                  T("Parcel Incident (sheet)", T("Recovery Detail"))),
                T("My Tasks (tab)", T("My Report Detail (sheet)"), T("My Drone Order (sheet)")),
                T("Periodic (tab)", T("Schedule Detail (sheet)", T("Drone Inspection Checklist (sheet)"))),
                T("Flight Tools (tab)", T("Mission Planner", T("Waypoint Edit (sheet)")), T("Flight Data"))]),
    "03d-screen-flow-admin-web": dict(
        title="Screen Flow — Admin Web", hub="Admin Sidebar Menu", chain=[T("Admin Login"), T("2FA Email OTP")],
        blocks=[T("Dashboard"),
                T("Users", T("Create User / Staff (modal)"), T("Wallet Adjust (modal)"), T("User Detail")),
                T("Stores", T("Store Create / Edit (modal)"),
                  T("Store Detail", T("Add Locker (modal)"), T("Box Settings (modal)"), T("Locker Settings (modal)"))),
                T("Lockers",
                  T("Locker Layout", T("Cell Actions (dialog)"), T("Edit Box (modal)"), T("Box QR (modal)"),
                    T("Kiosk Screen (modal)"), T("Locker Location (modal)"), T("Assign Controller (dialog)"),
                    T("Bluetooth Test Panel"), T("Add Box Preview"), T("Locker Logs Panel")),
                  T("Open Box by QR")),
                T("Cabinet Control"), T("Services"),
                T("Maintenance", T("Assign Report (dialog)"), T("Resolve Report (dialog)"), T("Repair Log (dialog)"),
                  T("Schedules (create / edit / inspect)")),
                T("Technicians", T("Technician Detail", T("Extend SLA (dialog)"), T("Edit Phone (dialog)"))),
                T("Drones", T("Add Drone (dialog)"),
                  T("Drone Detail", T("Rename / Battery / Decommission"), T("Drone IoT Logs Panel"))),
                T("Drone Orders", T("Report Drop (dialog)"), T("Drone Order Detail")),
                T("Drone Incidents", T("Incident Detail (dialog)"), T("Compensation Proposal (dialog)"),
                  T("Recovery Dispatch Map (modal)"), T("Drone Incident Detail")),
                T("Drone Logs"),
                T("Orders", T("Order Status Update (modal)"), T("Order Detail")),
                T("Payments", T("Payment Detail (modal)"), T("Approve / Reject Withdrawal (dialog)")),
                T("Refunds", T("Refund Detail (dialog)"), T("Approve Refund (dialog)"), T("Reject Refund (dialog)")),
                T("Revenue", T("Revenue Orders (modal)"), T("Revenue Detail")),
                T("Loyalty"),
                T("Promotions", T("Promotion Create / Edit (modal)")),
                T("Feedback", T("Resolve Report"), T("Feedback Detail")),
                T("Scheduler", T("Confirm Run (dialog)"), T("Job Info (dialog)")),
                T("Notifications", T("Create Notification (modal)"), T("Broadcast (modal)")),
                T("Knowledge Base", T("Upload / Edit Document (dialog)"), T("Document Detail (sheet)"),
                  T("Conversation Detail (sheet)"), T("Eval Cases (add / import)")),
                T("Business Settings", T("Save Changes (dialog)"), T("Audit History (sheet)"))]),
}

for pid in sys.argv[1:] or list(PAGES):
    build(pid, **PAGES[pid])
