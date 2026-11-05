"""State machine diagrams (draw.io) for the main LockR entities — every state the code can reach,
happy and unhappy paths (cancel, expire, fail, reject, timeout…).

Rules (checked before writing each file):
  * exactly one initial node and one final node;
  * no cycles (the graph is a DAG). A transition that returns to an earlier state (e.g. "cell released ->
    Available", "admin sends a revised proposal") is drawn into the final node, with the state it returns to
    written in the label; secondary back edges are left out when the state already reaches the final node;
  * every state is reachable from the initial node and reaches the final node;
  * state names are Title Case (one word per enum token, e.g. READY_FOR_PICKUP -> Ready For Pickup);
  * state colour shows its meaning (CATEGORIES): yellow waiting, blue in progress, green completed, orange needs
    attention, red canceled / failed, grey inactive / removed; a legend is drawn under the subtitle;
  * transition labels stay short (main idea only);
  * a grey dashed frame is a composite state (group): a transition leaving the frame applies to every state
    inside it. Frames hold no initial node, so each diagram keeps a single initial node;
  * no edge segment passes through a state, no two edges cross (edges may merge just before the final node).

Source of truth: backend `origin/main` (order-service, locker-service, payment-service, auth-service) and
the clients that trigger each transition (mobile app, admin web, kiosk).

Usage:  py gen_state_machines.py            -> writes ../06*-state-machine-*.drawio
        py gen_state_machines.py --png DIR  -> also renders PNG previews into DIR (needs Chrome and the
                                               draw.io viewer, path in env VIEWER_JS)
"""
import glob
import html
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)

COLW, ROWH = 360, 128          # grid pitch
W, H = 230, 56                 # state box
C = 30                         # initial / final circle
MX, MY = 300, 100              # left/top margin (room for the title)

STATE = ("rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor={fill};strokeColor={stroke};"
         "fontColor=#000000;fontSize=15;fontStyle=1;")

# State colour by meaning (draw.io standard palette); legend text shown on every diagram.
CATEGORIES = {
    "pending": ("#FFF2CC", "#D6B656", "Waiting / pending"),
    "active": ("#DAE8FC", "#6C8EBF", "In progress / operational"),
    "success": ("#D5E8D4", "#82B366", "Completed"),
    "warning": ("#FFE6CC", "#D79B00", "Needs attention"),
    "failure": ("#F8CECC", "#B85450", "Canceled / failed"),
    "disabled": ("#F5F5F5", "#666666", "Inactive / removed"),
}
DEFAULT_CATEGORY = {
    **dict.fromkeys(["INITIALIZED", "AWAITING_DISPATCH", "PENDING", "SEARCHING", "OFFERED", "AWAITING_LOADING",
                     "READY_TO_LAUNCH", "OPEN_LID_REQUESTED", "CLOSE_LID_REQUESTED", "PENDING_CHECK", "OPEN",
                     "RESERVED", "RETURN_REQUESTED", "AWAITING_ADMIN_REVIEW", "AWAITING_CUSTOMER_RESPONSE",
                     "CONFIRMED", "READY_FOR_PICKUP", "REPORTED"], "pending"),
    **dict.fromkeys(["STORING", "PICKUP_ASSIGNED", "PICKED_UP", "ACCEPTED", "LAUNCHING", "DEPARTED", "EN_ROUTE",
                     "APPROACHING", "ARRIVED", "LID_OPENING", "LID_OPENED", "IN_PROGRESS", "INVESTIGATING",
                     "RECOVERY_IN_PROGRESS", "RESOLUTION_IN_PROGRESS", "COMMAND_ACCEPTED", "RETURNING", "OCCUPIED",
                     "IN_FLIGHT", "ACTIVE", "IDLE", "AVAILABLE", "CHARGING", "CLEANING"], "active"),
    **dict.fromkeys(["COMPLETED", "RESOLVED", "DEPOSITED", "CONSUMED", "TEST_COMPLETED"], "success"),
    **dict.fromkeys(["EXPIRED", "FAULT", "MAINTENANCE", "OUT_OF_SERVICE", "MANUAL_INTERVENTION_REQUIRED",
                     "DISPUTED"], "warning"),
    **dict.fromkeys(["CANCELED", "CANCELLED", "FAILED", "REJECTED", "ABORTED", "LID_OPEN_FAILED",
                     "LID_CLOSE_FAILED", "DROP_REPORTED"], "failure"),
    **dict.fromkeys(["INACTIVE", "DELETED"], "disabled"),
}
LEGEND_CHIP = "rounded=1;arcSize=30;html=1;fillColor={fill};strokeColor={stroke};"
LEGEND_TEXT = "text;html=1;align=left;verticalAlign=middle;fontSize=12;fontColor=#333333;"
START = "ellipse;html=1;shape=startState;fillColor=#000000;strokeColor=#000000;"
CHOICE = "rhombus;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.4;"
END = "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;"
GROUP = ("rounded=1;arcSize=3;absoluteArcSize=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#8C8C8C;"
         "dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontSize=13;"
         "fontStyle=3;fontColor=#555555;")
EDGE = ("edgeStyle=none;rounded=0;html=1;strokeColor=#333333;strokeWidth=1.4;endArrow=block;endFill=1;"
        "endSize=8;fontSize=12;fontColor=#000000;labelBackgroundColor=#FFFFFF;")
TITLE = "text;html=1;align=left;verticalAlign=middle;fontSize=22;fontStyle=1;fontColor=#000000;"
SUB = "text;html=1;align=left;verticalAlign=middle;fontSize=13;fontColor=#555555;whiteSpace=wrap;"


def title_case(enum_name):
    return " ".join(w.capitalize() for w in enum_name.split("_"))


class Box:
    def __init__(self, key, label, kind):
        self.key, self.label, self.kind = key, label, kind

    @property
    def cx(self): return self.x + self.w / 2
    @property
    def cy(self): return self.y + self.h / 2
    @property
    def top(self): return self.y
    @property
    def bottom(self): return self.y + self.h
    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w

    def port(self, fx, fy):
        return self.x + fx * self.w, self.y + fy * self.h


class Node(Box):
    def __init__(self, key, label, col, row, kind, rowh, colw=COLW, w=W):
        super().__init__(key, label, kind)
        cx = MX + col * colw
        if kind == "state":
            self.w, self.h = w, H
            self.x, self.y = cx - w / 2, MY + row * rowh
        elif kind == "choice":
            self.w = self.h = 40
            self.x, self.y = cx - 20, MY + row * rowh + (H - 40) / 2
        else:
            self.w = self.h = C
            self.x, self.y = cx - C / 2, MY + row * rowh + (H - C) / 2


class Group(Box):
    """Composite state drawn as a frame around its members (states or nested groups)."""

    def __init__(self, key, label, members, pad):
        super().__init__(key, label, "group")
        self.members = members
        l, t, r, b = pad
        self.x = min(m.x for m in members) - l
        self.y = min(m.y for m in members) - t
        self.w = max(m.right for m in members) + r - self.x
        self.h = max(m.bottom for m in members) + b - self.y

    def fx(self, x):
        return (x - self.x) / self.w

    def fy(self, y):
        return (y - self.y) / self.h


