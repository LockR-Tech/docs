"""1.2 Package diagrams in UML notation, built from the real source tree.

* Every package / folder name is read from the code; source files are not drawn.
* Every dependency arrow corresponds to import statements in the code (check_edges); only the main
  dependencies are drawn, the tables of the report list all of them.
* Notation: a package that shows its contents has its name in the tab, a package shown without contents has
  its name in the body, a dependency is a dashed arrow with an open head and no label. Black on white.
* Each diagram sits in an outer package frame (empty tab) whose title is written inside, centred at the top.
* Packages are placed on a grid (a package may span several columns / rows); every arrow is a straight
  horizontal or vertical line (or one right angle), routed so that it never crosses a package.
"""
import math
import os
import re

from dl import Diagram, tw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
JAVA = ("com", "huynqb", "laundrylocker")

FONT = "fontFamily=Helvetica;fontColor=#000000;"
BOX = "html=1;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;" + FONT
LTW, LTH = 26, 8            # tab of a package drawn without its contents
TH = 18                     # tab of a package that shows its contents
LH = 30                     # body height of a package drawn without its contents
PAD = 14                    # inner margin of a package that shows its contents
CGAP = 10                   # gap between packages inside a grid package
TITLE_H = 32                # title line of a frame
FTW = 90                    # tab width of the outer frame
FPAD = 18                   # inner margin of a frame
DEP = "endArrow=open;endSize=8;dashed=1;html=1;rounded=0;strokeColor=#000000;edgeStyle=none;"


def lw(label):
    return max(84, int(tw(label, 11, True)) + 26)


# ====================================================================== nodes
class Leaf:
    """Package drawn without its contents."""
    def __init__(self, label, w=None):
        self.label, self.w = label, w or lw(label)

    def size(self):
        return self.w, LTH + LH


class Grid:
    """Package whose sub-packages (drawn without contents) sit in a grid."""
    def __init__(self, label, items, cols):
        self.label, self.items = label, list(items)
        self.cols = max(1, min(cols, len(self.items)))
        self.cw = max(lw(i) for i in self.items)

    def rows(self):
        return math.ceil(len(self.items) / self.cols)

    def size(self):
        w = 2 * PAD + self.cols * self.cw + (self.cols - 1) * CGAP
        w = max(w, int(tw(self.label, 11, True)) + 60)
        return w, TH + PAD + self.rows() * (LTH + LH) + (self.rows() - 1) * CGAP + PAD


class Graph:
    """Package (or, with frame=True, the diagram frame) holding nodes on a grid.
    nodes: {name: (node, pos)}, pos = (col, row) | (col0, col1, row) | (col0, col1, row0, row1)."""
    def __init__(self, label, nodes, edges=(), gx=28, gy=30, frame=False, min_col=40):
        self.label, self.edges, self.gx, self.gy, self.frame = label, list(edges), gx, gy, frame
        self.nodes = {}
        for n, (nd, p) in nodes.items():
            p = (p[0], p[0], p[1], p[1]) if len(p) == 2 else (p[0], p[1], p[2], p[2]) if len(p) == 3 else p
            self.nodes[n] = (nd, p)
        self.min_col = min_col
        leaves = [nd for nd, p in self.nodes.values() if isinstance(nd, Leaf) and p[0] == p[1]]
        for nd in leaves:                       # packages of one graph share one width: aligned columns
            nd.w = max(x.w for x in leaves)

    def geom(self):
        nc = max(p[1] for _, p in self.nodes.values()) + 1
        nr = max(p[3] for _, p in self.nodes.values()) + 1
        colw, rowh = [self.min_col] * nc, [0] * nr
        sz = {n: nd.size() for n, (nd, _) in self.nodes.items()}
        for n, (nd, (c0, c1, r0, r1)) in self.nodes.items():
            if c0 == c1:
                colw[c0] = max(colw[c0], sz[n][0])
            if r0 == r1:
                rowh[r0] = max(rowh[r0], sz[n][1])
        for n, (nd, (c0, c1, r0, r1)) in self.nodes.items():
            need = sz[n][0] - (sum(colw[c0:c1 + 1]) + self.gx * (c1 - c0))
            if need > 0:
                colw[c1] += need
            need = sz[n][1] - (sum(rowh[r0:r1 + 1]) + self.gy * (r1 - r0))
            if need > 0:
                rowh[r1] += need
        W = sum(colw) + self.gx * (nc - 1)
        H = sum(rowh) + self.gy * (nr - 1)
        return colw, rowh, W, H

    def size(self):
        _, _, W, H = self.geom()
        if self.frame:
            return max(W, int(tw(self.label, 13, True)) + 40) + 2 * FPAD, TH + TITLE_H + H + FPAD
        return max(W + 2 * PAD, int(tw(self.label, 11, True)) + 60), TH + PAD + H + PAD


