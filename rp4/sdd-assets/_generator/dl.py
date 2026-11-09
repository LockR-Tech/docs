"""Small draw.io (mxGraph) builder for the SDD diagrams: packages, classes, tables, sequences."""
import html, itertools, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "drawio")
DRAWIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawio")


def esc(s):
    return html.escape(s, quote=True)


def tw(text, size=11, bold=False):
    """Rough pixel width of a single line of Helvetica text."""
    w = 0.0
    for ch in text:
        if ch in "il.,:;'|!()[] ":
            w += 0.32
        elif ch in "mwMW@":
            w += 0.9
        elif ch.isupper():
            w += 0.68
        else:
            w += 0.56
    return w * size * (0.97 if bold else 0.9)


class Diagram:
    def __init__(self, name):
        self.name = name
        self.cells = []
        self._ids = itertools.count(2)

    def nid(self):
        return f"c{next(self._ids)}"

    def v(self, label, x, y, w, h, style, parent="1", cid=None):
        cid = cid or self.nid()
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
        return cid

    def e(self, src, tgt, style, label="", pts=(), sp=None, tp=None, parent="1"):
        cid = self.nid()
        p = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in pts)
        arr = f'<Array as="points">{p}</Array>' if pts else ""
        s = f'<mxPoint x="{sp[0]:.1f}" y="{sp[1]:.1f}" as="sourcePoint"/>' if sp else ""
        t = f'<mxPoint x="{tp[0]:.1f}" y="{tp[1]:.1f}" as="targetPoint"/>' if tp else ""
        st = f' source="{src}"' if src else ""
        tt = f' target="{tgt}"' if tgt else ""
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{style}" edge="1" parent="{parent}"{st}{tt}>'
            f'<mxGeometry relative="1" as="geometry">{s}{t}{arr}</mxGeometry></mxCell>')
        return cid

    def save(self):
        os.makedirs(OUT, exist_ok=True)
        os.makedirs(DRAWIO_DIR, exist_ok=True)
        xml = (f'<mxfile host="drawio"><diagram name="{esc(self.name)}" id="{self.name}">'
               f'<mxGraphModel grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" '
               f'pageScale="1" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
               + "".join(self.cells) + '</root></mxGraphModel></diagram></mxfile>')
        path = os.path.join(OUT, self.name + ".drawio")
        open(path, "w", encoding="utf-8").write(xml)
        drawio_path = os.path.join(DRAWIO_DIR, self.name + ".drawio")
        open(drawio_path, "w", encoding="utf-8").write(xml)
        return path


# ---------------------------------------------------------------- packages
PKG_FRAME = ("shape=folder;tabWidth=120;tabHeight=28;tabPosition=left;html=1;whiteSpace=wrap;fillColor=#dae8fc;"
             "strokeColor=#6c8ebf;verticalAlign=top;fontStyle=1;fontSize=18;spacingTop=34;")
PKG_GROUP = ("shape=folder;tabWidth=50;tabHeight=20;tabPosition=left;html=1;whiteSpace=wrap;fillColor=#fff2cc;"
             "strokeColor=#d6b656;verticalAlign=top;fontStyle=1;fontSize=13;spacingTop=22;")
PKG = ("shape=folder;tabWidth=32;tabHeight=14;tabPosition=left;html=1;whiteSpace=wrap;fillColor=#fff2cc;"
       "strokeColor=#d6b656;fontStyle=1;fontSize=12;spacingTop=12;")
DEP = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;endArrow=open;endSize=9;strokeColor=#333333;"
       "jettySize=auto;orthogonalLoop=1;")

# UML notation: a package that shows its contents carries its name in the tab; a package shown without
# contents carries its name in the body; a file / module inside a package is a plain packaged element.
TAB_H, TAB_H_FRAME = 22, 30


def pkg_tab_style(label, frame=False):
    size, th = (16, TAB_H_FRAME) if frame else (13, TAB_H)
    fill, stroke = ("#dae8fc", "#6c8ebf") if frame else ("#fff2cc", "#d6b656")
    tab = int(tw(label, size, True) + 22)
    return (f"shape=folder;tabWidth={tab};tabHeight={th};tabPosition=left;html=1;whiteSpace=nowrap;fillColor={fill};"
            f"strokeColor={stroke};verticalAlign=top;align=left;spacingLeft=9;spacingTop={2 if frame else 1};"
            f"fontStyle=1;fontSize={size};")