class SM:
    def __init__(self, name, title, subtitle, rowh=ROWH, colw=COLW, w=W):
        self.name, self.title, self.subtitle, self.rowh = name, title, subtitle, rowh
        self.colw, self.w = colw, w
        self.nodes, self.groups, self.edges = {}, {}, []

    def start(self, col, row):
        self.nodes["S"] = Node("S", "", col, row, "start", self.rowh, self.colw)
        return self.nodes["S"]

    def choice(self, key, col, row):
        """UML choice pseudo-state (diamond): outgoing transitions carry the guards."""
        self.nodes[key] = Node(key, "", col, row, "choice", self.rowh, self.colw)
        return self.nodes[key]

    def end(self, col, row):
        self.nodes["E"] = Node("E", "", col, row, "end", self.rowh, self.colw)
        return self.nodes["E"]

    def state(self, key, enum_name, col, row, cat=None):
        node = Node(key, title_case(enum_name), col, row, "state", self.rowh, self.colw, self.w)
        node.cat = cat or DEFAULT_CATEGORY[enum_name]
        self.nodes[key] = node
        return node

    def group(self, key, name, member_keys, pad=(70, 34, 70, 16)):
        members = [self.nodes.get(k) or self.groups[k] for k in member_keys]
        self.groups[key] = Group(key, name, members, pad)
        return self.groups[key]

    def box(self, key):
        return self.nodes.get(key) or self.groups[key]

    def edge(self, a, b, label="", pts=(), exit=None, entry=None, lseg=None, off=(0, 0)):
        """`lseg` = index of the polyline segment whose middle carries the label (default: whole-edge middle)."""
        self.edges.append(dict(a=a, b=b, label=label, pts=list(pts), exit=exit, entry=entry, lseg=lseg, off=off))

    def members(self, key):
        if key in self.nodes:
            return [key]
        out = []
        for m in self.groups[key].members:
            out += self.members(m.key)
        return out

    # ------------------------------------------------------------------ checks
    def polyline(self, e):
        a, b = self.box(e["a"]), self.box(e["b"])
        pts = e["pts"]
        if e["exit"]:
            p0 = a.port(*e["exit"])
        else:
            p0 = perimeter(a, pts[0] if pts else (b.cx, b.cy))
        if e["entry"]:
            p1 = b.port(*e["entry"])
        else:
            p1 = perimeter(b, pts[-1] if pts else p0)
        return [p0] + pts + [p1]

    def validate(self):
        keys = set(self.nodes)
        out = {k: [] for k in keys}
        for e in self.edges:
            assert e["b"] in self.nodes, f"{self.name}: edge into a group"
            for src in self.members(e["a"]):
                out[src].append(e["b"])
        inc = {k: 0 for k in keys}
        for ts in out.values():
            for t in ts:
                inc[t] += 1
        assert [k for k in keys if self.nodes[k].kind == "start"] == ["S"], "one start"
        assert [k for k in keys if self.nodes[k].kind == "end"] == ["E"], "one end"
        assert inc["S"] == 0 and not out["E"], "start has no incoming, end has no outgoing"
        deg, queue, seen = dict(inc), ["S"], 0
        while queue:
            k = queue.pop()
            seen += 1
            for t in out[k]:
                deg[t] -= 1
                if deg[t] == 0:
                    queue.append(t)
        assert seen == len(keys), f"{self.name}: cycle detected"

        def reach(src, adj):
            stack, got = [src], {src}
            while stack:
                for t in adj[stack.pop()]:
                    if t not in got:
                        got.add(t)
                        stack.append(t)
            return got
        rev = {k: [] for k in keys}
        for a, ts in out.items():
            for t in ts:
                rev[t].append(a)
        assert reach("S", out) == keys, f"{self.name}: unreachable {keys - reach('S', out)}"
        assert reach("E", rev) == keys, f"{self.name}: dead end {keys - reach('E', rev)}"
        segs = []
        for i, e in enumerate(self.edges):
            line = self.polyline(e)
            for p, q in zip(line, line[1:]):
                assert abs(p[0] - q[0]) < 0.01 or abs(p[1] - q[1]) < 0.01 or not e["pts"], \
                    f"{self.name}: diagonal {e['a']}->{e['b']}"
                for k, n in self.nodes.items():
                    if k in (e["a"], e["b"]):
                        continue
                    assert not seg_hits_rect(p, q, n), f"{self.name}: {e['a']}->{e['b']} crosses node {k}"
                segs.append((i, p, q))
        for x in range(len(segs)):
            for y in range(x + 1, len(segs)):
                i, p, q = segs[x]
                j, r, s = segs[y]
                if i != j and proper_cross(p, q, r, s):
                    ea, eb = self.edges[i], self.edges[j]
                    raise AssertionError(f"{self.name}: {ea['a']}->{ea['b']} crosses {eb['a']}->{eb['b']}")

    # ------------------------------------------------------------------ output
    def label_x(self, e):
        if e["lseg"] is None:
            return 0
        line = self.polyline(e)
        lens = [math.dist(p, q) for p, q in zip(line, line[1:])]
        k = e["lseg"] if e["lseg"] >= 0 else len(lens) + e["lseg"]
        t = sum(lens[:k]) + lens[k] / 2
        return round(2 * t / sum(lens) - 1, 4)

    def xml(self):
        cells, ids = [], {}
        boxes = list(self.nodes.values()) + list(self.groups.values())
        x0 = min(b.x for b in boxes)
        y0 = min([b.y for b in boxes] + [p[1] for e in self.edges for p in e["pts"]])
        cells.append(f'<mxCell id="t1" value="{esc(self.title)}" style="{TITLE}" vertex="1" parent="1">'
                     f'<mxGeometry x="{x0 - 40:.1f}" y="{y0 - 116:.1f}" width="1000" height="34" as="geometry"/>'
                     f'</mxCell>')
        cells.append(f'<mxCell id="t2" value="{esc(self.subtitle)}" style="{SUB}" vertex="1" parent="1">'
                     f'<mxGeometry x="{x0 - 40:.1f}" y="{y0 - 82:.1f}" width="1000" height="24" as="geometry"/>'
                     f'</mxCell>')
        used = [c for c in CATEGORIES if any(getattr(n, "cat", None) == c for n in self.nodes.values())]
        lx = x0 - 40
        for c in used:
            fill, stroke, text = CATEGORIES[c]
            cells.append(f'<mxCell id="lg_{c}" value="" style="{LEGEND_CHIP.format(fill=fill, stroke=stroke)}" '
                         f'vertex="1" parent="1"><mxGeometry x="{lx:.1f}" y="{y0 - 48:.1f}" width="26" height="16" '
                         f'as="geometry"/></mxCell>')
            cells.append(f'<mxCell id="lt_{c}" value="{esc(text)}" style="{LEGEND_TEXT}" vertex="1" parent="1">'
                         f'<mxGeometry x="{lx + 32:.1f}" y="{y0 - 50:.1f}" width="170" height="20" as="geometry"/>'
                         f'</mxCell>')
            lx += 32 + 7.2 * len(text) + 26
        # frames first (outer before inner) so they sit behind the states
        for k, g in sorted(self.groups.items(), key=lambda kv: -kv[1].w * kv[1].h):
            cid = ids[k] = f"g_{k}"
            cells.append(f'<mxCell id="{cid}" value="{esc(g.label)}" style="{GROUP}" vertex="1" parent="1">'
                         f'<mxGeometry x="{g.x:.1f}" y="{g.y:.1f}" width="{g.w:.1f}" height="{g.h:.1f}" '
                         f'as="geometry"/></mxCell>')
        for k, n in self.nodes.items():
            cid = ids[k] = f"n_{k}"
            if n.kind == "state":
                fill, stroke, _ = CATEGORIES[n.cat]
                style = STATE.format(fill=fill, stroke=stroke)
            elif n.kind == "choice":
                style = CHOICE
            else:
                style = START if n.kind == "start" else END
            cells.append(f'<mxCell id="{cid}" value="{esc(n.label)}" style="{style}" vertex="1" parent="1">'
                         f'<mxGeometry x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" '
                         f'as="geometry"/></mxCell>')
        for i, e in enumerate(self.edges):
            style = EDGE
            if e["exit"]:
                style += f"exitX={e['exit'][0]:.4f};exitY={e['exit'][1]:.4f};exitDx=0;exitDy=0;exitPerimeter=0;"
            if e["entry"]:
                style += f"entryX={e['entry'][0]:.4f};entryY={e['entry'][1]:.4f};entryDx=0;entryDy=0;entryPerimeter=0;"
            pts = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in e["pts"])
            arr = f'<Array as="points">{pts}</Array>' if pts else ""
            off = f'<mxPoint x="{e["off"][0]}" y="{e["off"][1]}" as="offset"/>' if e["off"] != (0, 0) else ""
            cells.append(f'<mxCell id="e{i}" value="{esc(e["label"])}" style="{style}" edge="1" parent="1" '
                         f'source="{ids[e["a"]]}" target="{ids[e["b"]]}">'
                         f'<mxGeometry x="{self.label_x(e)}" relative="1" as="geometry">{arr}{off}</mxGeometry>'
                         f'</mxCell>')
        return (f'<mxfile host="app.diagrams.net"><diagram name="{esc(self.title)}" id="{self.name}">'
                f'<mxGraphModel dx="1600" dy="1000" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
                f'arrows="1" fold="1" page="0" pageScale="1" pageWidth="1600" pageHeight="1200" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(cells)}</root></mxGraphModel>'
                f'</diagram></mxfile>')