# ====================================================================== drawing + routing
class Canvas:
    def __init__(self, name):
        self.d = Diagram(name)
        self.body = {}         # key -> (cell id, x, y, w, h) of the body
        self.rect = {}         # key -> (x, y, w, h) of the whole package (tab included)
        self.tab = {}          # key -> (x, y, w, h) of the tab
        self.segs = []         # drawn arrow segments ((x1, y1), (x2, y2))

    # ------------------------------------------------------------------ nodes
    def draw(self, nd, key, x, y, w, h):
        if isinstance(nd, Leaf):
            self.tab[key] = (x, y, LTW, LTH)
            self.d.v("", x, y, LTW, LTH + 1, BOX)
            cid = self.d.v(nd.label, x, y + LTH, w, h - LTH, BOX + "fontStyle=1;fontSize=11;")
            self.body[key], self.rect[key] = (cid, x, y + LTH, w, h - LTH), (x, y, w, h)
            return
        if isinstance(nd, Graph) and nd.frame:
            self.d.v("", x, y, FTW, TH + 1, BOX)
            cid = self.d.v("", x, y + TH, w, h - TH, BOX)
            self.d.v(nd.label, x, y + TH + 4, w, TITLE_H - 8,
                     "text;html=1;fontStyle=1;fontSize=13;align=center;verticalAlign=middle;" + FONT)
            self.body[key] = (cid, x, y + TH, w, h - TH)   # the frame is not an obstacle for the arrows
            top, inner_h = y + TH + TITLE_H, h - TH - TITLE_H - FPAD
        else:
            tw_ = int(tw(nd.label, 11, True) + 22)
            self.tab[key] = (x, y, tw_, TH)
            self.d.v(nd.label, x, y, tw_, TH + 1, BOX + "fontStyle=1;fontSize=11;align=left;spacingLeft=6;")
            cid = self.d.v("", x, y + TH, w, h - TH, BOX)
            self.body[key], self.rect[key] = (cid, x, y + TH, w, h - TH), (x, y, w, h)
            top, inner_h = y + TH + PAD, h - TH - 2 * PAD
        if isinstance(nd, Grid):
            iw = nd.cols * nd.cw + (nd.cols - 1) * CGAP
            ih = nd.rows() * (LTH + LH) + (nd.rows() - 1) * CGAP
            x0, y0 = x + (w - iw) / 2, top + (inner_h - ih) / 2
            for i, it in enumerate(nd.items):
                r, c = divmod(i, nd.cols)
                self.draw(Leaf(it, nd.cw), f"{key}/{it}", x0 + c * (nd.cw + CGAP), y0 + r * (LTH + LH + CGAP),
                          nd.cw, LTH + LH)
            return
        colw, rowh, W, H = nd.geom()
        x0, y0 = x + (w - W) / 2, top + (inner_h - H) / 2
        colx = [x0 + sum(colw[:c]) + nd.gx * c for c in range(len(colw))]
        rowy = [y0 + sum(rowh[:r]) + nd.gy * r for r in range(len(rowh))]
        for n, (ch, (c0, c1, r0, r1)) in nd.nodes.items():
            sx, sy = colx[c0], rowy[r0]
            sw, sh = colx[c1] + colw[c1] - sx, rowy[r1] + rowh[r1] - sy
            nw, nh = ch.size()
            cw_, cx_ = (nw, sx + (sw - nw) / 2) if c0 == c1 else (sw, sx)
            ch_, cy_ = (nh, sy + (sh - nh) / 2) if r0 == r1 else (sh, sy)
            self.draw(ch, f"{key}/{n}" if key else n, cx_, cy_, cw_, ch_)
        for a, b in nd.edges:
            self.dep(f"{key}/{a}" if key else a, f"{key}/{b}" if key else b)

    # ------------------------------------------------------------------ arrows
    def _blocked(self, seg, a, b):
        (x1, y1), (x2, y2) = seg
        lo_x, hi_x, lo_y, hi_y = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        anc = {k for k in self.rect for t in (a, b) if t.startswith(k + "/")}
        for k, (rx, ry, rw, rh) in self.rect.items():
            if k in (a, b) or k in anc:
                continue
            if lo_x < rx + rw + 3 and hi_x > rx - 3 and lo_y < ry + rh + 3 and hi_y > ry - 3:
                return True
        for k in (a, b, *anc):
            if k in self.tab:
                rx, ry, rw, rh = self.tab[k]
                if lo_x < rx + rw + 12 and hi_x > rx - 12 and lo_y < ry + rh + 1 and hi_y > ry - 3:
                    return True
        for (p1, p2) in self.segs:            # never run along another arrow
            if x1 == x2 and p1[0] == p2[0] and abs(p1[0] - x1) < 7 and \
                    min(hi_y, max(p1[1], p2[1])) - max(lo_y, min(p1[1], p2[1])) > 1:
                return True
            if y1 == y2 and p1[1] == p2[1] and abs(p1[1] - y1) < 7 and \
                    min(hi_x, max(p1[0], p2[0])) - max(lo_x, min(p1[0], p2[0])) > 1:
                return True
        return False

    @staticmethod
    def _cands(lo, hi, pref):
        lo, hi = lo + 10, hi - 10
        if hi < lo:
            return []
        pref = min(max(pref, lo), hi)
        pts = [pref] + [p for k in range(1, 400) for p in (pref - 2 * k, pref + 2 * k) if lo <= p <= hi]
        return pts

    def dep(self, a, b):
        _, ax, ay, aw, ah = self.body[a]
        _, bx, by, bw, bh = self.body[b]
        route = None
        if min(ax + aw, bx + bw) - max(ax, bx) >= 24 and (ay + ah <= by or by + bh <= ay):
            down = ay + ah <= by
            pref = (ax + aw / 2) if aw < bw else (bx + bw / 2)
            t = self.tab.get(b if down else a)
            if t and t[2] > LTW:                 # container: aim at the part of its top edge right of the tab
                pref = (t[0] + t[2] + (bx + bw if down else ax + aw)) / 2
            for x in self._cands(max(ax, bx), min(ax + aw, bx + bw), pref):
                seg = ((x, ay + ah if down else ay), (x, by if down else by + bh))
                if not self._blocked(seg, a, b):
                    route = [seg]
                    break
        elif min(ay + ah, by + bh) - max(ay, by) >= 16 and (ax + aw <= bx or bx + bw <= ax):
            right = ax + aw <= bx
            pref = (ay + ah / 2) if ah < bh else (by + bh / 2)
            for y in self._cands(max(ay, by), min(ay + ah, by + bh), pref):
                seg = ((ax + aw if right else ax, y), (bx if right else bx + bw, y))
                if not self._blocked(seg, a, b):
                    route = [seg]
                    break
        if route is None:                      # one right angle: leave a sideways, enter b from above / below
            right = bx + bw / 2 > ax + aw / 2
            down = by + bh / 2 > ay + ah / 2
            for y in self._cands(ay, ay + ah, ay + ah / 2):
                for x in self._cands(bx, bx + bw, bx + bw / 2):
                    s1 = ((ax + aw if right else ax, y), (x, y))
                    s2 = ((x, y), (x, by if down else by + bh))
                    if (x - s1[0][0]) * (1 if right else -1) > 10 and (s2[1][1] - y) * (1 if down else -1) > 10 \
                            and not self._blocked(s1, a, b) and not self._blocked(s2, a, b):
                        route = [s1, s2]
                        break
                if route:
                    break
        assert route, f"no clean route for {a} -> {b}"
        (sx, sy), (tx, ty) = route[0][0], route[-1][1]
        st = DEP + (f"exitX={(sx - ax) / aw:.4f};exitY={(sy - ay) / ah:.4f};exitDx=0;exitDy=0;exitPerimeter=0;"
                    f"entryX={(tx - bx) / bw:.4f};entryY={(ty - by) / bh:.4f};entryDx=0;entryDy=0;entryPerimeter=0;")
        self.d.e(self.body[a][0], self.body[b][0], st, pts=[route[0][1]] if len(route) == 2 else ())
        self.segs += route

    def save(self):
        self.d.save()