ELEM = ("rounded=0;html=1;whiteSpace=wrap;fillColor=#ffffff;strokeColor=#d6b656;fontSize=12;")


def package_diagram(name, title, groups, singles, deps, cell_w=150, cell_h=56):
    """groups: [(gid, label, x, y, cols, [pkg names])]; singles: [(pid, label, x, y)]; deps: [(from, to)]
    Package ids inside groups are '<gid>/<pkg>'. Sizes are derived from the grid."""
    d = Diagram(name)
    ids = {}
    items = []
    maxx = maxy = 0
    for gid, label, x, y, cols, pkgs in groups:
        rows = (len(pkgs) + cols - 1) // cols
        w = 30 + cols * (cell_w + 24)
        h = 50 + rows * (cell_h + 22) + 6
        items.append((gid, label, x, y, w, h, cols, pkgs))
        maxx, maxy = max(maxx, x + w), max(maxy, y + h)
    for pid, label, x, y in singles:
        maxx, maxy = max(maxx, x + cell_w + 20), max(maxy, y + cell_h + 30)
    frame = d.v(title, 0, 0, maxx + 40, maxy + 40, PKG_FRAME)
    for gid, label, x, y, w, h, cols, pkgs in items:
        g = d.v(label, x, y, w, h, PKG_GROUP)
        ids[gid] = g
        for i, p in enumerate(pkgs):
            r, c = divmod(i, cols)
            ids[f"{gid}/{p}"] = d.v(p, x + 27 + c * (cell_w + 24), y + 44 + r * (cell_h + 22), cell_w, cell_h, PKG)
    for pid, label, x, y in singles:
        ids[pid] = d.v(label, x, y, cell_w + 20, cell_h + 10, PKG_GROUP.replace("verticalAlign=top;", "")
                       .replace("spacingTop=22;", "spacingTop=14;"))
    for a, b in deps:
        d.e(ids[a], ids[b], DEP)
    d.save()
    return d


# ---------------------------------------------------------------- classes
CLS_BLUE = "#94B6E7"        # one colour for every class box
STEREO = {"controller": "Controller", "service": "Service", "interface": "Interface", "repository": "Repository",
          "entity": "Entity", "client": "FeignClient", "external": "External", "component": "Component", "dto": "DTO"}
CLS_HEAD = 40


try:
    from PIL import ImageFont
    _F11, _F12B = ImageFont.truetype("arial.ttf", 11), ImageFont.truetype("arialbd.ttf", 12)

    def _text_w(s, bold=False):
        return (_F12B if bold else _F11).getlength(s)
except Exception:                                   # no Pillow / font: rough estimate
    def _text_w(s, bold=False):
        return tw(s, 12 if bold else 11, bold) * 1.07


def class_size(name, attrs, methods):
    la, lm = attrs or [], methods or []
    # text + spacingLeft 6 + spacingRight 4 + a small safety margin
    w = max(120, _text_w(name, True) + 24, *(_text_w(s) + 20 for s in la + lm))
    w = float(int(w + 0.999))
    ha = round(len(la) * 13.2) + 8 if la else 10      # html text, fontSize 11 -> 13.2 px per line
    hm = round(len(lm) * 13.2) + 8 if lm else 10
    return w, CLS_HEAD + ha + 8 + hm, ha, hm


def class_box(d, name, kind, attrs, methods, x, y, w=None):
    lines_a, lines_m = attrs or [], methods or []
    w0, h, ha, hm = class_size(name, lines_a, lines_m)
    w = w or w0
    st = (f"swimlane;fontStyle=0;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize={CLS_HEAD};"
          f"horizontalStack=0;resizeParent=1;resizeLast=0;collapsible=0;marginBottom=0;html=1;whiteSpace=wrap;"
          f"fillColor={CLS_BLUE};swimlaneFillColor={CLS_BLUE};strokeColor=#36393d;fontSize=12;")
    cid = d.v(f"&lt;&lt;{STEREO[kind]}&gt;&gt;<br><b>{esc(name)}</b>", x, y, w, h, st)
    txt = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=6;spacingRight=4;"
           "overflow=hidden;rotatable=0;html=1;whiteSpace=nowrap;fontSize=11;")
    d.v("<br>".join(esc(s) for s in lines_a), 0, CLS_HEAD, w, ha, txt, parent=cid)
    d.v("", 0, CLS_HEAD + ha, w, 8, "line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;"
        "spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;", parent=cid)
    d.v("<br>".join(esc(s) for s in lines_m), 0, CLS_HEAD + ha + 8, w, hm, txt, parent=cid)
    return cid, w, h