def esc(s):
    return html.escape(s, quote=True)


def perimeter(n, toward):
    dx, dy = toward[0] - n.cx, toward[1] - n.cy
    if dx == 0 and dy == 0:
        return n.cx, n.cy
    if n.kind in ("start", "end"):
        d = math.hypot(dx, dy)
        return n.cx + dx / d * n.w / 2, n.cy + dy / d * n.h / 2
    sx = (n.w / 2) / abs(dx) if dx else float("inf")
    sy = (n.h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return n.cx + dx * s, n.cy + dy * s


def seg_hits_rect(p, q, n, pad=4):
    x0, y0, x1, y1 = n.x - pad, n.y - pad, n.right + pad, n.bottom + pad
    (ax, ay), (bx, by) = p, q
    if abs(ax - bx) < 0.01:
        return x0 < ax < x1 and max(min(ay, by), y0) < min(max(ay, by), y1)
    if abs(ay - by) < 0.01:
        return y0 < ay < y1 and max(min(ax, bx), x0) < min(max(ax, bx), x1)
    return False


def proper_cross(p, q, r, s):
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 1e-6) - (v < -1e-6)
    o1, o2, o3, o4 = orient(p, q, r), orient(p, q, s), orient(r, s, p), orient(r, s, q)
    return o1 * o2 < 0 and o3 * o4 < 0


def mid(above, below):
    return (above.bottom + below.top) / 2


def chain(m, col, row0, items, step=1.0):
    prev = "S"
    for i, (key, enum, label) in enumerate(items):
        m.state(key, enum, col, row0 + i * step)
        m.edge(prev, key, label)
        prev = key
    return prev


# ====================================================================== orders


def order_shape(m, first, first_label, to_storing, cancel_label, storing_to_completed):
    """Shared layout of the two order diagrams: first -> Storing -> Completed, with Canceled and Expired."""
    m.start(1, 0)
    a = m.state("A", first, 1, 1)
    sto = m.state("STO", "STORING", 1, 2)
    can = m.state("CAN", "CANCELED", 2, 2)
    exp = m.state("EXP", "EXPIRED", 0, 3)
    com = m.state("COM", "COMPLETED", 1, 4)
    e = m.end(1, 5)
    m.edge("S", "A", first_label)
    m.edge("A", "STO", to_storing)
    m.edge("A", "CAN", cancel_label, [(can.cx, a.cy)], lseg=0)
    m.edge("STO", "COM", storing_to_completed)
    m.edge("STO", "EXP", "Overdue, moved to storage", [(exp.cx, sto.cy)], lseg=0)
    m.edge("EXP", "COM", "Pay overdue fee & collect", [(exp.cx, com.cy)], lseg=1)
    m.edge("COM", "E")
    m.edge("CAN", "E", "", [(can.cx, e.cy)])
    return m


def locker_rental_order():
    m = SM("06a-state-machine-locker-rental-order", "State Machine Diagram — Locker Rental Order",
           "orders.status of SEND (send a parcel through a cell) and RENTAL (rent a cell by the hour) orders")
    return order_shape(m, "INITIALIZED", "Create send / rental order", "Pay & drop items",
                       "Cancel / unpaid timeout", "Pick up / end rental")


def drone_delivery_order():
    m = SM("06b-state-machine-drone-delivery-order", "State Machine Diagram — Drone Delivery Order",
           "orders.status of a DRONE_DELIVERY order · delivery steps in detail: Drone Delivery Stage diagram")
    return order_shape(m, "AWAITING_DISPATCH", "Create drone order", "Parcel delivered to cell",
                       "Cancel / timeout / delivery failed", "Receiver picks up")