def render(name, frame):
    cv = Canvas(name)
    w, h = frame.size()
    cv.draw(frame, "", 20, 20, w, h)
    cv.save()
    return cv


def check_edges(shown, real, what):
    missing = set(shown) - set(real)
    assert not missing, f"{what}: arrows without an import in the code: {sorted(missing)}"


def listdir(*p):
    return sorted(os.listdir(os.path.join(ROOT, *p)))


def subdirs(*p):
    base = os.path.join(ROOT, *p)
    return sorted((d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))
                   and not d.startswith((".", "__")) and d not in ("node_modules",)), key=str.lower)


# ====================================================================== dependency extraction (from imports)
def java_service(svc):
    mod = f"{svc}-service"
    base = os.path.join(ROOT, "backend", mod, "src", "main", "java", *JAVA, svc)
    pkgs, deps, common = {}, set(), set()
    for dp, dns, fs in os.walk(base):
        rel = os.path.relpath(dp, base).replace(os.sep, ".")
        if rel == ".":
            continue
        top = rel.split(".")[0]
        if "." in rel:
            pkgs.setdefault(top, set()).add(rel.split(".", 1)[1])
        else:
            pkgs.setdefault(top, set())
        for f in fs:
            if not f.endswith(".java"):
                continue
            src = open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()
            for m in re.finditer(r"^import\s+(?:static\s+)?com\.huynqb\.laundrylocker\.(\w+)\.([\w.]+)\s*;", src, re.M):
                owner, path = m.group(1), m.group(2).split(".")
                head = []
                for p in path:
                    if p[0].isupper() or p == "*":
                        break
                    head.append(p)
                if owner == svc and head and head[0] != top:
                    deps.add((top, head[0]))
                elif owner == "common" and head:
                    common.add(head[0])
    items = {p: ((p, sorted(s)) if s else p) for p, s in pkgs.items()}
    return items, sorted(deps), sorted(common)


