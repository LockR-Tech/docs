"""UML activity diagrams with swimlanes (one partition per actor, every backend service, the locker and the drone
grouped as "System"). Flow runs top to bottom; every edge is an orthogonal polyline with explicit ports so draw.io
never re-routes it. Exported only when no edge crosses another edge or passes through a node.

Notation (UML 2.5): ● initial node · ◉ activity final · rounded rectangle = action · ◇ decision / merge with
[guard] on each outgoing edge · black bar = fork / join · open arrowhead = control flow.

Terms follow the app/backend: drop-off PIN, pickup PIN, box, VietQR bank transfer, order states in CAPS.
"""
import os
import sys
from dio import Diagram
from geom import seg_box, seg_cross, too_close_parallel

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the drawio/ folder

ACTION = "rounded=1;arcSize=24;whiteSpace=wrap;html=1;spacingLeft=6;spacingRight=6;fillColor=#DAE8FC;strokeColor=#1F4E79;fontColor=#000000;fontSize=12;"
DIAMOND = "rhombus;html=1;fillColor=#FFF2CC;strokeColor=#7F6000;"
START = "ellipse;html=1;shape=startState;fillColor=#000000;strokeColor=#000000;"
FINAL = "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;"
BAR = "rounded=0;html=1;fillColor=#000000;strokeColor=#000000;"
LANE = ("swimlane;html=1;startSize=34;horizontal=1;fillColor=#6FA8DC;swimlaneFillColor=#FFFFFF;strokeColor=#1F4E79;"
        "fontStyle=1;fontSize=14;fontColor=#000000;collapsible=0;")
FRAME = ("shape=umlFrame;whiteSpace=wrap;html=1;width={w};height=28;boundedLbl=1;verticalAlign=middle;align=left;"
         "spacingLeft=6;fontSize=13;fontStyle=1;strokeColor=#333333;fillColor=none;")
EDGE = "edgeStyle=none;html=1;rounded=0;endArrow=open;endSize=9;strokeWidth=1.2;strokeColor=#000000;"
GUARD = "text;html=1;fontSize=11;fontColor=#000000;spacing=0;verticalAlign=middle;whiteSpace=wrap;"

RH = 76            # row height
AW, AH = 208, 50   # action box
DS = 30            # decision diamond
SIDE = {"t": (0.5, 0), "b": (0.5, 1), "l": (0, 0.5), "r": (1, 0.5)}


class Node:
    def __init__(self, key, kind, x, y, w, h):
        self.key, self.kind, self.x, self.y, self.w, self.h = key, kind, x, y, w, h
        self.cx, self.cy = x + w / 2, y + h / 2
        self.vid = None

    def port(self, side, at=None):
        if at is not None:                                   # a point along the top/bottom edge of a bar
            return (at, self.y if side == "t" else self.y + self.h)
        fx, fy = SIDE[side]
        return (self.x + fx * self.w, self.y + fy * self.h)

    def box(self):
        return (self.x, self.y, self.w, self.h)