_E = "edgeStyle=none;rounded=0;html=1;fontSize=10;labelBackgroundColor=#ffffff;strokeColor=#000000;"
EDGE = {
    "uses": _E + "dashed=1;endArrow=open;endSize=10;",
    "impl": _E + "dashed=1;endArrow=block;endFill=0;endSize=12;",
    "ext": _E + "endArrow=block;endFill=0;endSize=12;",
    "assoc": _E + "endArrow=none;",
    "async": _E + "dashed=1;dashPattern=1 3;endArrow=open;endSize=10;",
}
HIDDEN_LABELS = {"Uses", "Manages", "Feign", "Implements"}   # the arrow / stereotype already says it


class _Router:
    """Orthogonal routes between class boxes: straight when the boxes face each other, otherwise
    vertical - horizontal - vertical through the free band between two rows. No segment crosses a box,
    no two arrows run on top of each other."""

    def __init__(self, geo):
        self.geo, self.segs = geo, []

    def blocked(self, seg, a, b, tight=False):
        (x1, y1), (x2, y2) = seg
        lx, hx, ly, hy = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        for n, (rx, ry, rw, rh) in self.geo.items():
            m = 0 if n in (a, b) else 8
            if n in (a, b):
                # a segment may only touch its own boxes at the end points
                if lx < rx + rw - 1 and hx > rx + 1 and ly < ry + rh - 1 and hy > ry + 1:
                    return True
                continue
            if lx < rx + rw + m and hx > rx - m and ly < ry + rh + m and hy > ry - m:
                return True
        for (p1, p2) in self.segs:
            if x1 == x2 and p1[0] == p2[0] and abs(p1[0] - x1) < 20 and \
                    min(hy, max(p1[1], p2[1])) - max(ly, min(p1[1], p2[1])) > -6:
                return True
            if y1 == y2 and p1[1] == p2[1] and abs(p1[1] - y1) < 20 and \
                    min(hx, max(p1[0], p2[0])) - max(lx, min(p1[0], p2[0])) > -6:
                return True
        return False

    def clear(self, segs, a, b):
        return all(not self.blocked(s, a, b) for s in segs)

    def crossings(self, segs):
        n = 0
        for (p1, p2) in segs:
            for (q1, q2) in self.segs:
                if p1[0] == p2[0] and q1[1] == q2[1]:
                    x, y = p1[0], q1[1]
                    if min(q1[0], q2[0]) + 2 < x < max(q1[0], q2[0]) - 2 and min(p1[1], p2[1]) + 2 < y < max(p1[1], p2[1]) - 2:
                        n += 1
                elif p1[1] == p2[1] and q1[0] == q2[0]:
                    x, y = q1[0], p1[1]
                    if min(p1[0], p2[0]) + 2 < x < max(p1[0], p2[0]) - 2 and min(q1[1], q2[1]) + 2 < y < max(q1[1], q2[1]) - 2:
                        n += 1
        return n

    @staticmethod
    def cands(lo, hi, pref, step=6, margin=16):
        lo, hi = lo + margin, hi - margin
        if hi < lo:
            return []
        pref = min(max(pref, lo), hi)
        out = [pref]
        k = 1
        while pref - k * step >= lo or pref + k * step <= hi:
            for v in (pref - k * step, pref + k * step):
                if lo <= v <= hi:
                    out.append(v)
            k += 1
        return out

    def route(self, a, b, bands):
        ax, ay, aw, ah = self.geo[a]
        bx, by, bw, bh = self.geo[b]
        acx, bcx = ax + aw / 2, bx + bw / 2
        # 1. straight vertical
        if ay + ah <= by or by + bh <= ay:
            down = ay + ah <= by
            lo, hi = max(ax, bx), min(ax + aw, bx + bw)
            pref = (lo + hi) / 2
            for x in self.cands(lo, hi, pref):
                s = [((x, ay + ah if down else ay), (x, by if down else by + bh))]
                if self.clear(s, a, b):
                    return s
        # 2. straight horizontal
        if ax + aw <= bx or bx + bw <= ax:
            right = ax + aw <= bx
            lo, hi = max(ay + CLS_HEAD * 0.4, by + CLS_HEAD * 0.4), min(ay + ah, by + bh)
            for y in self.cands(lo, hi, lo + 4, margin=0):
                s = [((ax + aw if right else ax, y), (bx if right else bx + bw, y))]
                if self.clear(s, a, b):
                    return s
        # 3. vertical - horizontal - vertical through a free band
        if by >= ay + ah:                      # b below a
            ea, eb, opts = ay + ah, by, [bd for bd in bands if bd[0] >= ay + ah - 1 and bd[1] <= by + 1]
        elif ay >= by + bh:                    # b above a
            ea, eb, opts = ay, by + bh, [bd for bd in bands if bd[0] >= by + bh - 1 and bd[1] <= ay + 1]
        else:                                  # same row: leave and enter from below
            ea, eb = ay + ah, by + bh
            opts = [bd for bd in bands if bd[0] >= max(ay + ah, by + bh) - 1][:1]
        fallback = None
        for band in opts:
            for yc in self.cands(band[0], band[1], (band[0] + band[1]) / 2, step=8, margin=12):
                for xa in self.cands(ax, ax + aw, min(max(bcx, ax), ax + aw)):
                    s1 = ((xa, ea), (xa, yc))
                    if self.blocked(s1, a, b):
                        continue
                    for xb in self.cands(bx, bx + bw, bcx if abs(bcx - xa) > 1 else bcx):
                        segs = [s1, ((xa, yc), (xb, yc)), ((xb, yc), (xb, eb))]
                        if abs(xb - xa) < 1:
                            segs = [((xa, ea), (xa, eb))]
                        if self.clear(segs[1:] if len(segs) == 3 else segs, a, b):
                            if not self.crossings(segs):
                                return segs
                            fallback = fallback or segs
        if fallback:
            alt = self.astar(a, b)
            return alt if alt and not self.crossings(alt) else fallback
        return self.astar(a, b)

    def astar(self, a, b, step=10):
        """Orthogonal path on a grid avoiding every box (with a margin) and the arrows already drawn."""
        import heapq
        xs0 = min(g[0] for g in self.geo.values()) - 80
        ys0 = min(g[1] for g in self.geo.values()) - 80
        X1 = max(g[0] + g[2] for g in self.geo.values()) + 80
        Y1 = max(g[1] + g[3] for g in self.geo.values()) + 80
        nx, ny = int((X1 - xs0) / step) + 1, int((Y1 - ys0) / step) + 1
        P = lambda i, j: (xs0 + i * step, ys0 + j * step)

        def inside(n, x, y, m):
            rx, ry, rw, rh = self.geo[n]
            return rx - m < x < rx + rw + m and ry - m < y < ry + rh + m
        free = {}

        def ok(i, j):
            if (i, j) not in free:
                x, y = P(i, j)
                free[(i, j)] = 0 <= i < nx and 0 <= j < ny and not any(
                    inside(n, x, y, 1 if n in (a, b) else 10) for n in self.geo)
            return free[(i, j)]
        used, near = set(), set()
        for (p1, p2) in self.segs:
            for t in range(0, int(max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1])) / step) + 1):
                x = p1[0] + (step * t if p2[0] > p1[0] else -step * t if p2[0] < p1[0] else 0)
                y = p1[1] + (step * t if p2[1] > p1[1] else -step * t if p2[1] < p1[1] else 0)
                i0, j0, v = round((x - xs0) / step), round((y - ys0) / step), p1[0] == p2[0]
                used.add((i0, j0, v))
                for k in (-1, 1):                # keep a free lane on both sides of an arrow
                    near.add((i0 + k, j0, v) if v else (i0, j0 + k, v))

        def ports(n):
            rx, ry, rw, rh = self.geo[n]
            out = []
            for i in range(int((rx + 16 - xs0) / step) + 1, int((rx + rw - 16 - xs0) / step)):
                out.append(((i, int((ry - xs0 * 0 - ys0) / step) - 1), (0, -1), (P(i, 0)[0], ry)))
                out.append(((i, int((ry + rh - ys0) / step) + 1), (0, 1), (P(i, 0)[0], ry + rh)))
            for j in range(int((ry + 30 - ys0) / step) + 1, int((ry + rh - 10 - ys0) / step)):
                out.append(((int((rx - xs0) / step) - 1, j), (-1, 0), (rx, P(0, j)[1])))
                out.append(((int((rx + rw - xs0) / step) + 1, j), (1, 0), (rx + rw, P(0, j)[1])))
            return out
        goal = {}
        for cell, d, pt in ports(b):
            goal[(cell, (-d[0], -d[1]))] = pt
        pq, best, prev = [], {}, {}
        for cell, d, pt in ports(a):
            if ok(*cell):
                st = (cell, d)
                best[st] = 0
                prev[st] = ("start", pt)
                heapq.heappush(pq, (0, cell, d))
        end = None
        while pq:
            c, cell, d = heapq.heappop(pq)
            if best.get((cell, d), 1e18) < c:
                continue
            if (cell, d) in goal:
                end = (cell, d)
                break
            for nd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if nd == (-d[0], -d[1]):
                    continue
                nc = (cell[0] + nd[0], cell[1] + nd[1])
                if not ok(*nc):
                    continue
                vert = nd[0] == 0
                cost = c + step + (300 if nd != d else 0) + (5000 if (nc[0], nc[1], vert) in used else 0) + (2000 if (nc[0], nc[1], vert) in near else 0) + (60 if (nc[0], nc[1], not vert) in used else 0)
                if cost < best.get((nc, nd), 1e18):
                    best[(nc, nd)] = cost
                    prev[(nc, nd)] = (cell, d)
                    heapq.heappush(pq, (cost, nc, nd))
        if end is None:
            return None
        cells, st = [], end
        while prev[st][0] != "start":
            cells.append(P(*st[0]))
            st = prev[st]
        cells.append(P(*st[0]))
        start_pt = prev[st][1]
        cells = [start_pt] + cells[::-1] + [goal[end]]
        pts = [cells[0]]                        # keep only the corners
        for k in range(1, len(cells) - 1):
            p0, p1, p2 = pts[-1], cells[k], cells[k + 1]
            if not ((p0[0] == p1[0] == p2[0]) or (p0[1] == p1[1] == p2[1])):
                pts.append(p1)
        pts.append(cells[-1])
        return [(pts[k], pts[k + 1]) for k in range(len(pts) - 1)]


