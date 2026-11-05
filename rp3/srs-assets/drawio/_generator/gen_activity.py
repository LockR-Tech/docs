"""UML activity diagrams, horizontal swimlanes: one band per actor (every backend service, the locker and the drone
grouped as "System"), flow runs left to right. Every edge is an orthogonal polyline with explicit ports so draw.io
never re-routes it. Exported only when no edge crosses another edge, passes through a node, or leaves/enters a node
through the wrong side, and no two nodes overlap.

Notation (UML 2.5): ● initial node · ◉ activity final · rounded rectangle = action · ◇ decision / merge with
[guard] on each outgoing edge · black bar = fork / join · open arrowhead = control flow.
Colours: blue = ordinary action, green = locker / drone / notification / AI action, orange = cancel or error path.

Terms follow the app/backend: drop-off PIN, pickup PIN, box, VietQR bank transfer, order states in CAPS.
Usage: python gen_activity.py [name-fragment ...]
"""
import os
import sys
from dio import Diagram
from geom import seg_box, seg_cross, too_close_parallel

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the drawio/ folder

TONE = {"blue": ("#DAE8FC", "#6C8EBF"), "green": ("#D5E8D4", "#82B366"), "orange": ("#FFE6CC", "#D79B00")}
ACTION = ("rounded=1;arcSize=18;whiteSpace=wrap;html=1;fillColor={f};strokeColor={s};fontColor=#1A1A1A;fontSize=11;"
          "spacingLeft=4;spacingRight=4;")
DIAMOND = "rhombus;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;"
START = "ellipse;html=1;shape=startState;fillColor=#000000;strokeColor=#000000;"
FINAL = "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;"
BAR = "rounded=0;html=1;fillColor=#000000;strokeColor=#000000;"
HEAD = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#37474F;strokeColor=#FFFFFF;strokeWidth=2;fontColor=#FFFFFF;"
        "fontStyle=1;fontSize=13;")
BODY = "rounded=0;html=1;fillColor=#F7F8FA;strokeColor=none;"
RULE = "rounded=0;html=1;fillColor=#C9CED6;strokeColor=none;"
EDGE = "edgeStyle=none;html=1;rounded=0;endArrow=open;endSize=8;strokeWidth=1.2;strokeColor=#666666;"
GUARD = "text;html=1;fontSize=10;fontColor=#333333;spacing=0;verticalAlign=middle;whiteSpace=wrap;"

HW = 132           # lane header width
CW = 200           # column pitch
AW, AH = 166, 56   # action box
DS = 30            # decision diamond
SIDE = {"t": (0.5, 0), "b": (0.5, 1), "l": (0, 0.5), "r": (1, 0.5)}


class Node:
    def __init__(self, key, kind, x, y, w, h):
        self.key, self.kind, self.x, self.y, self.w, self.h = key, kind, x, y, w, h
        self.cx, self.cy = x + w / 2, y + h / 2
        self.vid = None
        self.label, self.tone = "", "blue"

    def port(self, side, at=None):
        if at is not None:                       # a point along one side of a bar
            if side in "lr":
                return (self.x if side == "l" else self.x + self.w, at)
            return (at, self.y if side == "t" else self.y + self.h)
        fx, fy = SIDE[side]
        return (self.x + fx * self.w, self.y + fy * self.h)

    def box(self):
        return (self.x, self.y, self.w, self.h)