def order():
    """Whole Order entity: orders.status for both types, plus orders.delivery_stage on the drone branch."""
    m = SM("06-state-machine-order", "State Machine Diagram — Order",
           "orders.status by orders.type · drone branch = orders.delivery_stage (Failed / Drop Reported: "
           "status Canceled) · grey frame = composite state", rowh=110)
    m.start(1, -1.4)
    ch = m.choice("CH", 1, -0.4)
    ini = m.state("INI", "INITIALIZED", 0, 1)
    rows = {"AWD": 1, "PAS": 2, "PUP": 3, "ACC": 4, "LAU": 5.35, "DEP": 6.35, "ENR": 7.35, "APP": 8.35,
            "ARR": 9.35, "RFP": 10.6}
    items = [("AWD", "AWAITING_DISPATCH", None),
             ("PAS", "PICKUP_ASSIGNED", "Technician takes pickup job"),
             ("PUP", "PICKED_UP", "Collect parcel (pickup code)"),
             ("ACC", "ACCEPTED", "Assign drone"),
             ("LAU", "LAUNCHING", "Load & launch"),
             *FLIGHT,
             ("RFP", "READY_FOR_PICKUP", "Parcel in cell, PIN sent")]
    prev = None
    for key, enum, label in items:
        m.state(key, enum, 2, rows[key])
        if prev:
            m.edge(prev, key, label)
        prev = key
    n = m.nodes
    sto = m.state("STO", "STORING", 0, 10.6)
    exp = m.state("EXP", "EXPIRED", 1, 11.7)
    com = m.state("COM", "COMPLETED", 1, 12.9)
    e = m.end(1, 14.0)
    can = m.state("CAN", "CANCELED", 1, 15.1)
    fai = m.state("FAI", "FAILED", 3, 12.9)
    drp = m.state("DRP", "DROP_REPORTED", 4, 12.9)
    fl = m.group("FL", "Flight", ["LAU", "DEP", "ENR", "APP", "ARR"], (45, 30, 45, 8))
    g = m.group("G", "Delivery In Progress", ["AWD", "PAS", "PUP", "ACC", "FL"], (25, 34, 25, 12))

    m.edge("S", "CH")
    m.edge("CH", "INI", "[Rental] Create order", [(ini.cx, ch.cy)], exit=(0, 0.5), lseg=0)
    m.edge("CH", "AWD", "[Drone Delivery] Create order", [(n["AWD"].cx, ch.cy)], exit=(1, 0.5), lseg=0)
    # rental branch
    m.edge("INI", "STO", "Pay & drop items")
    lane = ini.left - 60
    m.edge("INI", "CAN", "Cancel / unpaid timeout", [(lane, ini.cy), (lane, can.cy)], exit=(0, 0.5), lseg=1)
    m.edge("STO", "EXP", "Overdue → storage", [(exp.port(0.25, 0)[0], sto.cy)], exit=(1, 0.5), entry=(0.25, 0),
           lseg=0)
    m.edge("STO", "COM", "Pick up / end rental", [(sto.cx, com.cy)], lseg=0)
    # drone branch
    rfp = n["RFP"]
    m.edge("RFP", "EXP", "Overdue → storage", [(exp.port(0.75, 0)[0], rfp.cy)], exit=(0, 0.5), entry=(0.75, 0),
           lseg=0)
    m.edge("RFP", "COM", "Receiver picks up", [(rfp.cx, com.cy)], lseg=0)
    xr = drp.right + 100
    for key, dx, label in [("AWD", 0, "Customer cancels / unpaid"), ("PAS", 35, "Customer cancels"),
                           ("ACC", 70, "Cancel before launch")]:
        x = xr - dx
        m.edge(key, "CAN", label, [(x, n[key].cy), (x, can.cy)], exit=(1, 0.5), lseg=0)
    y = n["ARR"].cy
    m.edge("G", "FAI", "Delivery failed / timeout", [(fai.cx, y)], exit=(1, g.fy(y)), lseg=1)
    y = n["DEP"].cy
    m.edge("FL", "DRP", "Parcel dropped", [(drp.cx, y)], exit=(1, fl.fy(y)), lseg=1)
    # shared ends
    m.edge("EXP", "COM", "Pay fee & collect")
    m.edge("COM", "E")
    m.edge("CAN", "E")
    m.edge("FAI", "E", "", [(fai.cx, e.cy)])
    m.edge("DRP", "E", "", [(drp.cx, e.cy)])
    return m


# ====================================================================== drone delivery

FLIGHT = [
    ("DEP", "DEPARTED", "Take off"),
    ("ENR", "EN_ROUTE", "Leave source locker"),
    ("APP", "APPROACHING", "Near destination"),
    ("ARR", "ARRIVED", "Land at destination"),
]


def drone_delivery_stage():
    m = SM("06c-state-machine-drone-delivery-stage", "State Machine Diagram — Drone Delivery Stage",
           "orders.delivery_stage of a DRONE_DELIVERY order · grey frame = composite state "
           "(its outgoing transition applies to every state inside)", rowh=110)
    m.start(1, -0.7)
    rows = {"AWD": 1, "PAS": 2, "PUP": 3, "ACC": 4, "LAU": 5.35, "DEP": 6.35, "ENR": 7.35, "APP": 8.35,
            "ARR": 9.35, "RFP": 10.6}
    items = [
        ("AWD", "AWAITING_DISPATCH", "Create drone order"),
        ("PAS", "PICKUP_ASSIGNED", "Technician takes pickup job"),
        ("PUP", "PICKED_UP", "Collect parcel (pickup code)"),
        ("ACC", "ACCEPTED", "Assign drone"),
        ("LAU", "LAUNCHING", "Load & launch"),
        *FLIGHT,
        ("RFP", "READY_FOR_PICKUP", "Parcel in cell, PIN sent"),
    ]
    prev = "S"
    for key, enum, label in items:
        m.state(key, enum, 1, rows[key])
        m.edge(prev, key, label)
        prev = key
    n = m.nodes
    exp = m.state("EXP", "EXPIRED", 0, 11.6)
    com = m.state("COM", "COMPLETED", 1, 12.6)
    fai = m.state("FAI", "FAILED", 2, 12.6)
    drp = m.state("DRP", "DROP_REPORTED", 3, 12.6)
    can = m.state("CAN", "CANCELED", 4, 12.6)
    e = m.end(3, 13.7)
    fl = m.group("FL", "Flight", ["LAU", "DEP", "ENR", "APP", "ARR"], (45, 30, 45, 8))
    g = m.group("G", "Delivery In Progress", ["AWD", "PAS", "PUP", "ACC", "FL"], (25, 34, 25, 12))
    m.edge("RFP", "COM", "Receiver picks up")
    m.edge("RFP", "EXP", "Overdue, moved to storage", [(exp.cx, n["RFP"].cy)], lseg=0)
    m.edge("EXP", "COM", "Pay overdue fee & collect", [(exp.cx, com.cy)], lseg=1)
    for key, port, label in [("AWD", 0.8, "Customer cancels / unpaid"),
                             ("PAS", 0.5, "Customer cancels"),
                             ("ACC", 0.2, "Cancel before launch")]:
        x = can.port(port, 0)[0]
        m.edge(key, "CAN", label, [(x, n[key].cy)], exit=(1, 0.5), entry=(port, 0), lseg=0)
    y = n["ARR"].cy
    m.edge("G", "FAI", "Delivery failed / timeout", [(fai.cx, y)], exit=(1, g.fy(y)), lseg=1)
    y = n["DEP"].cy
    m.edge("FL", "DRP", "Parcel dropped", [(drp.cx, y)], exit=(1, fl.fy(y)), lseg=1)
    m.edge("DRP", "E")
    m.edge("FAI", "E", "", [(fai.cx, e.cy)])
    m.edge("CAN", "E", "", [(can.cx, e.cy)])
    below = e.bottom + 40
    m.edge("COM", "E", "", [(com.cx, below), (e.cx, below)])
    return m


def drone_pickup():
    m = SM("06d-state-machine-drone-pickup", "State Machine Diagram — Drone Pickup",
           "drone_pickups.status · technician collects the parcel at the sender's address · "
           "grey frame = composite state")
    m.start(1, -0.7)
    sea = m.state("SEA", "SEARCHING", 1, 1)
    m.state("OFF", "OFFERED", 1, 2)
    acc = m.state("ACC", "ACCEPTED", 1, 3)
    m.state("PUP", "PICKED_UP", 1, 4, cat="success")
    fai = m.state("FAI", "FAILED", 2.3, 4)
    can = m.state("CAN", "CANCELED", 3.3, 2)
    e = m.end(1, 5)
    b = m.group("B", "Before Pickup", ["SEA", "OFF", "ACC"], (95, 32, 95, 14))
    m.edge("S", "SEA", "Order paid")
    m.edge("SEA", "OFF", "Offer to nearest technician")
    m.edge("OFF", "ACC", "Technician accepts")
    lane = sea.left - 70
    m.edge("SEA", "ACC", "Admin assigns", [(lane, sea.cy), (lane, acc.cy)], lseg=1)
    m.edge("ACC", "PUP", "Parcel collected")
    m.edge("ACC", "FAI", "Pickup failed", [(fai.cx, acc.cy)], lseg=0)
    m.edge("B", "CAN", "Order closed", exit=(1, b.fy(can.cy)))
    m.edge("PUP", "E")
    m.edge("FAI", "E", "", [(fai.cx, e.cy)])
    below = e.bottom + 40
    m.edge("CAN", "E", "", [(can.cx, below), (e.cx, below)])
    return m


