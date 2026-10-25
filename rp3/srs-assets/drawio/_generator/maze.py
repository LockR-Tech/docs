"""Grid maze router (A*): orthogonal lines that never cross, touch or run next to another line or a box."""
import heapq

DIRS = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}


class Maze:
    def __init__(self, boxes, cell=6, margin=10, stub_cells=4, spacing=2, bend=6, pad=260, port_gap=2):
        self.boxes = dict(boxes)
        self.cell, self.stub, self.spacing, self.bend, self.port_gap = cell, stub_cells, spacing, bend, port_gap
        xs = [b[0] for b in boxes.values()] + [b[0] + b[2] for b in boxes.values()]
        ys = [b[1] for b in boxes.values()] + [b[1] + b[3] for b in boxes.values()]
        self.x0, self.y0 = min(xs) - pad, min(ys) - pad
        self.W = int((max(xs) + pad - self.x0) / cell) + 1
        self.H = int((max(ys) + pad - self.y0) / cell) + 1
        self.box_at = [None] * (self.W * self.H)      # which box (inflated by margin) covers the cell
        self.line = bytearray(self.W * self.H)         # 1 = taken by a line or its spacing halo
        self.used_ports = {}
        for name, (x, y, w, h) in boxes.items():
            i0, i1 = self._ci(x - margin), self._ci(x + w + margin)
            j0, j1 = self._cj(y - margin), self._cj(y + h + margin)
            for j in range(max(0, j0), min(self.H, j1 + 1)):
                for i in range(max(0, i0), min(self.W, i1 + 1)):
                    self.box_at[j * self.W + i] = name

    def _ci(self, x):
        return int((x - self.x0) / self.cell)

    def _cj(self, y):
        return int((y - self.y0) / self.cell)

    def cx(self, i):
        return self.x0 + (i + 0.5) * self.cell

    def cy(self, j):
        return self.y0 + (j + 0.5) * self.cell

    # ports: (side, port point on the box edge, list of stub cells from the box outwards)
    def _ports(self, name, sides, fixed=None):
        x, y, w, h = self.boxes[name]
        out = []
        for side in sides:
            dx, dy = DIRS[side]
            used = self.used_ports.get((name, side), [])
            if side in "LR":
                rows = [self._cj(fixed)] if fixed is not None else list(range(self._cj(y + 8), self._cj(y + h - 8) + 1))
                rows.sort(key=lambda j: abs(self.cy(j) - (y + h / 2)))
                for j in rows:
                    if any(abs(j - u) < self.port_gap + 1 for u in used):
                        continue
                    ex = x if side == "L" else x + w
                    i = self._ci(ex) + (0 if side == "L" else 0)
                    # first free cell outside the box margin, then the stub
                    cells = []
                    ii = self._ci(ex)
                    while 0 <= ii < self.W and self.box_at[j * self.W + ii] == name:
                        cells.append((ii, j))
                        ii += dx
                    for _ in range(self.stub):
                        cells.append((ii, j))
                        ii += dx
                    out.append((side, (ex, self.cy(j)), cells, j))
            else:
                cols = list(range(self._ci(x + 8), self._ci(x + w - 8) + 1))
                cols.sort(key=lambda i: abs(self.cx(i) - (x + w / 2)))
                for i in cols:
                    if any(abs(i - u) < self.port_gap + 1 for u in used):
                        continue
                    ey = y if side == "T" else y + h
                    cells = []
                    jj = self._cj(ey)
                    while 0 <= jj < self.H and self.box_at[jj * self.W + i] == name:
                        cells.append((i, jj))
                        jj += dy
                    for _ in range(self.stub):
                        cells.append((i, jj))
                        jj += dy
                    out.append((side, (self.cx(i), ey), cells, i))
        return out

    def _free(self, i, j, own=()):
        if not (0 <= i < self.W and 0 <= j < self.H):
            return False
        k = j * self.W + i
        if self.line[k]:
            return False
        b = self.box_at[k]
        return b is None or b in own

    def route(self, a, b, sides_a="LRTB", sides_b="LRTB", fixed_a=None, fixed_b=None, max_ports=14, max_pops=250000):
        def toward(box):
            x, y, w, h = self.boxes[box]
            return x + w / 2, y + h / 2

        def near(ports, other):
            ox, oy = toward(other)
            bx, by, bw, bh = self.boxes[other]
            # distance from the port to the other box (0 when the port faces it squarely)
            def key(p):
                px, py = p[1]
                dx = max(bx - px, 0, px - (bx + bw))
                dy = max(by - py, 0, py - (by + bh))
                return dx + dy + 0.01 * (abs(px - ox) + abs(py - oy))
            return sorted(ports, key=key)

        srcs = near([p for p in self._ports(a, sides_a, fixed_a) if all(self._free(i, j, (a,)) for i, j in p[2])], b)[:max_ports]
        dsts = near([p for p in self._ports(b, sides_b, fixed_b) if all(self._free(i, j, (b,)) for i, j in p[2])], a)[:max_ports]
        if not srcs or not dsts:
            return None
        goal = {}
        for k, (side, pt, cells, idx) in enumerate(dsts):
            ei, ej = cells[-1]
            dx, dy = DIRS[side]
            goal[(ei, ej)] = (k, (-dx, -dy))       # must arrive moving toward the box
        bx, by, bw, bh = self.boxes[b]
        ti, tj = self._ci(bx + bw / 2), self._cj(by + bh / 2)
        heap, best, prev = [], {}, {}
        for k, (side, pt, cells, idx) in enumerate(srcs):
            si, sj = cells[-1]
            d = DIRS[side]
            st = (si, sj, d)
            best[st] = 0
            prev[st] = ("src", k)
            heapq.heappush(heap, (abs(si - ti) + abs(sj - tj), 0, si, sj, d))
        found = None
        own = (a, b)
        pops = 0
        while heap:
            pops += 1
            if pops > max_pops:
                break
            f, g, i, j, d = heapq.heappop(heap)
            if best.get((i, j, d), 1e18) < g:
                continue
            if (i, j) in goal and goal[(i, j)][1] == d:
                found = (i, j, d)
                break
            for nd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if nd[0] == -d[0] and nd[1] == -d[1]:
                    continue
                ni, nj = i + nd[0], j + nd[1]
                if not self._free(ni, nj):
                    # the target's own margin is only reachable through its stub (handled by goal cells)
                    continue
                ng = g + 1 + (self.bend if nd != d else 0)
                key = (ni, nj, nd)
                if ng < best.get(key, 1e18):
                    best[key] = ng
                    prev[key] = (i, j, d)
                    heapq.heappush(heap, (ng + abs(ni - ti) + abs(nj - tj), ng, ni, nj, nd))
        if found is None:
            return None
        # walk back
        cells_path = []
        st = found
        while True:
            p = prev[st]
            cells_path.append((st[0], st[1]))
            if p[0] == "src":
                sk = p[1]
                break
            st = p
        cells_path.reverse()
        dk = goal[(found[0], found[1])][0]
        s_side, s_pt, s_cells, s_idx = srcs[sk]
        d_side, d_pt, d_cells, d_idx = dsts[dk]
        full = list(s_cells[:-1]) + cells_path + list(reversed(d_cells[:-1]))
        # mark the line + spacing halo
        for (i, j) in full:
            for dj in range(-self.spacing, self.spacing + 1):
                for di in range(-self.spacing, self.spacing + 1):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < self.W and 0 <= jj < self.H:
                        self.line[jj * self.W + ii] = 1
        self.used_ports.setdefault((a, s_side), []).append(s_idx)
        self.used_ports.setdefault((b, d_side), []).append(d_idx)
        pts = [s_pt] + [(self.cx(i), self.cy(j)) for i, j in full] + [d_pt]
        return _corners(pts), s_side, d_side


def _corners(pts):
    # keep the exact port points, snap the first/last cell onto the port's axis, drop collinear points
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) < 0.01 and abs(p[1] - out[-1][1]) < 0.01:
            continue
        out.append(p)
    res = [out[0]]
    for k in range(1, len(out) - 1):
        a, b, c = res[-1], out[k], out[k + 1]
        if (abs(a[0] - b[0]) < 0.01 and abs(b[0] - c[0]) < 0.01) or (abs(a[1] - b[1]) < 0.01 and abs(b[1] - c[1]) < 0.01):
            continue
        res.append(b)
    res.append(out[-1])
    return res


def mark_line(mz, pts):
    """Reserve an externally drawn polyline (plus its spacing halo) so routed lines keep clear of it."""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        n = int(max(abs(x2 - x1), abs(y2 - y1)) / (mz.cell / 2)) + 1
        for k in range(n + 1):
            x, y = x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n
            i, j = mz._ci(x), mz._cj(y)
            for dj in range(-mz.spacing, mz.spacing + 1):
                for di in range(-mz.spacing, mz.spacing + 1):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < mz.W and 0 <= jj < mz.H:
                        mz.line[jj * mz.W + ii] = 1
