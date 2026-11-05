"""Đi dây không cắt, không trùng: dùng bộ định tuyến lưới A* (maze.py) của bộ sinh Report 3, cộng kiểm tra lại sau khi đi.

Mỗi đường giữ ô lưới của nó kèm một vành đệm nên đường sau không thể cắt, chạm hay chạy sát đường trước; viền khối
service được dựng thành tường có cửa nhỏ, nên đường chỉ được cắt ngang viền chứ không chạy dọc theo viền."""
import os
import random
import sys

SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "drawio", "_generator"))
sys.path.insert(0, SRC)
from maze import Maze  # noqa: E402
from geom import polylines_cross, seg_box, too_close_parallel  # noqa: E402

CELL = 5
MAX_POPS = 1_500_000       # đường vòng xa trên lưới lớn cần nhiều bước tìm hơn mặc định
MAX_PORTS = 400           # xét đủ cổng ở mọi cạnh được phép, không chỉ 14 cổng gần nhất


def wall(mz, rect, doors="TBLR", every=4):
    """Dựng tường dày 3 ô trên viền hình chữ nhật; cạnh nằm trong `doors` có cửa rộng 1 ô, cách nhau `every` ô."""
    x, y, w, h = rect
    i0, i1, j0, j1 = mz._ci(x), mz._ci(x + w), mz._cj(y), mz._cj(y + h)

    def block(i, j):
        if 0 <= i < mz.W and 0 <= j < mz.H:
            mz.line[j * mz.W + i] = 1
    for i in range(i0 - 1, i1 + 2):                      # cạnh trên, dưới
        for side, jc in (("T", j0), ("B", j1)):
            if side in doors and (i - i0) % every == 2 and i0 + 2 < i < i1 - 2:
                continue
            for dj in (-1, 0, 1):
                block(i, jc + dj)
    for j in range(j0 - 1, j1 + 2):                      # cạnh trái, phải
        for side, ic in (("L", i0), ("R", i1)):
            if side in doors and (j - j0) % every == 2 and j0 + 2 < j < j1 - 2:
                continue
            for di in (-1, 0, 1):
                block(ic + di, j)


def audit(boxes, done, walls):
    """Đếm: cặp đường cắt nhau, đường đi xuyên hộp không phải hai đầu của nó, cặp đường chạy chồng/sát nhau,
    đường chạy dọc viền khối."""
    keys = list(done)
    polys = {k: done[k][0] for k in keys}
    bad = set()
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            pa, pb = polys[keys[a]], polys[keys[b]]
            if polylines_cross(pa, pb):
                bad |= {keys[a], keys[b]}
                continue
            for i in range(len(pa) - 1):
                if any(too_close_parallel(pa[i], pa[i + 1], pb[j], pb[j + 1], gap=6) for j in range(len(pb) - 1)):
                    bad |= {keys[a], keys[b]}
                    break
    for k in keys:
        a, b = done[k][3]
        pts = polys[k]
        for n, bx in boxes.items():
            if n in (a, b):
                continue
            if any(seg_box(pts[q], pts[q + 1], bx, 0) for q in range(len(pts) - 1)):
                bad.add(k)
        for (x, y, w, h) in walls:
            edges = [((x, y), (x + w, y)), ((x, y + h), (x + w, y + h)), ((x, y), (x, y + h)), ((x + w, y), (x + w, y + h))]
            if any(too_close_parallel(pts[q], pts[q + 1], e1, e2, gap=6) for q in range(len(pts) - 1) for e1, e2 in edges):
                bad.add(k)
    return bad


def plen(pts):
    return sum(abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)) + 60 * (len(pts) - 2)


def route_shortest(mz, e):
    """Thử mọi phương án (cạnh ra/vào) của một đường, giữ phương án ngắn và ít góc bẻ nhất."""
    tries = e["tries"]
    if len(tries) == 1:
        sa, sb, fa, fb = tries[0]
        return mz.route(e["a"], e["b"], sides_a=sa, sides_b=sb, fixed_a=fa, fixed_b=fb, max_pops=MAX_POPS, max_ports=MAX_PORTS)
    snap_line, snap_ports = mz.line[:], {k: list(v) for k, v in mz.used_ports.items()}
    best = None
    for n, t in enumerate(tries):
        sa, sb, fa, fb = t
        res = mz.route(e["a"], e["b"], sides_a=sa, sides_b=sb, fixed_a=fa, fixed_b=fb, max_pops=MAX_POPS, max_ports=MAX_PORTS)
        if not res and os.environ.get("ERD_DEBUG_EDGE") and os.environ["ERD_DEBUG_EDGE"] in str(e["key"]):
            print("   thử", t, "-> không đi được", flush=True)
        if res:
            c = plen(res[0]) + (250 if n and fa is None else 0)   # ưu tiên đầu dây nằm đúng hàng cột khoá ngoại
            if os.environ.get("ERD_DEBUG_EDGE") and os.environ["ERD_DEBUG_EDGE"] in str(e["key"]):
                print("   thử", t, "->", round(c), res[1], res[2], res[0][:2], res[0][-2:], flush=True)
            if best is None or c < best[0] - 1:
                best = (c, t)
            mz.line[:] = snap_line
            mz.used_ports = {k: list(v) for k, v in snap_ports.items()}
    if best is None:
        return None
    sa, sb, fa, fb = best[1]
    return mz.route(e["a"], e["b"], sides_a=sa, sides_b=sb, fixed_a=fa, fixed_b=fb, max_pops=MAX_POPS, max_ports=MAX_PORTS)