def drone_mission():
    m = SM("06e-state-machine-drone-mission", "State Machine Diagram — Drone Mission",
           "drone_missions.status · created when a drone technician accepts the order with a drone · "
           "grey frame = composite state", rowh=110)
    m.start(1, -0.7)
    rows = {"AWL": 1, "RTL": 2, "LAU": 3.4, "DEP": 4.4, "ENR": 5.4, "APP": 6.4, "ARR": 7.4, "DPO": 8.75}
    items = [
        ("AWL", "AWAITING_LOADING", "Accept order, reserve drone"),
        ("RTL", "READY_TO_LAUNCH", "Confirm loading"),
        ("LAU", "LAUNCHING", "Launch"),
        *FLIGHT,
        ("DPO", "DEPOSITED", "Parcel in cell"),
    ]
    prev = "S"
    for key, enum, label in items:
        m.state(key, enum, 1, rows[key])
        m.edge(prev, key, label)
        prev = key
    n = m.nodes
    fai = m.state("FAI", "FAILED", 2, 9.9)
    drp = m.state("DRP", "DROP_REPORTED", 3, 9.9)
    can = m.state("CAN", "CANCELED", 4, 9.9)
    e = m.end(3, 11)
    bl = m.group("BL", "Before Launch", ["AWL", "RTL"], (45, 30, 45, 10))
    fl = m.group("FL", "Flight", ["LAU", "DEP", "ENR", "APP", "ARR"], (45, 30, 45, 8))
    o = m.group("O", "Mission Open", ["BL", "FL"], (25, 32, 25, 12))
    y = n["AWL"].cy
    m.edge("BL", "CAN", "Cancel before launch", [(can.cx, y)], exit=(1, bl.fy(y)), lseg=0)
    y = n["ARR"].cy
    m.edge("O", "FAI", "Delivery failed / timeout", [(fai.cx, y)], exit=(1, o.fy(y)), lseg=1)
    y = n["DEP"].cy
    m.edge("FL", "DRP", "Parcel dropped", [(drp.cx, y)], exit=(1, fl.fy(y)), lseg=1)
    m.edge("DRP", "E")
    m.edge("FAI", "E", "", [(fai.cx, e.cy)])
    m.edge("CAN", "E", "", [(can.cx, e.cy)])
    below = e.bottom + 40
    m.edge("DPO", "E", "", [(n["DPO"].cx, below), (e.cx, below)])
    return m


def drone_delivery_session():
    m = SM("06f-state-machine-drone-delivery-session", "State Machine Diagram — Drone Delivery Session",
           "drone_delivery_sessions.state · drone ↔ locker hand-off at the destination cell (sliding lid) · "
           "grey frame = composite state")
    m.start(1, -0.7)
    olr = m.state("OLR", "OPEN_LID_REQUESTED", 1, 1)
    m.state("LOG", "LID_OPENING", 1, 2)
    lod = m.state("LOD", "LID_OPENED", 1, 3)
    clr = m.state("CLR", "CLOSE_LID_REQUESTED", 1, 4)
    tst = m.state("TST", "TEST_COMPLETED", 0, 5)
    m.state("RFP", "READY_FOR_PICKUP", 1, 5, cat="success")
    abt = m.state("ABT", "ABORTED", 2, 5)
    lcf = m.state("LCF", "LID_CLOSE_FAILED", 3, 5)
    lof = m.state("LOF", "LID_OPEN_FAILED", 4, 3)
    e = m.end(1, 6.3)
    op = m.group("OP", "Opening Lid", ["OLR", "LOG"], (100, 30, 100, 12))
    m.edge("S", "OLR", "ArUco marker matched")
    m.edge("OLR", "LOG", "Locker acknowledges")
    m.edge("LOG", "LOD", "Lid open")
    lane = olr.left - 70
    m.edge("OLR", "LOD", "Lid open<br>(no ack)", [(lane, olr.cy), (lane, lod.cy)], lseg=1)
    m.edge("LOD", "CLR", "Parcel released")
    m.edge("CLR", "RFP", "Lid closed")
    m.edge("CLR", "TST", "Lid closed (test mode)", [(tst.cx, clr.cy)], lseg=0)
    y = clr.port(1, 0.7)[1]
    m.edge("CLR", "ABT", "Order not advanced", [(abt.cx, y)], exit=(1, 0.7), lseg=1)
    y = clr.port(1, 0.3)[1]
    m.edge("CLR", "LCF", "Close failed", [(lcf.cx, y)], exit=(1, 0.3), lseg=1)
    y = olr.cy
    m.edge("OP", "LOF", "Open failed / expired", [(lof.cx, y)], exit=(1, op.fy(y)), lseg=0)
    m.edge("RFP", "E")
    m.edge("TST", "E", "", [(tst.cx, e.cy)])
    m.edge("ABT", "E", "", [(abt.cx, e.cy)])
    below = e.bottom + 40
    m.edge("LCF", "E", "", [(lcf.cx, below), (e.cx, below)])
    m.edge("LOF", "E", "", [(lof.cx, below), (e.cx, below)])
    return m


# ====================================================================== lockers & drones


def locker_box():
    m = SM("06g-state-machine-locker-box", "State Machine Diagram — Locker Box",
           "locker_boxes.status · a transition into the final node ends one cycle of the cell "
           "(→ the state it returns to)")
    m.start(2, 0)
    av = m.state("AV", "AVAILABLE", 2, 1)
    res = m.state("RES", "RESERVED", 0, 2)
    cle = m.state("CLE", "CLEANING", 3, 2)
    oos = m.state("OOS", "OUT_OF_SERVICE", 4, 2)
    occ = m.state("OCC", "OCCUPIED", 0, 3)
    pen = m.state("PEN", "PENDING_CHECK", 1, 4)
    fau = m.state("FAU", "FAULT", 2, 5)
    e = m.end(2, 6)
    below = e.bottom + 50
    m.edge("S", "AV", "Add cell")
    m.edge("AV", "RES", "Order created", [(res.cx, av.cy)], lseg=0)
    m.edge("RES", "OCC", "Items dropped")
    lane = res.left - 60
    m.edge("RES", "E", "Order canceled (→ Available)",
           [(lane, res.cy), (lane, below), (e.cx, below)], exit=(0, 0.5), lseg=2)
    m.edge("OCC", "E", "Order closed<br>(→ Available)", [(occ.cx, e.cy)], lseg=0)
    y_pa = mid(occ, pen)
    m.edge("AV", "PEN", "Customer reports fault",
           [(av.port(0.25, 1)[0], y_pa), (pen.port(0.75, 0)[0], y_pa)], exit=(0.25, 1), entry=(0.75, 0), lseg=0)
    m.edge("OCC", "PEN", "Customer reports fault",
           [(pen.port(0.25, 0)[0], occ.cy)], exit=(1, 0.5), entry=(0.25, 0), lseg=0)
    m.edge("PEN", "FAU", "Fault confirmed", [(pen.cx, fau.cy)], lseg=1)
    x = pen.port(0.25, 1)[0]
    m.edge("PEN", "E", "Report rejected<br>(→ previous)", [(x, e.cy)], exit=(0.25, 1), lseg=0, off=(-60, 0))
    m.edge("AV", "FAU", "Fault reported")
    m.edge("FAU", "E", "Ticket resolved (→ previous)")
    m.edge("AV", "CLE", "Start cleaning", [(cle.cx, av.port(1, 0.7)[1])], exit=(1, 0.7), lseg=0)
    m.edge("AV", "OOS", "Take out of service", [(oos.cx, av.port(1, 0.3)[1])], exit=(1, 0.3), lseg=0)
    m.edge("CLE", "E", "Back to service<br>(→ Available)", [(cle.cx, e.cy)], lseg=0)
    m.edge("OOS", "E", "Back to service<br>(→ Available)", [(oos.cx, below), (e.cx, below)], lseg=0)
    return m


