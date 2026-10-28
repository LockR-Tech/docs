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
CLS_FILL = {"controller": "#7EA6E0", "service": "#7EA6E0", "interface": "#A9C4EB", "repository": "#A9C4EB",
            "entity": "#B9E0A5", "client": "#FFE6CC", "external": "#F5F5F5", "component": "#7EA6E0", "dto": "#E1D5E7"}
STEREO = {"controller": "Controller", "service": "Service", "interface": "Interface", "repository": "Repository",
          "entity": "Entity", "client": "FeignClient", "external": "External", "component": "Component", "dto": "DTO"}


def class_box(d, name, kind, attrs, methods, x, y, w=None):
    lines_a = attrs or []
    lines_m = methods or []
    w = w or max(170, tw(name, 12, True) + 30, *(tw(s, 11) * 1.07 + 24 for s in lines_a + lines_m))
    head = 40
    ha = max(1, len(lines_a)) * 15 + 8 if lines_a else 10
    hm = max(1, len(lines_m)) * 15 + 8 if lines_m else 10
    h = head + ha + 8 + hm
    fill = CLS_FILL[kind]
    st = (f"swimlane;fontStyle=0;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize={head};"
          f"horizontalStack=0;resizeParent=1;resizeLast=0;collapsible=0;marginBottom=0;html=1;whiteSpace=wrap;"
          f"fillColor={fill};swimlaneFillColor={fill};strokeColor=#36393d;fontSize=12;")
    cid = d.v(f"&lt;&lt;{STEREO[kind]}&gt;&gt;<br><b>{esc(name)}</b>", x, y, w, h, st)
    txt = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=6;spacingRight=4;"
           "overflow=hidden;rotatable=0;html=1;whiteSpace=nowrap;fontSize=11;")
    d.v("<br>".join(esc(s) for s in lines_a), 0, head, w, ha, txt, parent=cid)
    d.v("", 0, head + ha, w, 8, "line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;"
        "spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;", parent=cid)
    d.v("<br>".join(esc(s) for s in lines_m), 0, head + ha + 8, w, hm, txt, parent=cid)
    return cid, w, h


EDGE = {
    "uses": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;endArrow=open;endSize=10;fontSize=10;labelBackgroundColor=#ffffff;",
    "impl": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;endArrow=block;endFill=0;endSize=12;fontSize=10;labelBackgroundColor=#ffffff;",
    "ext": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=0;endSize=12;fontSize=10;labelBackgroundColor=#ffffff;",
    "assoc": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;fontSize=10;labelBackgroundColor=#ffffff;",
    "async": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;dashPattern=1 3;endArrow=open;endSize=10;fontSize=10;labelBackgroundColor=#ffffff;",
}


def class_diagram(name, rows, classes, edges, hgap=50, vgap=70):
    """rows: list of lists of class names; classes: name -> (kind, attrs, methods); edges: (a, b, kind, label)"""
    d = Diagram(name)
    sizes = {}
    for n, (kind, attrs, methods) in classes.items():
        la, lm = attrs or [], methods or []
        w = max(170, tw(n, 12, True) + 30, *(tw(s, 11) * 1.07 + 24 for s in la + lm))
        sizes[n] = w
    widths = [sum(sizes[n] for n in r) + hgap * (len(r) - 1) for r in rows]
    total = max(widths)
    y = 0
    ids, geo, rowof, rowtop, rowbot = {}, {}, {}, [], []
    for ri, (r, rw) in enumerate(zip(rows, widths)):
        x = (total - rw) / 2
        hmax = 0
        for n in r:
            kind, attrs, methods = classes[n]
            cid, w, h = class_box(d, n, kind, attrs, methods, x, y, sizes[n])
            ids[n], geo[n], rowof[n] = cid, (x, y, w, h), ri
            x += w + hgap
            hmax = max(hmax, h)
        rowtop.append(y)
        rowbot.append(y + hmax)
        y += hmax + vgap
    # spread the exit points of each source and the entry points of each target
    outs, ins = {}, {}
    for a, b, kind, label in edges:
        outs.setdefault(a, []).append(b)
        ins.setdefault(b, []).append(a)

    def frac(lst, item):
        k = lst.index(item)
        return (k + 1) / (len(lst) + 1)

    corridor = [0]
    for a, b, kind, label in edges:
        ax, ay, aw, ah = geo[a]
        bx, by, bw, bh = geo[b]
        ra, rb = rowof[a], rowof[b]
        st = EDGE[kind]
        lbl = "" if label == "Uses" else label
        fa = frac(sorted(outs[a], key=lambda n: geo[n][0]), b)
        fb = frac(sorted(ins[b], key=lambda n: geo[n][0]), a)
        if ra == rb:
            between = [n for n in rows[ra] if min(ax, bx) < geo[n][0] < max(ax, bx)]
            if not between:
                right = bx > ax
                st += (f"exitX={1 if right else 0};exitY={30 / ah:.4f};exitDx=0;exitDy=0;"
                       f"entryX={0 if right else 1};entryY={30 / bh:.4f};entryDx=0;entryDy=0;")
                d.e(ids[a], ids[b], st, lbl)
            else:
                gy = rowbot[ra] + vgap * 0.3
                st += f"exitX={fa:.3f};exitY=1;exitDx=0;exitDy=0;entryX={fb:.3f};entryY=1;entryDx=0;entryDy=0;"
                d.e(ids[a], ids[b], st, lbl, pts=[(ax + aw * fa, gy), (bx + bw * fb, gy)])
        elif abs(rb - ra) == 1:
            down = rb > ra
            gy = (rowbot[ra] if down else rowtop[ra]) + (1 if down else -1) * vgap * (0.25 + 0.5 * fb)
            st += (f"exitX={fa:.3f};exitY={1 if down else 0};exitDx=0;exitDy=0;"
                   f"entryX={fb:.3f};entryY={0 if down else 1};entryDx=0;entryDy=0;")
            d.e(ids[a], ids[b], st, lbl, pts=[(ax + aw * fa, gy), (bx + bw * fb, gy)])
        else:
            down = rb > ra
            cx = total + 30 + 16 * corridor[0]
            corridor[0] += 1
            g1 = (rowbot[ra] + vgap * 0.5) if down else (rowtop[ra] - vgap * 0.5)
            g2 = (rowtop[rb] - vgap * 0.5) if down else (rowbot[rb] + vgap * 0.5)
            st += (f"exitX={fa:.3f};exitY={1 if down else 0};exitDx=0;exitDy=0;"
                   f"entryX={fb:.3f};entryY={0 if down else 1};entryDx=0;entryDy=0;")
            d.e(ids[a], ids[b], st, lbl, pts=[(ax + aw * fa, g1), (cx, g1), (cx, g2), (bx + bw * fb, g2)])
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