class Activity:
    def __init__(self, name, title, lanes, top=80):
        """lanes: [(label, width)]"""
        self.d = Diagram(name)
        self.title = title
        self.lanes, x = [], 30
        for label, w in lanes:
            self.lanes.append((label, x, w))
            x += w
        self.top = top          # y of row 0 centre
        self.nodes, self.edges, self.guards = {}, [], []
        self.max_row = 0

    # ---- placement ------------------------------------------------------------------------------------------
    def X(self, lane, f=0.5):
        _, x, w = self.lanes[lane]
        return x + f * w

    def Y(self, row):
        return self.top + row * RH

    def _add(self, key, kind, lane, row, f, w, h):
        cx, cy = self.X(lane, f), self.Y(row)
        n = Node(key, kind, cx - w / 2, cy - h / 2, w, h)
        assert key not in self.nodes, key
        self.nodes[key] = n
        self.max_row = max(self.max_row, row)
        return n

    def start(self, key, lane, row, f=0.5):
        self._add(key, "start", lane, row, f, 28, 28)

    def final(self, key, lane, row, f=0.5):
        self._add(key, "final", lane, row, f, 30, 30)

    def action(self, key, lane, row, label, f=0.5, h=AH, w=AW):
        self._add(key, "action", lane, row, f, w, h).label = label

    def decision(self, key, lane, row, f=0.5):
        self._add(key, "decision", lane, row, f, DS, DS)

    merge = decision

    def bar(self, key, lane_from, f_from, lane_to, f_to, row):
        x0, x1 = self.X(lane_from, f_from) - 30, self.X(lane_to, f_to) + 30
        n = Node(key, "bar", x0, self.Y(row) - 4, x1 - x0, 8)
        self.nodes[key] = n
        self.max_row = max(self.max_row, row)

    # ---- edges ----------------------------------------------------------------------------------------------
    def flow(self, a, b, guard="", out=None, inn=None, via=(), at_out=None, at_in=None, gpos=None):
        """Orthogonal control flow a -> b. Default ports: straight down, or out of the side facing b then down.
        via: extra absolute bend points (for loops). gpos: (dx, dy) guard offset from the exit point."""
        A, B = self.nodes[a], self.nodes[b]
        if out is None:
            out = "b" if abs(A.cx - B.cx) < 1 or "bar" in (A.kind, B.kind) else ("r" if B.cx > A.cx else "l")
        if inn is None:
            inn = "t" if B.cy > A.cy + 1 else ("l" if B.cx > A.cx else "r")
        p0 = A.port(out, at_out)
        p1 = B.port(inn, at_in)
        pts = list(via)
        if not pts:
            if out in "tb" and inn in "tb":
                if abs(p0[0] - p1[0]) > 0.5:
                    ym = (p0[1] + p1[1]) / 2
                    pts = [(p0[0], ym), (p1[0], ym)]
            elif out in "lr" and inn in "tb":
                pts = [(p1[0], p0[1])]
            elif out in "tb" and inn in "lr":
                pts = [(p0[0], p1[1])]
            else:
                if abs(p0[1] - p1[1]) > 0.5:
                    xm = (p0[0] + p1[0]) / 2
                    pts = [(xm, p0[1]), (xm, p1[1])]
        self.edges.append((a, b, out, inn, p0, p1, pts, at_out, at_in))
        if guard:
            nxt = (pts or [p1])[0]
            room = abs(nxt[0] - p0[0]) - 8 if out in "lr" else 250
            self.guards.append((guard, out, p0, gpos, room))

    # ---- output ---------------------------------------------------------------------------------------------
    def audit(self):
        problems = []
        lines = []
        for a, b, out, inn, p0, p1, pts, *_ in self.edges:
            poly = [p0, *pts, p1]
            for i in range(len(poly) - 1):
                (x0, y0), (x1, y1) = poly[i], poly[i + 1]
                if abs(x0 - x1) > 0.5 and abs(y0 - y1) > 0.5:
                    problems.append(f"diagonal segment {a}->{b}: {poly[i]} {poly[i + 1]}")
            # the first segment must leave the source through the side it claims
            (sx, sy), (nx, ny) = poly[0], poly[1]
            if not {"t": ny < sy, "b": ny > sy, "l": nx < sx, "r": nx > sx}[out]:
                problems.append(f"arrow {a}->{b} leaves '{out}' in the wrong direction")
            # the last segment must enter the target through the side it claims
            (lx, ly), (ex, ey) = poly[-2], poly[-1]
            want = {"t": ey > ly, "b": ey < ly, "l": ex > lx, "r": ex < lx}[inn]
            if not want:
                problems.append(f"arrow {a}->{b} enters '{inn}' from the wrong direction")
            lines.append(((a, b), poly))
            for k, n in self.nodes.items():
                if k in (a, b):
                    continue
                for i in range(len(poly) - 1):
                    if seg_box(poly[i], poly[i + 1], n.box(), margin=-4):
                        problems.append(f"edge {a}->{b} passes through {k}")
                        break
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                (ka, pa), (kb, pb) = lines[i], lines[j]
                for s in range(len(pa) - 1):
                    for t in range(len(pb) - 1):
                        if seg_cross(pa[s], pa[s + 1], pb[t], pb[t + 1]):
                            problems.append(f"edges {ka} and {kb} cross")
                        elif set(ka) & set(kb) == set() and too_close_parallel(pa[s], pa[s + 1], pb[t], pb[t + 1], 6):
                            problems.append(f"edges {ka} and {kb} overlap")
        return problems

    def build(self):
        d = self.d
        bottom = self.Y(self.max_row) + 50
        lane_top = self.top - 62
        x0 = self.lanes[0][1]
        x1 = self.lanes[-1][1] + self.lanes[-1][2]
        d.vertex(f"act {self.title}", x0 - 14, lane_top - 42, x1 - x0 + 28, bottom - lane_top + 56,
                 FRAME.format(w=max(200, 9 * len(self.title) + 50)))
        for label, x, w in self.lanes:
            d.vertex(label, x, lane_top, w, bottom - lane_top, LANE)
        for n in self.nodes.values():
            style = {"start": START, "final": FINAL, "action": ACTION, "decision": DIAMOND, "bar": BAR}[n.kind]
            n.vid = d.vertex(getattr(n, "label", ""), n.x, n.y, n.w, n.h, style)
        for a, b, out, inn, p0, p1, pts, at_out, at_in in self.edges:
            A, B = self.nodes[a], self.nodes[b]
            ex, ey = ((at_out - A.x) / A.w, SIDE[out][1]) if at_out is not None else SIDE[out]
            nx, ny = ((at_in - B.x) / B.w, SIDE[inn][1]) if at_in is not None else SIDE[inn]
            style = EDGE + f"exitX={ex:.4f};exitY={ey};exitDx=0;exitDy=0;entryX={nx:.4f};entryY={ny};entryDx=0;entryDy=0;"
            d.edge(A.vid, B.vid, style, points=pts)
        for text, out, (px, py), gpos, room in self.guards:
            need = 6.3 * len(text) + 6
            w = min(need, 250) if gpos else min(need, max(room, 60))
            lines = -(-need // w)
            h = 15 * lines + 2
            if gpos:
                gx, gy = px + gpos[0], py + gpos[1]
            elif out == "b":
                gx, gy = px + 6, py + 2
            elif out == "r":
                gx, gy = px + 4, py - h - 2
            elif out == "l":
                gx, gy = px - 4 - w, py - h - 2
            else:
                gx, gy = px + 6, py - h - 2
            align = "align=right;" if (out == "l" and not gpos) else "align=left;"
            d.vertex(text, gx, gy, w, h, GUARD + align)

    def save(self):
        problems = self.audit()
        if problems:
            print(f"[{self.d.name}] NOT exported:")
            for p in problems:
                print("   ", p)
            return False
        self.build()
        path, png = self.d.save(OUT, scale=1.6, margin=24)
        print("wrote", png)
        return True


# =============================================================================================================
# 1. Send Parcel via Locker  (Sender | System | Receiver)
# =============================================================================================================
def send_parcel():
    a = Activity("06a-activity-send-parcel", "Send Parcel via Locker",
                 [("Sender", 470), ("System", 500), ("Receiver", 290)])
    S, Y, R = 0, 1, 2
    m, s = 0.32, 0.78                       # System main / side column
    a.start("st", S, 0)
    a.action("choose", S, 1, "Choose locker &amp; box size")
    a.action("receiver", S, 2, "Enter receiver phone, name &amp; email, then create order")
    a.action("reserve", Y, 3, "Reserve box (RESERVED) &amp; create order (INITIALIZED, UNPAID)", f=m)
    a.action("qr", Y, 4, "Generate VietQR payment code", f=m)
    a.action("pay", S, 5, "Pay by VietQR bank transfer (scan QR or open banking app)")
    a.action("verify", Y, 6, "Verify bank transfer", f=m)
    a.decision("dpay", Y, 7, f=m)
    a.action("cancel", Y, 7, "Cancel order &amp; release box", f=s)
    a.final("end_cancel", Y, 8, f=s)
    a.action("paid", Y, 8, "Mark order PAID &amp; issue drop-off PIN", f=m)
    a.decision("dopen", S, 9)
    a.action("open_app", S, 10, "Tap &quot;Open box to drop off&quot; in app", f=0.25, w=190)
    a.action("open_kiosk", S, 10, "Enter drop-off PIN at kiosk", f=0.75, w=190)
    a.merge("mopen", S, 11)
    a.action("open1", Y, 12, "Send open command to locker &amp; open box", f=m)
    a.action("put", S, 13, "Put parcel in box &amp; close door")
    a.action("confirm", S, 14, "Confirm drop-off (in app or at kiosk)")
    a.action("stored", Y, 15, "Mark box OCCUPIED, order STORING &amp; issue pickup PIN", f=m)
    a.action("notify", Y, 16, "Send pickup PIN to receiver (in-app, email, SMS)", f=m)
    a.merge("mpin", R, 17)
    a.action("enter", R, 18, "Enter pickup PIN at kiosk", w=200)
    a.action("check", Y, 19, "Validate pickup PIN", f=m)
    a.decision("dpin", Y, 20, f=m)
    a.action("wrong", Y, 20, "Show error &amp; count failed attempt (box locked after too many)", f=s, h=58)
    a.action("open2", Y, 21, "Open box", f=m)
    a.action("take", R, 22, "Take parcel &amp; close door", w=200)
    a.action("done", Y, 23, "Complete order (COMPLETED), release box &amp; add loyalty points to sender", f=m, h=58)
    a.final("end", Y, 24, f=m)

    a.flow("st", "choose"); a.flow("choose", "receiver"); a.flow("receiver", "reserve")
    a.flow("reserve", "qr"); a.flow("qr", "pay"); a.flow("pay", "verify"); a.flow("verify", "dpay")
    a.flow("dpay", "cancel", "[not paid within hold time]", out="r", inn="l")
    a.flow("cancel", "end_cancel")
    a.flow("dpay", "paid", "[payment confirmed]")
    a.flow("paid", "dopen")
    a.flow("dopen", "open_app", "[in app]", out="l", inn="t")
    a.flow("dopen", "open_kiosk", "[at kiosk]", out="r", inn="t")
    a.flow("open_app", "mopen", out="b", inn="l")
    a.flow("open_kiosk", "mopen", out="b", inn="r")
    a.flow("mopen", "open1", out="b", inn="t")
    a.flow("open1", "put"); a.flow("put", "confirm"); a.flow("confirm", "stored")
    a.flow("stored", "notify"); a.flow("notify", "mpin"); a.flow("mpin", "enter")
    a.flow("enter", "check"); a.flow("check", "dpin")
    a.flow("dpin", "wrong", "[invalid PIN]", out="r", inn="l")
    xr = a.X(R) + 128
    a.flow("wrong", "mpin", out="r", inn="r", via=[(xr, a.Y(20)), (xr, a.Y(17))])
    a.flow("dpin", "open2", "[valid PIN]")
    a.flow("open2", "take"); a.flow("take", "done"); a.flow("done", "end")
    return a


# =============================================================================================================
# 2. Rent Locker by Hours  (Customer | System)
# =============================================================================================================
def rent_locker():
    a = Activity("06b-activity-rent-locker", "Rent Locker by Hours", [("Customer", 480), ("System", 640)])
    C, Y = 0, 1
    l, m, s = 0.17, 0.5, 0.83
    a.start("st", C, 0)
    a.action("choose", C, 1, "Choose locker, box type &amp; rental hours")
    a.action("reserve", Y, 2, "Reserve box &amp; create rental order (UNPAID)", f=m)
    a.action("qr", Y, 3, "Generate VietQR payment code", f=m)
    a.action("pay", C, 4, "Pay by VietQR bank transfer")
    a.action("verify", Y, 5, "Verify bank transfer", f=m)
    a.decision("dpay", Y, 6, f=m)
    a.action("cancel", Y, 6, "Cancel order &amp; release box", f=s)
    a.final("end_cancel", Y, 7, f=s)
    a.action("paid", Y, 7, "Mark order PAID &amp; issue rental PIN", f=m)
    a.action("open_first", C, 8, "Tap &quot;Open box&quot; in app or enter PIN at kiosk")
    a.action("open1", Y, 9, "Open box", f=m)
    a.action("put", C, 10, "Put items in box, close door &amp; start rental")
    a.action("storing", Y, 11, "Start rental period (order STORING)", f=m)
    a.merge("muse", C, 12)
    a.action("use", C, 13, "Open box again: enter PIN at kiosk or tap &quot;Open box&quot;")
    a.decision("dvalid", Y, 14, f=m)
    a.action("reject", Y, 14, "Reject PIN (RENTAL_EXPIRED)", f=l, w=180)
    a.action("extend", C, 14, "Extend rental &amp; pay via VietQR", f=0.78, w=190)
    a.action("extended", Y, 15, "Verify payment &amp; extend rental end time", f=l, w=180)
    a.merge("mopen", Y, 15, f=m)
    a.action("open2", Y, 16, "Open box", f=m)
    a.action("access", C, 17, "Take or add items &amp; close door")
    a.decision("dmore", C, 18)
    a.action("finish", C, 19, "End rental &amp; take all items (in app or at kiosk)")
    a.action("done", Y, 20, "Complete order (COMPLETED), release box &amp; add loyalty points", f=m, h=58)
    a.final("end", Y, 21, f=m)

    a.flow("st", "choose"); a.flow("choose", "reserve"); a.flow("reserve", "qr"); a.flow("qr", "pay")
    a.flow("pay", "verify"); a.flow("verify", "dpay")
    a.flow("dpay", "cancel", "[not paid within hold time]", out="r", inn="l")
    a.flow("cancel", "end_cancel")
    a.flow("dpay", "paid", "[payment confirmed]")
    a.flow("paid", "open_first"); a.flow("open_first", "open1"); a.flow("open1", "put")
    a.flow("put", "storing"); a.flow("storing", "muse"); a.flow("muse", "use"); a.flow("use", "dvalid")
    a.flow("dvalid", "reject", "[rental expired]", out="l", inn="r")
    a.flow("reject", "extend", out="l", inn="r")
    a.flow("extend", "extended", out="b", inn="l", via=[(a.X(C, 0.78), a.Y(15))])
    a.flow("extended", "mopen", out="r", inn="l")
    a.flow("dvalid", "mopen", "[within rental period]")
    a.flow("mopen", "open2"); a.flow("open2", "access"); a.flow("access", "dmore")
    xl = a.X(C, 0) + 26
    a.flow("dmore", "muse", "[continue rental]", out="l", inn="l",
           via=[(xl, a.Y(18)), (xl, a.Y(12))], gpos=(-150, -20))
    a.flow("dmore", "finish", "[end rental]")
    a.flow("finish", "done"); a.flow("done", "end")
    return a


# =============================================================================================================
# 3. Drone Delivery  (Sender | System | Drone Technician | Receiver)
# =============================================================================================================
def drone_delivery():
    a = Activity("06c-activity-drone-delivery", "Book Drone Delivery",
                 [("Sender", 460), ("System", 660), ("Drone Technician", 420), ("Receiver", 290)])
    S, Y, T, R = 0, 1, 2, 3
    l, m, r = 0.17, 0.5, 0.83
    sl, sr = 0.25, 0.75
    t = 0.4
    a.start("st", S, 0)
    a.action("choose", S, 1, "Choose receiving locker, parcel details &amp; receiver")
    a.action("create", S, 2, "Confirm no prohibited items &amp; create order")
    a.action("reserve", Y, 3, "Check route (landing pad, free drone box, max range), reserve drone box &amp; create order",
             f=m, w=210, h=58)
    a.action("qr", Y, 4, "Generate VietQR payment code", f=m)
    a.action("pay", S, 5, "Pay by VietQR bank transfer")
    a.action("verify", Y, 6, "Verify bank transfer", f=m)
    a.decision("dpay", Y, 7, f=m)
    a.action("cancel", Y, 7, "Cancel order &amp; release box", f=r, w=180)
    a.final("end_cancel", Y, 8, f=r)
    a.action("paid", Y, 8, "Mark order PAID (AWAITING_DISPATCH)", f=m)
    a.action("place", S, 9, "Put parcel in drone box at sending locker &amp; tap &quot;I've placed the parcel&quot;", h=58)
    a.action("queue", Y, 10, "Show order in dispatch queue", f=m)
    a.action("accept", T, 11, "Accept order &amp; choose an idle drone at sending locker", f=t, w=200)
    a.action("mission", Y, 12, "Create delivery mission", f=m)
    a.action("load", T, 13, "Weigh parcel, complete checklist &amp; confirm loading", f=t, w=200)
    a.action("weigh", Y, 14, "Compare actual weight with declared weight", f=m)
    a.decision("dweight", Y, 15, f=m)
    a.action("surcharge", Y, 15, "Calculate surcharge &amp; notify sender", f=l, w=180)
    a.decision("dagree", S, 15, f=sr)
    a.action("decline", S, 15, "Decline surcharge", f=sl, w=170)
    a.action("paysur", S, 16, "Pay surcharge via VietQR", f=sr, w=190)
    a.merge("mload", Y, 17, f=m)
    a.action("refund", Y, 18, "Cancel order &amp; create refund request", f=l, w=180)
    a.final("end_refund", Y, 19, f=l)
    a.action("seal", Y, 18, "Issue seal code (ready to launch)", f=m)
    a.merge("mlaunch", T, 19, f=t)
    a.action("launch", T, 20, "Launch drone", f=t, w=200)
    a.decision("dfly", Y, 21, f=m)
    a.bar("fork", S, 0.5, Y, m, 22)
    a.action("track", S, 23, "Track delivery timeline &amp; map")
    a.action("fly", Y, 23, "Fly mission: LAUNCHING → DEPARTED → EN_ROUTE → APPROACHING → ARRIVED",
             f=m, w=220, h=58)
    a.bar("join", S, 0.5, Y, m, 24)
    a.action("deposit", Y, 25, "Deposit parcel into receiving drone box (READY_FOR_PICKUP)", f=m, w=210)
    a.action("notify", Y, 26, "Issue pickup PIN &amp; notify receiver", f=m)
    a.merge("mpin", R, 27)
    a.action("enter", R, 28, "Enter pickup PIN at kiosk", w=200)
    a.action("check", Y, 29, "Validate pickup PIN", f=m)
    a.decision("dpin", Y, 30, f=m)
    a.action("wrong", Y, 30, "Show error &amp; count failed attempt", f=r, w=180)
    a.action("open", Y, 31, "Open box", f=m)
    a.action("take", R, 32, "Take parcel &amp; close door", w=200)
    a.action("done", Y, 33, "Complete order (COMPLETED) &amp; release box", f=m)
    a.final("end", Y, 34, f=m)

    a.flow("st", "choose"); a.flow("choose", "create"); a.flow("create", "reserve")
    a.flow("reserve", "qr"); a.flow("qr", "pay"); a.flow("pay", "verify"); a.flow("verify", "dpay")
    a.flow("dpay", "cancel", "[not paid within 30 min]", out="r", inn="l")
    a.flow("cancel", "end_cancel")
    a.flow("dpay", "paid", "[payment confirmed]")
    a.flow("paid", "place"); a.flow("place", "queue"); a.flow("queue", "accept")
    a.flow("accept", "mission"); a.flow("mission", "load"); a.flow("load", "weigh"); a.flow("weigh", "dweight")
    a.flow("dweight", "surcharge", "[heavier than declared]", out="l", inn="r")
    a.flow("surcharge", "dagree", out="l", inn="r")
    a.flow("dagree", "paysur", "[accept]")
    a.flow("dagree", "decline", "[decline]", out="l", inn="r", gpos=(-58, -20))
    a.flow("paysur", "mload", out="b", inn="l", via=[(a.X(S, sr), a.Y(17))])
    a.flow("dweight", "mload", "[within declared weight]")
    a.flow("decline", "refund", out="b", inn="l", via=[(a.X(S, sl), a.Y(18))])
    a.flow("refund", "end_refund")
    a.flow("mload", "seal")
    a.flow("seal", "mlaunch"); a.flow("mlaunch", "launch"); a.flow("launch", "dfly")
    xb = a.X(T, 0.86)
    a.flow("dfly", "mlaunch", "[outside flight window, bad weather or flights paused]", out="r", inn="r",
           via=[(xb, a.Y(21)), (xb, a.Y(19))], gpos=(10, -36))  # long guard sits above the loop line
    a.flow("dfly", "fork", "[launch allowed]", out="b", inn="t", at_in=a.X(Y, m))
    a.flow("fork", "track", out="b", at_out=a.X(S))
    a.flow("fork", "fly", out="b", at_out=a.X(Y, m))
    a.flow("track", "join", inn="t", at_in=a.X(S))
    a.flow("fly", "join", inn="t", at_in=a.X(Y, m))
    a.flow("join", "deposit", out="b", at_out=a.X(Y, m))
    a.flow("deposit", "notify"); a.flow("notify", "mpin"); a.flow("mpin", "enter")
    a.flow("enter", "check"); a.flow("check", "dpin")
    a.flow("dpin", "wrong", "[invalid PIN]", out="r", inn="l")
    xr = a.X(R) + 128
    a.flow("wrong", "mpin", out="r", inn="r", via=[(xr, a.Y(30)), (xr, a.Y(27))])
    a.flow("dpin", "open", "[valid PIN]")
    a.flow("open", "take"); a.flow("take", "done"); a.flow("done", "end")
    return a


# =============================================================================================================
# 4. Ask AI Assistant  (Registered User | System)
# =============================================================================================================
def ask_assistant():
    a = Activity("06d-activity-ask-ai-assistant", "Ask AI Assistant", [("Registered User", 400), ("System", 560)])
    U, Y = 0, 1
    m, s = 0.34, 0.8
    a.start("st", U, 0)
    a.action("open", U, 1, "Open AI assistant")
    a.merge("mq", U, 2)
    a.action("ask", U, 3, "Enter question &amp; send")
    a.decision("dlimit", Y, 4, f=m)
    a.action("limit", Y, 4, "Reject: hourly question limit reached", f=s, w=190)
    a.final("end_limit", Y, 5, f=s)
    a.action("prepare", Y, 5, "Restore Vietnamese diacritics if the question has none", f=m)
    a.decision("dorder", Y, 6, f=m)
    a.action("orders", Y, 6, "Load the user's own orders (no PIN, phone masked)", f=s, w=190)
    a.merge("mctx", Y, 7, f=m)
    a.action("retrieve", Y, 8, "Embed question &amp; retrieve top-k chunks the user's role may read", f=m, h=58)
    a.decision("dscore", Y, 9, f=m)
    a.action("refuse", Y, 9, "Answer &quot;the documents do not cover this&quot; (no LLM call)", f=s, w=190, h=58)
    a.action("answer", Y, 10, "Generate answer with Claude, citing the chunks used", f=m)
    a.merge("mans", Y, 11, f=m)
    a.action("save", Y, 12, "Save conversation, message &amp; citations", f=m)
    a.action("view", U, 13, "View answer &amp; cited sources")
    a.decision("dmore", U, 14)
    a.final("end", U, 15)

    a.flow("st", "open"); a.flow("open", "mq"); a.flow("mq", "ask"); a.flow("ask", "dlimit")
    a.flow("dlimit", "limit", "[limit reached]", out="r", inn="l")
    a.flow("limit", "end_limit")
    a.flow("dlimit", "prepare", "[within limit]")
    a.flow("prepare", "dorder")
    a.flow("dorder", "orders", "[about own orders]", out="r", inn="l")
    a.flow("orders", "mctx", out="b", inn="r", via=[(a.X(Y, s), a.Y(7))])
    a.flow("dorder", "mctx", "[general question]")
    a.flow("mctx", "retrieve"); a.flow("retrieve", "dscore")
    a.flow("dscore", "refuse", "[no chunk above threshold]", out="r", inn="l", gpos=(4, -34))
    a.flow("refuse", "mans", out="b", inn="r", via=[(a.X(Y, s), a.Y(11))])
    a.flow("dscore", "answer", "[relevant context found]")
    a.flow("answer", "mans"); a.flow("mans", "save"); a.flow("save", "view"); a.flow("view", "dmore")
    xl = a.X(U, 0) + 26
    a.flow("dmore", "mq", "[ask follow-up]", out="l", inn="l", via=[(xl, a.Y(14)), (xl, a.Y(2))],
           gpos=(-120, -20))
    a.flow("dmore", "end", "[done]")
    return a


# =============================================================================================================
# 5. Manage Knowledge Base  (Administrator | System)
# =============================================================================================================
def knowledge_base():
    a = Activity("06e-activity-manage-knowledge-base", "Manage Knowledge Base",
                 [("Administrator", 400), ("System", 560)])
    A, Y = 0, 1
    m, s = 0.34, 0.8
    a.start("st", A, 0)
    a.action("open", A, 1, "Open Knowledge Base page (admin web)")
    a.action("upload", A, 2, "Upload document (PDF, DOCX, MD, TXT, HTML) &amp; choose roles allowed to read it", h=58)
    a.action("validate", Y, 3, "Validate file type, size (≤ 20 MB) &amp; checksum", f=m)
    a.decision("dvalid", Y, 4, f=m)
    a.action("reject", Y, 4, "Reject upload &amp; show error", f=s, w=190)
    a.final("end_reject", Y, 5, f=s)
    a.merge("mindex", Y, 5, f=m)
    a.action("pending", Y, 6, "Save document (PENDING)", f=m)
    a.action("chunk", Y, 7, "Background job: extract text &amp; split into chunks (INDEXING)", f=m)
    a.action("embed", Y, 8, "Create embeddings &amp; store vectors", f=m)
    a.decision("dok", Y, 9, f=m)
    a.action("failed", Y, 9, "Mark document FAILED", f=s, w=190)
    a.action("ready", Y, 10, "Mark document READY", f=m)
    a.merge("mres", Y, 11, f=m)
    a.action("view", A, 12, "View document status &amp; indexed chunks")
    a.decision("dre", A, 13)
    a.final("end", A, 14)

    a.flow("st", "open"); a.flow("open", "upload"); a.flow("upload", "validate"); a.flow("validate", "dvalid")
    a.flow("dvalid", "reject", "[invalid or duplicate]", out="r", inn="l")
    a.flow("reject", "end_reject")
    a.flow("dvalid", "mindex", "[valid]")
    a.flow("mindex", "pending"); a.flow("pending", "chunk"); a.flow("chunk", "embed"); a.flow("embed", "dok")
    a.flow("dok", "failed", "[indexing error]", out="r", inn="l")
    a.flow("failed", "mres", out="b", inn="r", via=[(a.X(Y, s), a.Y(11))])
    a.flow("dok", "ready", "[indexed]")
    a.flow("ready", "mres"); a.flow("mres", "view"); a.flow("view", "dre")
    xl = a.X(A, 0) + 26
    a.flow("dre", "mindex", "[re-index]", out="l", inn="l",
           via=[(xl, a.Y(13)), (xl, a.Y(4.5)), (a.X(Y, m) - 60, a.Y(4.5)), (a.X(Y, m) - 60, a.Y(5))],
           gpos=(-80, -20))
    a.flow("dre", "end", "[done]")
    return a


if __name__ == "__main__":
    only = set(sys.argv[1:])
    ok = True
    for f in (send_parcel, rent_locker, drone_delivery, ask_assistant, knowledge_base):
        act = f()
        if only and not any(o in act.d.name for o in only):
            continue
        ok &= act.save()
    sys.exit(0 if ok else 1)