def locker():
    m = SM("06h-state-machine-locker", "State Machine Diagram — Locker",
           "lockers.status · final node = locker station deleted (soft delete)")
    m.start(1, 0)
    act = m.state("ACT", "ACTIVE", 1, 1)
    mai = m.state("MAI", "MAINTENANCE", 0, 2)
    ina = m.state("INA", "INACTIVE", 2, 2)
    e = m.end(1, 3)
    m.edge("S", "ACT", "Create locker")
    m.edge("ACT", "MAI", "Enable maintenance", [(mai.cx, act.cy)], lseg=0)
    m.edge("ACT", "INA", "Set inactive (API)", [(ina.cx, act.cy)], lseg=0)
    m.edge("ACT", "E", "Delete locker")
    m.edge("MAI", "E", "Delete locker", [(mai.cx, e.cy)], lseg=1)
    m.edge("INA", "E", "Delete locker", [(ina.cx, e.cy)], lseg=1)
    return m


def drone():
    m = SM("06i-state-machine-drone", "State Machine Diagram — Drone",
           "drone_units.status · grey frame = composite state · a transition into the final node ends one "
           "cycle of the drone (→ the state it returns to)")
    m.start(1, -0.7)
    idl = m.state("IDL", "IDLE", 1, 1)
    m.state("CHG", "CHARGING", 2, 1)
    res = m.state("RES", "RESERVED", 0, 2)
    fly = m.state("FLY", "IN_FLIGHT", 0, 3)
    fau = m.state("FAU", "FAULT", 1.5, 3)
    mai = m.state("MAI", "MAINTENANCE", 1.5, 4)
    e = m.end(1, 5)
    a = m.group("A", "In Service", ["IDL", "CHG"], (30, 30, 30, 14))
    b = m.group("B", "On Mission", ["RES", "FLY"], (30, 30, 30, 12))
    m.edge("S", "IDL", "Add drone")
    m.edge("IDL", "CHG", "Charge")
    m.edge("IDL", "RES", "Order accepted", [(res.cx, idl.cy)], lseg=0)
    m.edge("RES", "FLY", "Launch")
    m.edge("FLY", "E", "Mission done (→ Idle)", [(fly.cx, e.cy)], lseg=1)
    m.edge("A", "FAU", "Fault reported", exit=(a.fx(fau.cx), 1))
    m.edge("B", "FAU", "Fault / flight failed", exit=(1, b.fy(fau.cy)))
    lane = MX + 3 * COLW
    m.edge("A", "MAI", "Set maintenance", [(lane, idl.cy), (lane, mai.cy)], exit=(1, a.fy(idl.cy)), lseg=1)
    m.edge("FAU", "MAI", "Set maintenance")
    y = fau.port(0, 0.8)[1]
    m.edge("FAU", "E", "Ticket resolved<br>(→ Idle)", [(e.cx, y)], exit=(0, 0.8), lseg=1)
    m.edge("MAI", "E", "Done (→ Idle)<br>or deleted", [(mai.cx, e.cy)], lseg=0)
    return m


def incident_report():
    m = SM("06j-state-machine-incident-report", "State Machine Diagram — Incident Report",
           "locker_reports.status · locker / cell / drone incident tickets · grey frame = composite state")
    s = m.start(1, -0.7)
    m.state("OPN", "OPEN", 1, 1)
    ipr = m.state("IPR", "IN_PROGRESS", 1, 2)
    res = m.state("RES", "RESOLVED", 0.6, 3.5)
    rej = m.state("REJ", "REJECTED", 1.4, 3.5)
    e = m.end(1, 4.6)
    t = m.group("T", "Open Ticket", ["OPN", "IPR"], (75, 30, 75, 14))
    m.edge("S", "OPN", "Report incident")
    lane = t.right + 90
    m.edge("S", "IPR", "Auto-assigned<br>report", [(lane, s.cy), (lane, ipr.cy)], lseg=1)
    m.edge("OPN", "IPR", "Claim / assign")
    m.edge("T", "RES", "Repair done", exit=(t.fx(res.cx), 1))
    m.edge("T", "REJ", "Rejected", exit=(t.fx(rej.cx), 1))
    m.edge("RES", "E", "", [(res.cx, e.cy)])
    m.edge("REJ", "E", "", [(rej.cx, e.cy)])
    return m


def drone_parcel_incident():
    m = SM("06k-state-machine-drone-parcel-incident", "State Machine Diagram — Drone Parcel Incident",
           "drone_parcel_incidents.status · parcel dropped during a drone flight")
    m.start(1, 0)
    chain(m, 1, 1, [
        ("REP", "REPORTED", "Parcel drop reported"),
        ("INV", "INVESTIGATING", "Delivery stopped"),
        ("RIP", "RECOVERY_IN_PROGRESS", "Start searching"),
        ("AAR", "AWAITING_ADMIN_REVIEW", "Search result submitted"),
        ("ACR", "AWAITING_CUSTOMER_RESPONSE", "Proposal sent"),
        ("RSP", "RESOLUTION_IN_PROGRESS", "Customer accepts"),
        ("RSD", "RESOLVED", "Resolution done"),
    ])
    n = m.nodes
    mir = m.state("MIR", "MANUAL_INTERVENTION_REQUIRED", 2.1, 3)
    dis = m.state("DIS", "DISPUTED", 0, 7)
    e = m.end(1, 8)
    m.edge("INV", "MIR", "Return flight failed", [(mir.cx, n["INV"].cy)], lseg=0)
    m.edge("MIR", "AAR", "Drone back", [(mir.cx, n["AAR"].cy)], lseg=0)
    m.edge("ACR", "DIS", "Review requested", [(dis.cx, n["ACR"].cy)], lseg=0)
    m.edge("RSD", "E")
    m.edge("DIS", "E", "New proposal<br>(→ Awaiting Customer Response)", [(dis.cx, e.cy)], lseg=1)
    return m