def class_diagram(name, rows, classes, edges, hgap=60, vgap=90, max_w=1700):
    """rows: list of lists of class names; classes: name -> (kind, attrs, methods); edges: (a, b, kind, label)"""
    d = Diagram(name)
    size = {n: class_size(n, a, m)[:2] for n, (k, a, m) in classes.items()}
    wrapped = []                                 # a row wider than max_w continues on the next line
    for row in rows:
        cur, wsum = [], 0
        for n in row:
            if cur and wsum + hgap + size[n][0] > max_w:
                wrapped.append(cur)
                cur, wsum = [], 0
            wsum += (hgap if cur else 0) + size[n][0]
            cur.append(n)
        wrapped.append(cur)
    rows = wrapped
    rowof = {n: r for r, row in enumerate(rows) for n in row}
    nb = {n: set() for n in rowof}
    for a, b, _, _ in edges:
        nb[a].add(b)
        nb[b].add(a)
    # vertical positions
    rowtop, y = [], 0
    for row in rows:
        rowtop.append(y)
        y += max(size[n][1] for n in row) + vgap
    # horizontal positions: start packed, then pull every box towards the boxes it is connected to
    cx = {}
    for row in rows:
        tot = sum(size[n][0] for n in row) + hgap * (len(row) - 1)
        x = -tot / 2
        for n in row:
            cx[n] = x + size[n][0] / 2
            x += size[n][0] + hgap
    for it in range(12):
        for row in (rows if it % 2 == 0 else rows[::-1]):
            want = {n: sum(cx[m] for m in nb[n]) / len(nb[n]) for n in row if nb[n]}
            xs, prev = {}, None
            for n in row:
                w = size[n][0]
                left = (want[n] if n in want else (cx[n])) - w / 2
                if prev is not None:
                    left = max(left, prev + hgap)
                xs[n] = left + w / 2
                prev = left + w
            if want:                             # shift the row back so that it sits around its targets
                sh = sum(want[n] - xs[n] for n in want) / len(want)
                xs = {n: v + sh for n, v in xs.items()}
            cx.update(xs)
    # close empty vertical strips (e.g. between two groups of classes that are not connected)
    while True:
        iv = sorted((cx[n] - size[n][0] / 2, cx[n] + size[n][0] / 2) for n in rowof)
        reach, cut = iv[0][1], None
        for x0, x1 in iv[1:]:
            if x0 - reach > hgap + 1:
                cut = (reach, x0)
                break
            reach = max(reach, x1)
        if not cut:
            break
        for n in rowof:
            if cx[n] > cut[1]:
                cx[n] -= cut[1] - cut[0] - hgap
    minx = min(cx[n] - size[n][0] / 2 for n in rowof)
    geo, ids = {}, {}
    for r, row in enumerate(rows):
        for n in row:
            w, h = size[n]
            x0 = cx[n] - w / 2 - minx + 20
            kind, attrs, methods = classes[n]
            ids[n], w, h = class_box(d, n, kind, attrs, methods, x0, rowtop[r] + 20, w)
            geo[n] = (x0, rowtop[r] + 20, w, h)
    rowbot = [max(geo[n][1] + geo[n][3] for n in row) for row in rows]
    bands = [(rowbot[r], rowtop[r + 1] + 20) for r in range(len(rows) - 1)] + [(rowbot[-1], rowbot[-1] + vgap)]
    total_w = max(g[0] + g[2] for g in geo.values())
    router = _Router(geo)
    # short / straight edges first so that they get the best places
    order = sorted(edges, key=lambda e: (abs(rowof[e[0]] - rowof[e[1]]),
                                         abs(geo[e[0]][0] + geo[e[0]][2] / 2 - geo[e[1]][0] - geo[e[1]][2] / 2)))
    corridor = 0
    for a, b, kind, label in order:
        segs = router.route(a, b, bands)
        assert segs, f"{name}: no route for {a} -> {b}"
        router.segs += segs
        (sx, sy), (tx, ty) = segs[0][0], segs[-1][1]
        ax, ay, aw, ah = geo[a]
        bx, by, bw, bh = geo[b]
        st = EDGE[kind] + (f"exitX={(sx - ax) / aw:.4f};exitY={(sy - ay) / ah:.4f};exitDx=0;exitDy=0;exitPerimeter=0;"
                           f"entryX={(tx - bx) / bw:.4f};entryY={(ty - by) / bh:.4f};entryDx=0;entryDy=0;entryPerimeter=0;")
        pts = [s[1] for s in segs[:-1]]
        if kind == "assoc" and " .. " in label:     # multiplicities at the two ends of the association
            eid = d.e(ids[a], ids[b], st, "", pts=pts)
            for txt, pos in zip(label.split(" .. "), (-0.75, 0.75)):
                d.cells.append(
                    f'<mxCell id="{d.nid()}" value="{esc(txt.strip())}" style="edgeLabel;html=1;resizable=0;'
                    f'labelBackgroundColor=#ffffff;fontSize=11;" vertex="1" connectable="0" parent="{eid}">'
                    f'<mxGeometry x="{pos}" relative="1" as="geometry"><mxPoint y="-9" as="offset"/></mxGeometry></mxCell>')
        else:
            d.e(ids[a], ids[b], st, "" if label in HIDDEN_LABELS else label, pts=pts)
    d.save()
    return d