def ts_deps(base, alias=("@/", "~/")):
    deps = set()
    for dp, dns, fs in os.walk(base):
        for f in fs:
            if not f.endswith((".ts", ".tsx")):
                continue
            rel = os.path.relpath(os.path.join(dp, f), base).replace(os.sep, "/")
            me = rel.split("/")[0]
            for m in re.finditer(r"""(?:from|import)\s*\(?\s*['"]([^'"]+)['"]""",
                                 open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()):
                spec = m.group(1)
                if spec.startswith(alias):
                    tgt = spec[2:]
                elif spec.startswith("."):
                    tgt = os.path.normpath(os.path.join(os.path.dirname(rel), spec)).replace(os.sep, "/")
                else:
                    continue
                t = tgt.split("/")[0]
                if t != me and not t.startswith(".."):
                    if "/" not in tgt and os.path.exists(os.path.join(base, tgt + ".tsx")):
                        t = tgt + ".tsx"
                    deps.add((me, t))
    return deps


def dart_deps(base, pkg="package:smart_laundry_locker/", level=1, within=None):
    """Dependencies between folders `level` deep below base (or below base/within)."""
    deps = set()
    root = os.path.join(base, within) if within else base
    for dp, dns, fs in os.walk(root):
        for f in fs:
            if not f.endswith(".dart"):
                continue
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, base).replace(os.sep, "/")
            for m in re.finditer(r"""^(?:import|export)\s+['"]([^'"]+)['"]""",
                                 open(full, encoding="utf-8", errors="ignore").read(), re.M):
                spec = m.group(1)
                if spec.startswith(pkg):
                    tgt = spec[len(pkg):]
                elif spec.startswith(("package:", "dart:")):
                    continue
                else:
                    tgt = os.path.normpath(os.path.join(os.path.dirname(rel), spec)).replace(os.sep, "/")
                deps.add((rel, tgt))
    return deps


def py_deps(base, tops):
    deps = set()
    for name in os.listdir(base):
        full = os.path.join(base, name)
        files = []
        if name in tops:
            for dp, dns, fs in os.walk(full):
                files += [os.path.join(dp, f) for f in fs if f.endswith(".py")]
        elif name == "main.py":
            files = [full]
        for f in files:
            for m in re.finditer(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
                                 open(f, encoding="utf-8", errors="ignore").read(), re.M):
                t = (m.group(1) or m.group(2)).split(".")[0]
                if t in tops and t != name:
                    deps.add((name, t))
    return deps