class Activity:
    def __init__(self, name, lanes, left=20, top=20):
        """lanes: [(label, height)] from top to bottom."""
        self.d = Diagram(name)
        self.left = left
        self.lanes, y = [], top
        for label, h in lanes:
            self.lanes.append((label, y, h))
            y += h
        self.nodes, self.edges, self.guards = {}, [], []
        self.max_col = 0

    # ---- placement ------------------------------------------------------------------------------------------
    def X(self, col):
        return self.left + HW + 120 + col * CW

    def Y(self, lane, f=0.5):
        _, y, h = self.lanes[lane]
        return y + f * h

    def _add(self, key, kind, lane, col, f, w, h):
        cx, cy = self.X(col), self.Y(lane, f)
        n = Node(key, kind, cx - w / 2, cy - h / 2, w, h)
        assert key not in self.nodes, key
        self.nodes[key] = n
        self.max_col = max(self.max_col, col)
        return n

    def start(self, key, lane, col, f=0.5):
        self._add(key, "start", lane, col, f, 28, 28)

    def final(self, key, lane, col, f=0.5):
        self._add(key, "final", lane, col, f, 30, 30)

    def action(self, key, lane, col, label, f=0.5, tone="blue", w=AW, h=AH):
        n = self._add(key, "action", lane, col, f, w, h)
        n.label, n.tone = label, tone

    def decision(self, key, lane, col, f=0.5):
        self._add(key, "decision", lane, col, f, DS, DS)

    merge = decision

    def bar(self, key, col, lane_from, f_from, lane_to, f_to):
        y0, y1 = self.Y(lane_from, f_from) - 34, self.Y(lane_to, f_to) + 34
        self.nodes[key] = Node(key, "bar", self.X(col) - 4, y0, 8, y1 - y0)
        self.max_col = max(self.max_col, col)

    # ---- edges ----------------------------------------------------------------------------------------------
    def flow(self, a, b, guard="", out=None, inn=None, via=(), at_out=None, at_in=None, gpos=None):
        """Orthogonal control flow a -> b. Default: straight right along a band, straight up/down in a column,
        otherwise right out of a then up/down into b. via: extra absolute bend points (loops).
        gpos: (dx, dy) guard offset from the exit point."""
        A, B = self.nodes[a], self.nodes[b]
        if out is None:
            if abs(A.cx - B.cx) < 1 and "bar" not in (A.kind, B.kind):
                out = "b" if B.cy > A.cy else "t"
            else:
                out = "r" if B.cx > A.cx else "l"
        if inn is None:
            if abs(A.cy - B.cy) < 1 or "bar" in (A.kind, B.kind) or (abs(A.cx - B.cx) >= 1 and out in "tb"):
                inn = "l" if B.cx > A.cx else "r"
            else:
                inn = "t" if B.cy > A.cy else "b"
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
            elif abs(p0[1] - p1[1]) > 0.5:
                xm = (p0[0] + p1[0]) / 2
                pts = [(xm, p0[1]), (xm, p1[1])]
        self.edges.append((a, b, out, inn, p0, p1, pts, at_out, at_in))
        if guard:
            nxt = (pts or [p1])[0]
            room = abs(nxt[0] - p0[0]) - 8 if out in "lr" else 150
            self.guards.append((guard, out, p0, gpos, room))

    # ---- checks and output ----------------------------------------------------------------------------------
    def audit(self):
        problems, lines = [], []
        for a, b, out, inn, p0, p1, pts, *_ in self.edges:
            poly = [p0, *pts, p1]
            for i in range(len(poly) - 1):
                (x0, y0), (x1, y1) = poly[i], poly[i + 1]
                if abs(x0 - x1) > 0.5 and abs(y0 - y1) > 0.5:
                    problems.append(f"diagonal segment {a}->{b}: {poly[i]} {poly[i + 1]}")
            (sx, sy), (nx, ny) = poly[0], poly[1]
            if not {"t": ny < sy, "b": ny > sy, "l": nx < sx, "r": nx > sx}[out]:
                problems.append(f"arrow {a}->{b} leaves '{out}' in the wrong direction")
            (lx, ly), (ex, ey) = poly[-2], poly[-1]
            if not {"t": ey > ly, "b": ey < ly, "l": ex > lx, "r": ex < lx}[inn]:
                problems.append(f"arrow {a}->{b} enters '{inn}' from the wrong direction")
            lines.append(((a, b), poly))
            for k, n in self.nodes.items():
                if k in (a, b):
                    continue
                for i in range(len(poly) - 1):
                    if seg_box(poly[i], poly[i + 1], n.box(), margin=-4):
                        problems.append(f"edge {a}->{b} passes through {k}")
                        break
        keys = list(self.nodes)
        for i, k in enumerate(keys):                                  # nodes keep a 6 px gap
            n = self.nodes[k]
            for k2 in keys[i + 1:]:
                m = self.nodes[k2]
                if n.x < m.x + m.w + 6 and m.x < n.x + n.w + 6 and n.y < m.y + m.h + 6 and m.y < n.y + n.h + 6:
                    problems.append(f"nodes {k} and {k2} overlap")
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                (ka, pa), (kb, pb) = lines[i], lines[j]
                for s in range(len(pa) - 1):
                    for t in range(len(pb) - 1):
                        if seg_cross(pa[s], pa[s + 1], pb[t], pb[t + 1]):
                            problems.append(f"edges {ka} and {kb} cross")
                        elif not set(ka) & set(kb) and too_close_parallel(pa[s], pa[s + 1], pb[t], pb[t + 1], 6):
                            problems.append(f"edges {ka} and {kb} overlap")
        return problems

    def build(self):
        d = self.d
        x_end = self.X(self.max_col) + CW / 2 + 10
        x_body = self.left + HW
        for i, (label, y, h) in enumerate(self.lanes):
            d.vertex(label, self.left, y, HW, h, HEAD)
            d.vertex("", x_body, y, x_end - x_body, h, BODY)
            if i:
                d.vertex("", x_body, y - 0.5, x_end - x_body, 1, RULE)
        for n in self.nodes.values():
            if n.kind == "action":
                f, s = TONE[n.tone]
                style = ACTION.format(f=f, s=s)
            else:
                style = {"start": START, "final": FINAL, "decision": DIAMOND, "bar": BAR}[n.kind]
            n.vid = d.vertex(n.label, n.x, n.y, n.w, n.h, style)
        for a, b, out, inn, p0, p1, pts, at_out, at_in in self.edges:
            A, B = self.nodes[a], self.nodes[b]

            def frac(node, side, at):
                if at is None:
                    return SIDE[side]
                if side in "lr":
                    return SIDE[side][0], (at - node.y) / node.h
                return (at - node.x) / node.w, SIDE[side][1]

            ex, ey = frac(A, out, at_out)
            nx, ny = frac(B, inn, at_in)
            style = EDGE + (f"exitX={ex:.4f};exitY={ey:.4f};exitDx=0;exitDy=0;"
                            f"entryX={nx:.4f};entryY={ny:.4f};entryDx=0;entryDy=0;")
            d.edge(A.vid, B.vid, style, points=pts)
        for text, out, (px, py), gpos, room in self.guards:
            need = 5.6 * len(text) + 6
            w = min(need, 230) if gpos else min(need, max(room, 56))
            lines = -(-need // w)
            h = 13 * lines + 2
            if gpos:
                gx, gy = px + gpos[0], py + gpos[1]
            elif out == "b":
                gx, gy = px + 5, py + 2
            elif out == "t":
                gx, gy = px + 5, py - h - 2
            elif out == "r":
                gx, gy = px + 4, py - h - 1
            else:
                gx, gy = px - 4 - w, py - h - 1
            align = "align=right;" if (out == "l" and not gpos) else "align=left;"
            d.vertex(text, gx, gy, w, h, GUARD + align)

    def save(self):
        problems = self.audit()
        if problems:
            print(f"[{self.d.name}] NOT exported:")
            for p in sorted(set(problems)):
                print("   ", p)
            return False
        self.build()
        _, png = self.d.save(OUT, scale=1.6, margin=16)
        print("wrote", png)
        return True


# =============================================================================================================
# 1. Send Parcel via Locker  (Sender | System | Receiver)
# =============================================================================================================
def send_parcel():
    a = Activity("06a-activity-send-parcel", [("Sender", 130), ("System", 236), ("Receiver", 150)])
    S, Y, R = 0, 1, 2
    up, lo = 0.27, 0.75                      # System upper / lower row
    a.start("st", S, -0.45)
    a.action("choose", S, 0.5, "Choose locker &amp; box size; enter receiver phone, name &amp; email")
    a.action("create", Y, 0.5, "Create order (INITIALIZED, UNPAID), reserve box (RESERVED) &amp; generate VietQR code", f=up)
    a.action("pay", S, 1.5, "Pay by VietQR bank transfer (scan QR or open banking app)")
    a.action("verify", Y, 2.5, "Verify bank transfer", f=up)
    a.decision("dpay", Y, 3.3, f=up)
    a.action("cancel", Y, 3.3, "Cancel order &amp; release box", f=lo, tone="orange")
    a.final("end_cancel", Y, 4.05, f=lo)
    a.action("paid", Y, 4.35, "Mark order PAID &amp; issue drop-off PIN", f=up)
    a.action("open_req", S, 4.35, "Tap &quot;Open box to drop off&quot; in app or enter drop-off PIN at kiosk")
    a.action("open1", Y, 5.35, "Send open command to locker &amp; open box", f=up, tone="green")
    a.action("put", S, 6.35, "Put parcel in box, close door &amp; confirm drop-off")
    a.action("stored", Y, 7.35, "Mark box OCCUPIED, order STORING &amp; issue pickup PIN", f=up)
    a.action("notify", Y, 8.35, "Send pickup PIN to receiver (in-app, email, SMS)", f=up, tone="green")
    a.merge("mpin", R, 8.35, f=0.4)
    a.action("enter", R, 9.15, "Enter pickup PIN at kiosk", f=0.4)
    a.action("check", Y, 10.15, "Validate pickup PIN", f=up)
    a.decision("dpin", Y, 10.95, f=up)
    a.action("wrong", Y, 10.95, "Show error &amp; count failed attempt (box locked after too many)", f=lo, tone="orange")
    a.action("open2", Y, 11.95, "Open box", f=up, tone="green")
    a.action("take", R, 11.95, "Take parcel &amp; close door", f=0.4)
    a.action("done", Y, 12.95, "Complete order (COMPLETED), release box &amp; add loyalty points to sender", f=up)
    a.final("end", Y, 13.75, f=up)

    a.flow("st", "choose"); a.flow("choose", "create"); a.flow("create", "pay", out="r", inn="b")
    a.flow("pay", "verify"); a.flow("verify", "dpay")
    a.flow("dpay", "cancel", "[not paid within hold time]")
    a.flow("cancel", "end_cancel")
    a.flow("dpay", "paid", "[payment confirmed]", gpos=(4, -16))
    a.flow("paid", "open_req"); a.flow("open_req", "open1"); a.flow("open1", "put", out="r", inn="b")
    a.flow("put", "stored"); a.flow("stored", "notify"); a.flow("notify", "mpin"); a.flow("mpin", "enter")
    a.flow("enter", "check", out="r", inn="b"); a.flow("check", "dpin")
    a.flow("dpin", "wrong", "[invalid PIN]")
    yl = a.Y(R, 0.86)
    a.flow("wrong", "mpin", out="b", inn="b", via=[(a.X(10.95), yl), (a.X(8.35), yl)])
    a.flow("dpin", "open2", "[valid PIN]", gpos=(4, -16))
    a.flow("open2", "take"); a.flow("take", "done", out="r", inn="b"); a.flow("done", "end")
    return a


# =============================================================================================================
# 2. Rent Locker by Hours  (Customer | System)
# =============================================================================================================
def rent_locker():
    a = Activity("06b-activity-rent-locker", [("Customer", 160), ("System", 236)])
    C, Y = 0, 1
    up, lo = 0.27, 0.75
    a.start("st", C, -0.45)
    a.action("choose", C, 0.5, "Choose locker, box type &amp; rental hours")
    a.action("create", Y, 0.5, "Create rental order (UNPAID), reserve box &amp; generate VietQR code", f=up)
    a.action("pay", C, 1.5, "Pay by VietQR bank transfer")
    a.action("verify", Y, 2.5, "Verify bank transfer", f=up)
    a.decision("dpay", Y, 3.3, f=up)
    a.action("cancel", Y, 3.3, "Cancel order &amp; release box", f=lo, tone="orange")
    a.final("end_cancel", Y, 4.05, f=lo)
    a.action("paid", Y, 4.35, "Mark order PAID &amp; issue rental PIN", f=up)
    a.action("open_first", C, 4.35, "Tap &quot;Open box&quot; in app or enter PIN at kiosk")
    a.action("open1", Y, 5.35, "Open box", f=up, tone="green")
    a.action("put", C, 6.35, "Put items in box, close door &amp; start rental")
    a.action("storing", Y, 7.35, "Start rental period (order STORING)", f=up)
    a.merge("muse", C, 8.15)
    a.action("use", C, 8.95, "Open box again: enter PIN at kiosk or tap &quot;Open box&quot;")
    a.decision("dvalid", Y, 9.95, f=up)
    a.action("extend", C, 9.95, "Extend rental &amp; pay via VietQR")
    a.action("extended", Y, 10.95, "Verify payment &amp; extend rental end time", f=up)
    a.merge("mopen", Y, 11.75, f=up)
    a.action("open2", Y, 12.55, "Open box", f=up, tone="green")
    a.action("access", C, 12.55, "Take or add items &amp; close door")
    a.decision("dmore", C, 13.35)
    a.action("finish", C, 14.15, "End rental &amp; take all items (in app or at kiosk)")
    a.action("done", Y, 15.15, "Complete order (COMPLETED), release box &amp; add loyalty points", f=up)
    a.final("end", Y, 15.95, f=up)

    a.flow("st", "choose"); a.flow("choose", "create"); a.flow("create", "pay", out="r", inn="b")
    a.flow("pay", "verify"); a.flow("verify", "dpay")
    a.flow("dpay", "cancel", "[not paid within hold time]")
    a.flow("cancel", "end_cancel")
    a.flow("dpay", "paid", "[payment confirmed]", gpos=(4, -16))
    a.flow("paid", "open_first"); a.flow("open_first", "open1"); a.flow("open1", "put", out="r", inn="b")
    a.flow("put", "storing"); a.flow("storing", "muse", out="r", inn="b"); a.flow("muse", "use")
    a.flow("use", "dvalid", out="b", inn="l")
    a.flow("dvalid", "extend", "[rental expired: PIN rejected]", gpos=(5, -44))
    a.flow("extend", "extended")
    a.flow("extended", "mopen")
    yl = a.Y(Y, lo)
    a.flow("dvalid", "mopen", "[within rental period]", out="b", inn="b",
           via=[(a.X(9.95), yl), (a.X(11.75), yl)])
    a.flow("mopen", "open2"); a.flow("open2", "access"); a.flow("access", "dmore")
    yt = a.Y(C, 0.1)
    a.flow("dmore", "muse", "[continue rental]", out="t", inn="t",
           via=[(a.X(13.35), yt), (a.X(8.15), yt)], gpos=(5, -34))
    a.flow("dmore", "finish", "[end rental]", gpos=(2, -16))
    a.flow("finish", "done", out="r", inn="t"); a.flow("done", "end")
    return a


# =============================================================================================================
# 3. Drone Delivery  (Sender | System | Drone Technician | Receiver)
# =============================================================================================================
def drone_delivery():
    a = Activity("06c-activity-drone-delivery",
                 [("Sender", 140), ("System", 236), ("Drone<br>Technician", 150), ("Receiver", 150)])
    S, Y, T, R = 0, 1, 2, 3
    up, lo = 0.27, 0.75
    a.start("st", S, -0.45)
    a.action("choose", S, 0.5, "Choose receiving locker, parcel details &amp; receiver; confirm no prohibited items")
    a.action("create", Y, 0.5, "Check route, reserve drone box, create order &amp; generate VietQR code", f=up)
    a.action("pay", S, 1.5, "Pay by VietQR bank transfer")
    a.action("verify", Y, 2.5, "Verify bank transfer", f=up)
    a.decision("dpay", Y, 3.3, f=up)
    a.action("cancel", Y, 3.3, "Cancel order &amp; release box", f=lo, tone="orange")
    a.final("end_cancel", Y, 4.05, f=lo)
    a.action("paid", Y, 4.35, "Mark order PAID (AWAITING_DISPATCH)", f=up)
    a.action("place", S, 4.35, "Put parcel in drone box at sending locker &amp; tap &quot;I've placed the parcel&quot;")
    a.action("queue", Y, 5.35, "Show order in dispatch queue", f=up)
    a.action("accept", T, 5.35, "Accept order &amp; choose an idle drone at sending locker")
    a.action("mission", Y, 6.35, "Create delivery mission", f=lo)
    a.action("load", T, 7.35, "Weigh parcel, complete checklist &amp; confirm loading")
    a.action("weigh", Y, 8.35, "Compare actual weight with declared weight", f=lo)
    a.decision("dweight", Y, 9.25, f=lo)
    a.action("surcharge", Y, 9.25, "Calculate surcharge &amp; notify sender", f=up, tone="orange")
    a.decision("dagree", S, 9.25)
    a.action("decline", S, 8.15, "Decline surcharge", tone="orange", w=140)
    a.action("refund", Y, 8.15, "Cancel order &amp; create refund request", f=up, tone="orange", w=150)
    a.final("end_refund", Y, 7.3, f=up)
    a.action("paysur", S, 10.25, "Pay surcharge via VietQR")
    a.merge("mload", Y, 11.25, f=lo)
    a.action("seal", Y, 12.05, "Issue seal code (ready to launch)", f=lo)
    a.merge("mlaunch", T, 12.05, f=0.4)
    a.action("launch", T, 12.85, "Launch drone", f=0.4)
    a.decision("dfly", Y, 13.65, f=lo)
    a.bar("fork", 14.35, S, 0.5, Y, lo)
    a.action("track", S, 15.2, "Track delivery timeline &amp; map")
    a.action("fly", Y, 15.2, "Fly mission: LAUNCHING → DEPARTED → EN_ROUTE → APPROACHING → ARRIVED",
             f=lo, tone="green", h=66)
    a.bar("join", 16.05, S, 0.5, Y, lo)
    a.action("deposit", Y, 16.9, "Deposit parcel into receiving drone box (READY_FOR_PICKUP)", f=lo, tone="green")
    a.action("notify", Y, 17.9, "Issue pickup PIN &amp; notify receiver", f=lo, tone="green")
    a.merge("mpin", R, 17.9, f=0.4)
    a.action("enter", R, 18.7, "Enter pickup PIN at kiosk", f=0.4)
    a.action("check", Y, 19.7, "Validate pickup PIN", f=up)
    a.decision("dpin", Y, 20.5, f=up)
    a.action("wrong", Y, 20.5, "Show error &amp; count failed attempt", f=lo, tone="orange")
    a.action("open", Y, 21.5, "Open box", f=up, tone="green")
    a.action("take", R, 21.5, "Take parcel &amp; close door", f=0.4)
    a.action("done", Y, 22.5, "Complete order (COMPLETED) &amp; release box", f=up)
    a.final("end", Y, 23.3, f=up)

    a.flow("st", "choose"); a.flow("choose", "create"); a.flow("create", "pay", out="r", inn="b")
    a.flow("pay", "verify"); a.flow("verify", "dpay")
    a.flow("dpay", "cancel", "[not paid within 30 min]")
    a.flow("cancel", "end_cancel")
    a.flow("dpay", "paid", "[payment confirmed]", gpos=(4, -16))
    a.flow("paid", "place"); a.flow("place", "queue"); a.flow("queue", "accept")
    a.flow("accept", "mission", out="r", inn="b"); a.flow("mission", "load", out="r", inn="t")
    a.flow("load", "weigh", out="r", inn="b"); a.flow("weigh", "dweight")
    a.flow("dweight", "surcharge", "[heavier than declared]", gpos=(5, -32))
    a.flow("surcharge", "dagree")
    a.flow("dagree", "decline", "[decline]", gpos=(-50, -16))
    a.flow("decline", "refund"); a.flow("refund", "end_refund")
    a.flow("dagree", "paysur", "[accept]", gpos=(4, -16))
    a.flow("paysur", "mload", out="r", inn="t")
    a.flow("dweight", "mload", "[within declared weight]", gpos=(4, -16))
    a.flow("mload", "seal"); a.flow("seal", "mlaunch"); a.flow("mlaunch", "launch")
    a.flow("launch", "dfly", out="r", inn="b")
    yb = a.Y(T, 0.86)
    xg = a.X(13.65) + 40
    a.flow("dfly", "mlaunch", "[outside flight window, bad weather or flights paused]", out="r", inn="b",
           via=[(xg, a.Y(Y, lo)), (xg, yb), (a.X(12.05), yb)], gpos=(31, 68))
    yf = a.Y(Y, up) + 30
    a.flow("dfly", "fork", "[launch allowed]", out="t", inn="l", at_in=yf, via=[(a.X(13.65), yf)], gpos=(5, -46))
    a.flow("fork", "track", out="r", at_out=a.Y(S))
    a.flow("fork", "fly", out="r", at_out=a.Y(Y, lo))
    a.flow("track", "join", inn="l", at_in=a.Y(S))
    a.flow("fly", "join", inn="l", at_in=a.Y(Y, lo))
    a.flow("join", "deposit", out="r", at_out=a.Y(Y, lo))
    a.flow("deposit", "notify"); a.flow("notify", "mpin"); a.flow("mpin", "enter")
    a.flow("enter", "check", out="r", inn="b"); a.flow("check", "dpin")
    a.flow("dpin", "wrong", "[invalid PIN]")
    yl = a.Y(R, 0.86)
    a.flow("wrong", "mpin", out="b", inn="b", via=[(a.X(20.5), yl), (a.X(17.9), yl)])
    a.flow("dpin", "open", "[valid PIN]", gpos=(4, -16))
    a.flow("open", "take"); a.flow("take", "done", out="r", inn="b"); a.flow("done", "end")
    return a


# =============================================================================================================
# 4. Ask AI Assistant  (Registered User | System)
# =============================================================================================================
def ask_assistant():
    a = Activity("06d-activity-ask-ai-assistant", [("Registered<br>User", 160), ("System", 236)])
    U, Y = 0, 1
    up, lo = 0.27, 0.75
    a.start("st", U, -0.45)
    a.action("open", U, 0.5, "Open AI assistant")
    a.merge("mq", U, 1.3)
    a.action("ask", U, 2.1, "Enter question &amp; send")
    a.decision("dlimit", Y, 3.1, f=up)
    a.action("limit", Y, 3.1, "Reject: hourly question limit reached", f=lo, tone="orange")
    a.final("end_limit", Y, 3.85, f=lo)
    a.action("prepare", Y, 4.1, "Restore Vietnamese diacritics if the question has none", f=up)
    a.decision("dorder", Y, 4.9, f=up)
    a.action("orders", Y, 4.9, "Load the user's own orders (no PIN, phone masked)", f=lo)
    a.merge("mctx", Y, 5.9, f=up)
    a.action("retrieve", Y, 6.7, "Embed question &amp; retrieve top-k chunks the user's role may read", f=up)
    a.decision("dscore", Y, 7.5, f=up)
    a.action("refuse", Y, 7.5, "Answer &quot;the documents do not cover this&quot; (no LLM call)", f=lo, tone="orange")
    a.action("answer", Y, 8.5, "Generate answer with Claude, citing the chunks used", f=up, tone="green")
    a.merge("mans", Y, 9.3, f=up)
    a.action("save", Y, 10.1, "Save conversation, message &amp; citations", f=up)
    a.action("view", U, 11.1, "View answer &amp; cited sources")
    a.decision("dmore", U, 11.9)
    a.final("end", U, 12.6)

    a.flow("st", "open"); a.flow("open", "mq"); a.flow("mq", "ask"); a.flow("ask", "dlimit", out="r", inn="t")
    a.flow("dlimit", "limit", "[limit reached]")
    a.flow("limit", "end_limit")
    a.flow("dlimit", "prepare", "[within limit]", gpos=(3, -16))
    a.flow("prepare", "dorder")
    a.flow("dorder", "orders", "[about own orders]")
    a.flow("orders", "mctx", out="r", inn="b")
    a.flow("dorder", "mctx", "[general question]", gpos=(3, -16))
    a.flow("mctx", "retrieve"); a.flow("retrieve", "dscore")
    a.flow("dscore", "refuse", "[no chunk above threshold]")
    a.flow("refuse", "mans", out="r", inn="b")
    a.flow("dscore", "answer", "[relevant context found]", gpos=(3, -28))
    a.flow("answer", "mans"); a.flow("mans", "save"); a.flow("save", "view", out="r", inn="b")
    a.flow("view", "dmore")
    yt = a.Y(U, 0.1)
    a.flow("dmore", "mq", "[ask follow-up]", out="t", inn="t", via=[(a.X(11.9), yt), (a.X(1.3), yt)],
           gpos=(5, -34))
    a.flow("dmore", "end", "[done]", gpos=(2, -16))
    return a


# =============================================================================================================
# 5. Manage Knowledge Base  (Administrator | System)
# =============================================================================================================
def knowledge_base():
    a = Activity("06e-activity-manage-knowledge-base", [("Administrator", 160), ("System", 236)])
    A, Y = 0, 1
    up, lo = 0.27, 0.75
    a.start("st", A, -0.45)
    a.action("open", A, 0.5, "Open Knowledge Base page (admin web)")
    a.action("upload", A, 1.5, "Upload document (PDF, DOCX, MD, TXT, HTML) &amp; choose roles allowed to read it")
    a.action("validate", Y, 2.5, "Validate file type, size (≤ 20 MB) &amp; checksum", f=up)
    a.decision("dvalid", Y, 3.3, f=up)
    a.action("reject", Y, 3.3, "Reject upload &amp; show error", f=lo, tone="orange")
    a.final("end_reject", Y, 4.05, f=lo)
    a.merge("mindex", Y, 4.1, f=up)
    a.action("pending", Y, 4.9, "Save document (PENDING)", f=up)
    a.action("chunk", Y, 5.9, "Background job: extract text &amp; split into chunks (INDEXING)", f=up)
    a.action("embed", Y, 6.9, "Create embeddings &amp; store vectors", f=up, tone="green")
    a.decision("dok", Y, 7.7, f=up)
    a.action("failed", Y, 7.7, "Mark document FAILED", f=lo, tone="orange")
    a.action("ready", Y, 8.7, "Mark document READY", f=up)
    a.merge("mres", Y, 9.5, f=up)
    a.action("view", A, 10.5, "View document status &amp; indexed chunks")
    a.decision("dre", A, 11.3)
    a.final("end", A, 12.0)

    a.flow("st", "open"); a.flow("open", "upload"); a.flow("upload", "validate", out="r", inn="t")
    a.flow("validate", "dvalid")
    a.flow("dvalid", "reject", "[invalid or duplicate]")
    a.flow("reject", "end_reject")
    a.flow("dvalid", "mindex", "[valid]", gpos=(3, -16))
    a.flow("mindex", "pending"); a.flow("pending", "chunk"); a.flow("chunk", "embed"); a.flow("embed", "dok")
    a.flow("dok", "failed", "[indexing error]")
    a.flow("failed", "mres", out="r", inn="b")
    a.flow("dok", "ready", "[indexed]", gpos=(3, -16))
    a.flow("ready", "mres"); a.flow("mres", "view", out="r", inn="b"); a.flow("view", "dre")
    yt = a.Y(A, 0.1)
    a.flow("dre", "mindex", "[re-index]", out="t", inn="t", via=[(a.X(11.3), yt), (a.X(4.1), yt)],
           gpos=(5, -34))
    a.flow("dre", "end", "[done]", gpos=(2, -16))
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