# ---------------------------------------------------------------- database tables
def table_box(d, title, rows, x, y, w, more=0):
    """rows: [(key, name, type)] key in {'PK','FK','PK,FK',''}"""
    head = 28
    rh = 17
    n = len(rows) + (1 if more else 0)
    h = head + n * rh + 10
    st = ("swimlane;fontStyle=1;align=center;verticalAlign=middle;horizontal=1;startSize=28;collapsible=0;html=1;"
          "whiteSpace=wrap;fillColor=#dae8fc;strokeColor=#6c8ebf;swimlaneFillColor=#ffffff;fontSize=12;")
    cid = d.v(title, x, y, w, h, st)
    body = []
    for key, name, typ in rows:
        k = f"<b>{key}</b>" if key else ""
        nm = f"<u>{esc(name)}</u>" if "PK" in key else (f"<i>{esc(name)}</i>" if "FK" in key else esc(name))
        body.append(f'<tr><td style="width:30px;color:#C00000;padding:0">{k}</td><td style="padding:0 8px 0 0">{nm}</td>'
                    f'<td style="color:#555555;text-align:right;white-space:nowrap;padding:0">{esc(typ)}</td></tr>')
    if more:
        body.append(f'<tr><td style="padding:0"></td><td colspan="2" style="color:#777777;padding:0"><i>… {more} more columns</i></td></tr>')
    lbl = ('<table style="width:100%;border-collapse:collapse;font-size:10px;line-height:17px">'
           + "".join(body) + "</table>")
    d.cells.append(
        f'<mxCell id="{d.nid()}" value="{esc(lbl)}" style="text;html=1;whiteSpace=wrap;overflow=hidden;align=left;'
        f'verticalAlign=top;spacingLeft=6;spacingRight=6;spacingTop=2;fontSize=10;" vertex="1" parent="{cid}">'
        f'<mxGeometry x="0" y="{head}" width="{w}" height="{h - head}" as="geometry"/></mxCell>')
    return cid, h