# ====================================================================== 1. backend
def backend_overview():
    services = ["auth-service", "user-service", "order-service", "locker-service", "payment-service",
                "notification-service", "iot-service", "store-service", "loyalty-service", "assistant-service"]
    modules = re.findall(r"<module>([\w-]+)</module>", open(os.path.join(ROOT, "backend", "pom.xml"), encoding="utf-8").read())
    assert set(modules) == set(services) | {"common-lib", "api-gateway", "discovery-server"}, modules
    uses_common = [m for m in modules if m != "common-lib" and "<artifactId>common-lib</artifactId>" in
                   open(os.path.join(ROOT, "backend", m, "pom.xml"), encoding="utf-8").read()]
    assert set(uses_common) == set(services) | {"api-gateway"}, uses_common
    common = subdirs("backend", "common-lib", "src", "main", "java", *JAVA, "common")
    frame = Graph("Backend Package Diagram", {
        "api-gateway": (Leaf("api-gateway"), (0, 0)),
        "micro": (Grid("Backend Microservices", services, 3), (0, 1)),
        "common": (Grid("common-lib", common, 2), (1, 1, 0, 1)),
    }, edges=[("micro", "common"), ("api-gateway", "common")], gx=50, gy=36, frame=True)
    render("pkg_backend_overview", frame)


# ====================================================================== 2. one diagram per service
SVC_TITLE = {"auth": "Auth Service", "user": "User Service", "order": "Order Service", "locker": "Locker Service",
             "payment": "Payment Service", "notification": "Notification Service", "iot": "IoT Service",
             "store": "Store Service", "loyalty": "Loyalty Service", "assistant": "Assistant Service"}
SVC_ROW = ("client", "settings", "repository", "config", "email", "channel")       # packages under service