def drone_return_flight():
    m = SM("06l-state-machine-drone-return-flight", "State Machine Diagram — Drone Return Flight",
           "drone_parcel_incidents.return_flight_status · drone flying back after a parcel drop · "
           "grey frame = composite state")
    m.start(1, -0.7)
    m.state("RRQ", "RETURN_REQUESTED", 1, 1)
    cac = m.state("CAC", "COMMAND_ACCEPTED", 1, 2)
    m.state("RET", "RETURNING", 1, 3)
    fai = m.state("FAI", "FAILED", 0, 4.4)
    mir = m.state("MIR", "MANUAL_INTERVENTION_REQUIRED", 2, 4.4)
    com = m.state("COM", "COMPLETED", 1, 5.4)
    m.end(1, 6.4)
    p = m.group("P", "Return In Progress", ["RRQ", "CAC", "RET"], (60, 30, 60, 14))
    m.edge("S", "RRQ", "Parcel drop reported")
    m.edge("RRQ", "CAC", "Command accepted")
    m.edge("CAC", "RET", "Flying back")
    m.edge("P", "FAI", "Command failed", [(fai.cx, cac.cy)], exit=(0, p.fy(cac.cy)), lseg=0)
    m.edge("P", "MIR", "Needs manual control", [(mir.cx, cac.cy)], exit=(1, p.fy(cac.cy)), lseg=0)
    m.edge("RET", "COM", "Drone back")
    x = com.port(0.85, 0)[0]
    m.edge("P", "COM", "Admin confirms", exit=(p.fx(x), 1), entry=(0.85, 0), off=(55, 0))
    m.edge("FAI", "COM", "Admin confirms", [(fai.cx, com.cy)], lseg=1)
    m.edge("MIR", "COM", "Admin confirms", [(mir.cx, com.cy)], lseg=1)
    m.edge("COM", "E")
    return m


# ====================================================================== money & accounts


def payment():
    m = SM("06m-state-machine-payment", "State Machine Diagram — Payment",
           "payments.status · VietQR bank transfer through SePay")
    m.start(1, 0)
    pen = m.state("PEN", "PENDING", 1, 1)
    fai = m.state("FAI", "FAILED", 2, 2)
    com = m.state("COM", "COMPLETED", 1, 3)
    e = m.end(1, 4)
    m.edge("S", "PEN", "Pay via VietQR")
    m.edge("PEN", "COM", "Transfer confirmed")
    m.edge("PEN", "FAI", "Admin marks failed", [(fai.cx, pen.cy)], lseg=0)
    m.edge("FAI", "COM", "Admin marks completed", [(fai.cx, com.cy)], lseg=1)
    lane = fai.right + 60
    m.edge("FAI", "E", "", [(lane, fai.cy), (lane, e.cy)], exit=(1, 0.5))
    m.edge("COM", "E")
    return m


def refund_request():
    m = SM("06n-state-machine-refund-request", "State Machine Diagram — Refund Request",
           "refunds.status · money returned to the customer's bank account by an admin transfer")
    m.start(1, 0)
    pen = m.state("PEN", "PENDING", 1, 1)
    com = m.state("COM", "COMPLETED", 0, 2)
    rej = m.state("REJ", "REJECTED", 2, 2)
    e = m.end(1, 3)
    m.edge("S", "PEN", "Refund requested")
    m.edge("PEN", "COM", "Admin approves & transfers", [(com.cx, pen.cy)], lseg=0)
    m.edge("PEN", "REJ", "Admin rejects", [(rej.cx, pen.cy)], lseg=0)
    m.edge("COM", "E", "", [(com.cx, e.cy)])
    m.edge("REJ", "E", "", [(rej.cx, e.cy)])
    return m


def account():
    m = SM("06o-state-machine-account", "State Machine Diagram — Account",
           "auth_accounts.status · customer and staff login accounts")
    m.start(1, 0)
    act = m.state("ACT", "ACTIVE", 1, 1)
    ina = m.state("INA", "INACTIVE", 0, 2)
    dele = m.state("DEL", "DELETED", 1, 3)
    m.end(1, 4)
    m.edge("S", "ACT", "Sign up / staff created")
    m.edge("ACT", "INA", "Admin locks", [(ina.cx, act.cy)], lseg=0)
    m.edge("ACT", "DEL", "Admin deletes")
    m.edge("INA", "DEL", "Admin deletes", [(ina.cx, dele.cy)], lseg=1)
    m.edge("DEL", "E")
    return m


def kiosk_login_session():
    m = SM("06p-state-machine-kiosk-login-session", "State Machine Diagram — Kiosk Login Session",
           "QR login at the kiosk (in-memory session in auth-service) · grey frame = composite state")
    m.start(1, -0.7)
    pen = m.state("PEN", "PENDING", 1, 1)
    m.state("CNF", "CONFIRMED", 1, 2)
    exp = m.state("EXP", "EXPIRED", 0, 3.4, cat="failure")
    m.state("CON", "CONSUMED", 1, 3.4)
    can = m.state("CAN", "CANCELLED", 2, 3.4)
    e = m.end(1, 4.5)
    q = m.group("Q", "Waiting For Login", ["PEN", "CNF"], (60, 30, 60, 14))
    m.edge("S", "PEN", "Kiosk shows QR")
    m.edge("PEN", "CNF", "Confirmed in app")
    m.edge("CNF", "CON", "Kiosk gets session")
    m.edge("Q", "EXP", "QR expired", [(exp.cx, pen.cy)], exit=(0, q.fy(pen.cy)), lseg=0)
    m.edge("Q", "CAN", "Canceled", [(can.cx, pen.cy)], exit=(1, q.fy(pen.cy)), lseg=0)
    m.edge("CON", "E")
    m.edge("EXP", "E", "", [(exp.cx, e.cy)])
    m.edge("CAN", "E", "", [(can.cx, e.cy)])
    return m


def order_by_type():
    """Order entity at status level, branched by type; the drone branch is detailed in drone_delivery_order_full."""
    m = SM("06-1-state-machine-order", "State Machine Diagram — Order",
           "orders.status by orders.type · drone delivery stages in detail: Drone Delivery Order diagram")
    m.start(1, -1.4)
    ch = m.choice("CH", 1, -0.4)
    ini = m.state("INI", "INITIALIZED", 0, 1)
    awd = m.state("AWD", "AWAITING_DISPATCH", 2, 1)
    sto = m.state("STO", "STORING", 1, 2.2)
    exp = m.state("EXP", "EXPIRED", 0, 3.4)
    com = m.state("COM", "COMPLETED", 1, 4.6)
    m.end(1, 5.7)
    can = m.state("CAN", "CANCELED", 1, 6.8)
    m.edge("S", "CH")
    m.edge("CH", "INI", "[Rental] Create order", [(ini.cx, ch.cy)], exit=(0, 0.5), lseg=0)
    m.edge("CH", "AWD", "[Drone Delivery] Create order", [(awd.cx, ch.cy)], exit=(1, 0.5), lseg=0)
    m.edge("INI", "STO", "Pay & drop items", [(ini.cx, sto.cy)], lseg=0)
    m.edge("AWD", "STO", "Parcel delivered to cell", [(awd.cx, sto.cy)], lseg=0)
    lane = ini.left - 60
    m.edge("INI", "CAN", "Cancel / unpaid timeout", [(lane, ini.cy), (lane, can.cy)], exit=(0, 0.5), lseg=1)
    lane = awd.right + 60
    m.edge("AWD", "CAN", "Cancel / delivery failed /<br>parcel dropped", [(lane, awd.cy), (lane, can.cy)],
           exit=(1, 0.5), lseg=1)
    x = sto.port(0.2, 1)[0]
    m.edge("STO", "EXP", "Overdue → storage", [(x, exp.cy)], exit=(0.2, 1), lseg=1)
    m.edge("STO", "COM", "Picked up / rental ended", off=(45, 0))
    m.edge("EXP", "COM", "Pay fee & collect", [(exp.cx, com.cy)], lseg=0)
    m.edge("COM", "E")
    m.edge("CAN", "E")
    return m