REL = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endFill=0;startFill=0;endSize=12;startSize=12;"
       "strokeColor=#333333;jettySize=auto;orthogonalLoop=1;")


# ---------------------------------------------------------------- sequence diagrams
def _wrap(text, limit=46):
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > limit:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    return lines


def sequence(name, parts, steps):
    """parts: [(id, label, kind)] kind in actor|ui|ctrl|svc|repo|db|ext|mq|device
    steps: ('m'|'r'|'a', from, to, text) | ('s', who, text) | ('alt', [(cond, [steps])...]) | ('opt'|'loop', cond, [steps])"""
    d = Diagram(name)
    pid = [p[0] for p in parts]
    idx = {p: i for i, p in enumerate(pid)}
    counter = itertools.count(1)
    numbered = []

    def number(st):
        out = []
        for s in st:
            if s[0] in ("m", "r", "a") and s[1] == s[2]:
                out.append(("s", s[1], f"{next(counter)}: {s[3]}"))
            elif s[0] in ("m", "r", "a"):
                out.append((s[0], s[1], s[2], f"{next(counter)}: {s[3]}"))
            elif s[0] == "s":
                out.append(("s", s[1], f"{next(counter)}: {s[2]}"))
            elif s[0] == "alt":
                out.append(("alt", [(c, number(b)) for c, b in s[1]]))
            else:
                out.append((s[0], s[1], number(s[2])))
        return out

    steps = number(steps)

    # column gaps from label widths
    headw = [max(110, tw(lbl, 12) + 26) for _, lbl, _ in parts]
    gaps = [max(150, (headw[i] + headw[i + 1]) / 2 + 30) for i in range(len(parts) - 1)]
    msgs = []

    def collect(st):
        for s in st:
            if s[0] in ("m", "r", "a"):
                msgs.append(s)
            elif s[0] == "alt":
                for _, b in s[1]:
                    collect(b)
            elif s[0] in ("opt", "loop"):
                collect(s[2])
            elif s[0] == "s":
                i = idx[s[1]]
                need = max(tw(l, 11) for l in _wrap(s[2], 40)) + 60
                if i < len(gaps):
                    gaps[i] = max(gaps[i], need)

    collect(steps)
    for kind, a, b, text in sorted(msgs, key=lambda m: abs(idx[m[1]] - idx[m[2]])):
        i, j = sorted((idx[a], idx[b]))
        need = max(tw(l, 11) for l in _wrap(text)) + 24
        have = sum(gaps[i:j])
        if have < need:
            add = (need - have) / (j - i)
            for k in range(i, j):
                gaps[k] += add
    xs = [80]
    for g in gaps:
        xs.append(xs[-1] + g)
    top = 0
    y = [top + 80]
    involve = {p: [] for p in pid}
    frames = []
    draw = []

    def span_of(st):
        lo, hi = 10 ** 9, -1
        for s in st:
            if s[0] in ("m", "r", "a"):
                lo = min(lo, idx[s[1]], idx[s[2]])
                hi = max(hi, idx[s[1]], idx[s[2]])
            elif s[0] == "s":
                lo, hi = min(lo, idx[s[1]]), max(hi, idx[s[1]] + 1 if idx[s[1]] + 1 < len(pid) else idx[s[1]])
            elif s[0] == "alt":
                for _, b in s[1]:
                    a2, b2 = span_of(b)
                    lo, hi = min(lo, a2), max(hi, b2)
            else:
                a2, b2 = span_of(s[2])
                lo, hi = min(lo, a2), max(hi, b2)
        return lo, hi

    def layout(st, depth=0):
        for s in st:
            if s[0] in ("m", "r", "a"):
                lines = _wrap(s[3])
                y[0] += 14 * (len(lines) - 1)
                draw.append(("msg", s, y[0], lines))
                involve[s[1]].append(y[0])
                involve[s[2]].append(y[0])
                y[0] += 36
            elif s[0] == "s":
                lines = _wrap(s[2], 40)
                draw.append(("self", s, y[0], lines))
                involve[s[1]] += [y[0], y[0] + 18]
                y[0] += 36 + 14 * max(0, len(lines) - 1) + 8
            elif s[0] == "alt":
                lo, hi = span_of(st=[x for _, b in s[1] for x in b])
                fy = y[0] - 22
                seps = []
                for k, (cond, body) in enumerate(s[1]):
                    if k:
                        seps.append((y[0] - 18, cond))
                        y[0] += 18
                    else:
                        first = cond
                        y[0] += 12
                    layout(body, depth + 1)
                frames.append(("alt", lo, hi, fy, y[0] - 14, first, seps, depth))
                y[0] += 18
            else:
                lo, hi = span_of(s[2])
                fy = y[0] - 22
                y[0] += 12
                layout(s[2], depth + 1)
                frames.append((s[0], lo, hi, fy, y[0] - 14, s[1], [], depth))
                y[0] += 18

    layout(steps)
    bottom = y[0] + 10
    # lifelines
    for i, (p, lbl, kind) in enumerate(parts):
        w = headw[i]
        if kind == "actor":
            st = ("shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;"
                  "collapsible=0;recursiveResize=0;verticalAlign=top;spacingTop=36;outlineConnect=0;size=40;fontSize=12;labelBackgroundColor=#ffffff;whiteSpace=nowrap;")
            d.v(lbl, xs[i] - 20, top, 40, bottom - top, st)
        else:
            fill = {"db": "#dae8fc", "ext": "#f5f5f5", "mq": "#ffe6cc", "device": "#d5e8d4"}.get(kind, "#ffffff")
            st = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;collapsible=0;"
                  f"recursiveResize=0;outlineConnect=0;size=40;fontSize=12;fillColor={fill};")
            d.v(lbl, xs[i] - w / 2, top, w, bottom - top, st)
    # activation bars (one per participant, first..last involvement)
    for i, p in enumerate(pid):
        if parts[i][2] == "actor" or not involve[p]:
            continue
        a, b = min(involve[p]) - 6, max(involve[p]) + 6
        d.v("", xs[i] - 5, a, 10, b - a, "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;")
    # frames (outer first)
    for kind, lo, hi, fy, by, cond, seps, depth in sorted(frames, key=lambda f: f[7]):
        x0 = xs[lo] - headw[lo] / 2 - 14 + depth * 10
        x1 = xs[hi] + headw[hi] / 2 + 14 - depth * 10
        d.v(kind, x0, fy, x1 - x0, by - fy,
            "shape=umlFrame;whiteSpace=wrap;html=1;width=46;height=20;fontStyle=1;fillColor=none;fontSize=11;")
        d.v(f"[{cond}]", x0 + 52, fy, tw(cond, 11, True) + 20, 20,
            "text;html=1;align=left;verticalAlign=middle;fontStyle=1;fontSize=11;")
        for sy, c in seps:
            d.e(None, None, "endArrow=none;dashed=1;html=1;strokeColor=#000000;", sp=(x0, sy), tp=(x1, sy))
            d.v(f"[{c}]", x0 + 6, sy + 1, tw(c, 11, True) + 20, 18,
                "text;html=1;align=left;verticalAlign=middle;fontStyle=1;fontSize=11;")
    # messages
    for typ, s, yy, lines in draw:
        if typ == "msg":
            k, a, b, _ = s
            xa, xb = xs[idx[a]], xs[idx[b]]
            sgn = 1 if xb > xa else -1
            xa2 = xa + (5 * sgn if parts[idx[a]][2] != "actor" else 0)
            xb2 = xb - 5 * sgn
            st = {"m": "html=1;verticalAlign=bottom;endArrow=block;endFill=1;rounded=0;fontSize=11;",
                  "r": "html=1;verticalAlign=bottom;endArrow=open;dashed=1;endSize=8;rounded=0;fontSize=11;",
                  "a": "html=1;verticalAlign=bottom;endArrow=open;endSize=8;rounded=0;fontSize=11;"}[k]
            d.e(None, None, st, "<br>".join(esc(l) for l in lines), sp=(xa2, yy), tp=(xb2, yy))
        else:
            _, who, _ = s
            x = xs[idx[who]]
            d.e(None, None, "html=1;endArrow=block;endFill=1;rounded=0;fontSize=11;",
                sp=(x + 5, yy), tp=(x + 5, yy + 18), pts=[(x + 34, yy), (x + 34, yy + 18)])
            d.v("<br>".join(esc(l) for l in lines), x + 38, yy - 14, max(tw(l, 11) for l in lines) + 12,
                16 * len(lines), "text;html=1;align=left;verticalAlign=top;fontSize=11;")
    d.save()
    return d
