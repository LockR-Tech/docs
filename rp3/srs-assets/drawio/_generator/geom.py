"""Geometry checks so a diagram is only exported when no line crosses another line or a shape."""


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)


def seg_cross(p1, p2, p3, p4):
    """Proper crossing of two segments (touching at shared endpoints does not count)."""
    for a in (p1, p2):
        for b in (p3, p4):
            if abs(a[0] - b[0]) < 0.5 and abs(a[1] - b[1]) < 0.5:
                return False
    o1, o2, o3, o4 = _orient(p1, p2, p3), _orient(p1, p2, p4), _orient(p3, p4, p1), _orient(p3, p4, p2)
    return o1 * o2 < 0 and o3 * o4 < 0


def seg_box(p1, p2, box, margin=0.0):
    """Does the segment pass through the rectangle (x, y, w, h) shrunk by margin?"""
    x, y, w, h = box
    x0, y0, x1, y1 = x + margin, y + margin, x + w - margin, y + h - margin
    if x0 >= x1 or y0 >= y1:
        return False
    # Liang–Barsky clipping
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p1[0] - x0), (dx, x1 - p1[0]), (-dy, p1[1] - y0), (dy, y1 - p1[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return t1 - t0 > 1e-6


def seg_ellipse(p1, p2, cx, cy, rx, ry, steps=60):
    for i in range(steps + 1):
        t = i / steps
        x, y = p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 0.97:
            return True
    return False


def bezier(p0, c, p2, n=40):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def polylines_cross(a, b):
    for i in range(len(a) - 1):
        for j in range(len(b) - 1):
            if seg_cross(a[i], a[i + 1], b[j], b[j + 1]):
                return True
    return False


def too_close_parallel(a1, a2, b1, b2, gap=5.0):
    """Two axis-aligned segments running on top of / right next to each other."""
    if abs(a1[1] - a2[1]) < 0.01 and abs(b1[1] - b2[1]) < 0.01:      # both horizontal
        if abs(a1[1] - b1[1]) < gap:
            lo, hi = max(min(a1[0], a2[0]), min(b1[0], b2[0])), min(max(a1[0], a2[0]), max(b1[0], b2[0]))
            return hi - lo > 1.0
    if abs(a1[0] - a2[0]) < 0.01 and abs(b1[0] - b2[0]) < 0.01:      # both vertical
        if abs(a1[0] - b1[0]) < gap:
            lo, hi = max(min(a1[1], a2[1]), min(b1[1], b2[1])), min(max(a1[1], a2[1]), max(b1[1], b2[1]))
            return hi - lo > 1.0
    return False