def route_all(boxes, edges, walls=(), wall_doors=None, attempts=40, seed=11, tag="", spacing=1, pin_internal=False, polish=0):
    """edges: [{key, a, b, tries: [(sides_a, sides_b, fixed_a, fixed_b), ...]}] -> {key: (pts, side_a, side_b, (a, b))}.
    Thử nhiều thứ tự; chỉ trả về khi mọi đường đi được và kiểm tra không còn lỗi."""
    rng = random.Random(seed)

    def dist(e):
        a, b = boxes[e["a"]], boxes[e["b"]]
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    # quan hệ nội bộ đi trước để giữ đường ngắn giữa bảng cha – con; đường tham chiếu đi sau
    order = sorted(edges, key=lambda e: (1 if e.get("cross") else 0, dist(e)))
    priority = []
    best = None
    good, n_ok = None, 0

    def cost(done):
        tot = 0
        for pts, *_ in done.values():
            tot += sum(abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            tot += 60 * (len(pts) - 2)
        return tot
    for it in range(attempts):
        mz = Maze(boxes, cell=CELL, margin=8, stub_cells=5, spacing=spacing, bend=8, port_gap=2)
        for k, r in enumerate(walls):
            wall(mz, r, doors=(wall_doors[k] if wall_doors else "TBLR"))
        done, fail = {}, []
        for e in order:
            res = route_shortest(mz, e)
            if res is None:
                fail.append(e)
            else:
                pts, s1, s2 = res
                done[e["key"]] = (pts, s1, s2, (e["a"], e["b"]))
        bad = set() if fail else audit(boxes, done, walls)
        n_bad = len(fail) + len(bad)
        print(f"  {tag} lần {it}: {len(fail)} đường không đi được, {len(bad)} đường lỗi kiểm tra "
              f"{[e['key'] for e in fail][:6]}", flush=True)
        if best is None or n_bad < best[0]:
            best = (n_bad, done)
        if n_bad == 0:
            c = cost(done)
            print(f"  {tag} lần {it}: lời giải hợp lệ, độ dài+góc = {c:.0f}", flush=True)
            if good is None or c < good[0]:
                good = (c, done)
            n_ok += 1
            if n_ok > polish:
                return good[1]
            order = list(edges) if not pin_internal else order
            rng.shuffle(order)
            if pin_internal:
                order = [e for e in order if not e.get("cross")] + [e for e in order if e.get("cross")]
            continue
        culprits = fail + [e for e in edges if e["key"] in bad]
        for e in culprits:
            if e not in priority:
                priority.append(e)
        pri = list(priority)
        rng.shuffle(pri)
        noise = 0.6 if it % 4 else 1.6
        rest = sorted([e for e in edges if e not in pri], key=lambda e: dist(e) * (1 - noise / 2 + noise * rng.random()))
        k = rng.randint(0, len(pri))
        order = pri[:k] + rest[:rng.randint(0, len(rest))] + pri[k:]
        order += [e for e in edges if e not in order]
        if pin_internal:   # quan hệ trong cùng database luôn đi trước, giữ đường ngắn gọn
            order = [e for e in order if not e.get("cross")] + [e for e in order if e.get("cross")]
    if good:
        return good[1]
    if os.environ.get("ERD_SHOW_BEST"):     # chỉ để xem chỗ nghẽn: trả lời giải tốt nhất dù còn thiếu đường
        print(f"  {tag}: XEM THỬ lời giải còn {best[0]} lỗi", flush=True)
        return best[1]
    raise RuntimeError(f"{tag}: không đi được dây sạch sau {attempts} lần (tốt nhất còn {best[0]} lỗi)")


def anchor(prefix, box, p):
    x, y, w, h = box
    return (f"{prefix}X={(p[0] - x) / w:.4f};{prefix}Y={(p[1] - y) / h:.4f};{prefix}Dx=0;{prefix}Dy=0;"
            f"{prefix}Perimeter=0;")