def drone_delivery_order_full():
    """Drone delivery order on its own (orders.delivery_stage), laid out left-to-right for a landscape page."""
    m = SM("06-2-state-machine-drone-delivery-order", "State Machine Diagram — Drone Delivery Order",
           "orders.delivery_stage (type DRONE_DELIVERY) · Ready For Pickup = status Storing, Failed / Drop Reported = "
           "status Canceled · grey frame = composite state",
           rowh=190, colw=330, w=210)
    m.start(-0.75, 1)
    row1 = [("AWD", "AWAITING_DISPATCH"), ("PAS", "PICKUP_ASSIGNED"), ("PUP", "PICKED_UP"), ("ACC", "ACCEPTED")]
    row2 = [("LAU", "LAUNCHING"), ("DEP", "DEPARTED"), ("ENR", "EN_ROUTE"), ("APP", "APPROACHING"),
            ("ARR", "ARRIVED")]
    for i, (k, enum) in enumerate(row1):
        m.state(k, enum, i, 1)
    for i, (k, enum) in enumerate(row2):
        m.state(k, enum, i, 2.3)
    n = m.nodes
    rfp = m.state("RFP", "READY_FOR_PICKUP", 4, 3.6)
    exp = m.state("EXP", "EXPIRED", 3, 3.6)
    com = m.state("COM", "COMPLETED", 3.5, 4.8)
    e = m.end(3.5, 5.9)
    can = m.state("CAN", "CANCELED", 5.3, 1)
    drp = m.state("DRP", "DROP_REPORTED", 5.3, 2.3)
    fai = m.state("FAI", "FAILED", 5.3, 3.6)
    fl = m.group("FL", "Flight", [k for k, _ in row2], (35, 30, 35, 10))
    g = m.group("G", "Delivery In Progress", ["AWD", "PAS", "PUP", "ACC", "FL"], (25, 34, 25, 14))

    m.edge("S", "AWD", "Create<br>order")
    m.edge("AWD", "PAS", "Technician takes<br>pickup job")
    m.edge("PAS", "PUP", "Collect parcel<br>(pickup code)")
    m.edge("PUP", "ACC", "Assign<br>drone")
    acc, lau = n["ACC"], n["LAU"]
    y_mid = (acc.bottom + fl.top) / 2
    m.edge("ACC", "LAU", "Load & launch", [(acc.cx, y_mid), (lau.cx, y_mid)], lseg=1)
    m.edge("LAU", "DEP", "Take off")
    m.edge("DEP", "ENR", "Leave<br>source locker")
    m.edge("ENR", "APP", "Near<br>destination")
    m.edge("APP", "ARR", "Land at<br>destination")
    m.edge("ARR", "RFP", "Parcel in cell,<br>PIN sent")
    m.edge("RFP", "EXP", "Overdue →<br>storage")
    m.edge("RFP", "COM", "Receiver picks up", [(rfp.cx, com.cy)], lseg=0)
    m.edge("EXP", "COM", "Pay fee<br>& collect", [(exp.cx, com.cy)], lseg=0)
    m.edge("COM", "E")
    # cancels: Awaiting Dispatch / Pickup Assigned go over the top, Accepted straight right
    top = g.top
    ad, pas = n["AWD"], n["PAS"]
    xa, xp = can.port(0.7, 0)[0], can.port(0.3, 0)[0]
    m.edge("AWD", "CAN", "Customer cancels / unpaid", [(ad.cx, top - 50), (xa, top - 50)], entry=(0.7, 0), lseg=1)
    m.edge("PAS", "CAN", "Customer cancels", [(pas.cx, top - 25), (xp, top - 25)], entry=(0.3, 0), lseg=1)
    m.edge("ACC", "CAN", "Cancel before launch")
    y = n["ARR"].cy
    m.edge("FL", "DRP", "Parcel<br>dropped", exit=(1, fl.fy(y)))
    x = (fl.right + g.right) / 2
    m.edge("G", "FAI", "Delivery failed /<br>timeout", [(x, fai.cy)], exit=(g.fx(x), 1), lseg=1)
    m.edge("FAI", "E", "", [(fai.cx, e.cy)])
    lane = drp.right + 45
    m.edge("DRP", "E", "", [(lane, drp.cy), (lane, e.cy)], exit=(1, 0.5))
    lane = can.right + 85
    m.edge("CAN", "E", "", [(lane, can.cy), (lane, e.cy)], exit=(1, 0.5))
    return m


ALL = [order_by_type, drone_delivery_order_full, order, locker_rental_order, drone_delivery_order, drone_delivery_stage, drone_pickup, drone_mission,
       drone_delivery_session, locker_box, locker, drone, incident_report, drone_parcel_incident,
       drone_return_flight, payment, refund_request, account, kiosk_login_session]


def render_png(sm, path_xml, png):
    viewer = os.environ.get("VIEWER_JS") or os.path.join(HERE, "viewer-static.min.js")
    chrome = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    boxes = list(sm.nodes.values()) + list(sm.groups.values())
    w = int(max(b.right for b in boxes) - min(b.x for b in boxes) + 900)
    h = int(max(b.bottom for b in boxes) - min(b.y for b in boxes) + 350)
    cfg = {"xml": open(path_xml, encoding="utf-8").read(), "toolbar": "", "highlight": "none", "nav": False,
           "resize": False, "zoom": 1, "border": 30, "lightbox": False}
    page = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}</style>'
            f'</head><body><div class="mxgraph" style="width:{w}px" '
            f'data-mxgraph="{html.escape(json.dumps(cfg), quote=True)}"></div>'
            f'<script src="file:///{viewer.replace(os.sep, "/")}"></script></body></html>')
    hp = png[:-4] + ".html"
    open(hp, "w", encoding="utf-8").write(page)
    try:
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--force-device-scale-factor=1", f"--window-size={w},{h}", "--virtual-time-budget=20000",
                        f"--screenshot={png}", "file:///" + hp.replace(os.sep, "/")],
                       check=True, capture_output=True, timeout=180)
    finally:
        os.remove(hp)


def main():
    png_dir = sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else None
    built = [build() for build in ALL]
    for sm in built:
        sm.validate()
    for sm in built:
        path = os.path.join(OUT, sm.name + ".drawio")
        with open(path, "w", encoding="utf-8") as f:
            f.write(sm.xml())
        print("ok", sm.name, f"states={sum(n.kind == 'state' for n in sm.nodes.values())}",
              f"transitions={len(sm.edges)}")
        if png_dir:
            os.makedirs(png_dir, exist_ok=True)
            render_png(sm, path, os.path.join(png_dir, sm.name + ".png"))


if __name__ == "__main__":
    main()