def service_graph(svc, items, deps):
    def node(p):
        it = items[p]
        return Grid(p, it[1], 1) if isinstance(it, tuple) else Leaf(p)
    if svc == "assistant":
        pos = {"controller": (0, 5, 0), "eval": (0, 1), "chat": (1, 4, 1), "knowledge": (5, 1),
               "settings": (1, 2), "orders": (2, 2), "query": (3, 2), "provider": (2, 5, 3), "config": (4, 4)}
        main = {("controller", "chat"), ("controller", "eval"), ("controller", "knowledge"), ("chat", "knowledge"),
                ("chat", "orders"), ("chat", "provider"), ("chat", "query"), ("chat", "settings"),
                ("knowledge", "provider"), ("orders", "provider"), ("query", "provider"), ("provider", "config")}
    else:
        row = [p for p in SVC_ROW if p in items]
        n = len(row)
        pos = {"dto": (0, 0, 0, 2), "controller": (1 + (n - 1) // 2, 0), "service": (1, n, 1)}
        pos.update({p: (1 + i, 2) for i, p in enumerate(row)})
        pos["model"] = (pos["repository"][0], 3)
        main = {("controller", "service"), ("controller", "dto"), ("service", "dto"), ("client", "dto"),
                ("repository", "model"), ("config", "service")} | {("service", p) for p in row}
    assert set(items) == set(pos), (svc, set(items) ^ set(pos))
    shown = sorted(e for e in deps if e in main)
    check_edges(shown, deps, svc)
    return Graph(".".join(JAVA + (svc,)), {p: (node(p), pos[p]) for p in items}, edges=shown)


def service_diagram(svc):
    items, deps, common = java_service(svc)
    frame = Graph(f"{SVC_TITLE[svc]} Package Diagram", {
        "base": (service_graph(svc, items, deps), (0, 0)),
        "common": (Grid("common-lib", common, len(common)), (0, 1)),
    }, edges=[("base", "common")], gy=40, frame=True)
    render("pkg_" + svc, frame)
    return items, deps, common


# ====================================================================== 3. admin web (frontend/fe/src)
def admin_web():
    p = ("frontend", "fe", "src")
    base = os.path.join(ROOT, *p)
    real = ts_deps(base)
    shown = [("routes", "pages"), ("routes", "context"), ("pages", "context"), ("pages", "components"),
             ("pages", "hooks"), ("pages", "stores"), ("hooks", "stores"), ("components", "lib"),
             ("stores", "schemas"), ("stores", "constants"), ("stores", "types"), ("stores", "utils"),
             ("schemas", "lib")]
    check_edges(shown, real, "admin web")
    pos = {"context": (0, 0, 0, 1), "routes": (1, 0), "assets": (6, 1), "pages": (1, 3, 1),
           "components": (1, 2), "hooks": (2, 2), "stores": (3, 5, 2), "types": (6, 6, 2, 3),
           "lib": (1, 3), "schemas": (3, 3), "constants": (4, 3), "utils": (5, 3)}
    assert set(subdirs(*p)) == set(pos), set(subdirs(*p)) ^ set(pos)
    cols = {"pages": 3, "components": 1, "types": 1, "stores": 1, "context": 1, "assets": 1}

    def node(n):
        s = subdirs(*p, n)
        return Grid(n, s, cols.get(n, 1)) if s else Leaf(n)
    src = Graph("src", {n: (node(n), q) for n, q in pos.items()}, edges=shown, gx=24)
    render("pkg_admin_web", Graph("Admin Web Package Diagram", {"src": (src, (0, 0))}, frame=True))
    return real, shown


# ====================================================================== 4. mobile application (mobile/lib)
def mobile_app():
    p = ("mobile", "lib")
    raw = dart_deps(os.path.join(ROOT, *p))
    real = {(s.split("/")[0], t.split("/")[0]) for s, t in raw if s.split("/")[0] != t.split("/")[0]}
    shown = [("features", "core"), ("features", "shared"), ("shared", "core"), ("core", "l10n")]
    check_edges(shown, real, "mobile app")
    pos = {"features": (0, 0, 0, 1), "core": (1, 0), "shared": (1, 1), "l10n": (2, 0)}
    assert set(subdirs(*p)) == set(pos), set(subdirs(*p)) ^ set(pos)
    cols = {"features": 2, "core": 3, "shared": 3}

    def node(n):
        s = subdirs(*p, n)
        return Grid(n, s, cols[n]) if s else Leaf(n)
    lib = Graph("lib", {n: (node(n), q) for n, q in pos.items()}, edges=shown, gx=40, gy=36)
    used = re.findall(r"""['"]assets/""", "".join(open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()
                      for dp, _, fs in os.walk(os.path.join(ROOT, *p)) for f in fs if f.endswith(".dart")))
    assert used, "lib does not use assets"
    assets = Grid("assets", subdirs("mobile", "assets"), 1)
    render("pkg_mobile_app", Graph("Mobile Application Package Diagram",
                                   {"assets": (assets, (0, 0)), "lib": (lib, (1, 0))},
                                   edges=[("lib", "assets")], gx=50, frame=True))
    return real, shown


# ====================================================================== 5. IoT locker controller (iot/)
def iot_controller():
    base = os.path.join(ROOT, "iot")
    tops = sorted(d for d in os.listdir(base) if os.path.exists(os.path.join(base, d, "__init__.py")))
    real = py_deps(base, set(tops))
    shown = [("services", "infracstructure"), ("services", "hardware"), ("services", "domain"),
             ("infracstructure", "hardware"), ("infracstructure", "config"), ("hardware", "domain"),
             ("config", "utils")]
    check_edges(shown, real, "iot controller")
    pos = {"services": (0, 2, 0), "infracstructure": (0, 1), "hardware": (1, 1), "domain": (2, 1),
           "config": (0, 2), "utils": (1, 2),
           "ui": (4, 0), "service_panel": (5, 0), "arduino": (4, 1), "scripts": (5, 1), "drone-iot": (4, 2)}
    assert set(tops) <= set(pos) and set(pos) <= set(subdirs("iot")), set(tops) ^ set(pos)
    iot = Graph("iot", {n: (Leaf(n), q) for n, q in pos.items()}, edges=shown)
    render("pkg_iot_controller", Graph("IoT Controller Package Diagram", {"iot": (iot, (0, 0))}, frame=True))
    return real, shown


# ====================================================================== run
if __name__ == "__main__":
    backend_overview()
    admin_web()
    mobile_app()
    iot_controller()
