"""Logical ERD v2 (new folder, the original files are not touched).

* table style as in the SDD database diagrams: light blue header, blue-grey border, PK / FK / (FK) in red,
  PK name underlined, FK name italic, data type right-aligned in grey; database frame dashed grey;
* the wallet is no longer part of the system: wallets, wallet_transactions and withdrawal_requests removed;
* every database whose service keeps admin-editable business rules (ADR-0005, e.g. unit prices) shows its
  system_settings and system_setting_audits tables, as created by the Flyway migrations.
"""
import copy
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.dirname(HERE)                                              # logical-erd-microservices-v2
SRC = os.path.join(os.path.dirname(DST), "logical-erd-microservices")   # original version (read only)
ROOT = os.path.abspath(os.path.join(DST, "..", "..", "..", ".."))

REMOVED_TABLES = {"wallets", "wallet_transactions", "withdrawal_requests", "Wallet",
                  "drone_delivery_requests",      # old drone request flow, replaced by orders + drone_missions
                  "ble_test_grants", "ble_signing_keys"}          # Bluetooth open test, not part of the system
SETTINGS = [("system_settings", [("PK", "setting_key", "varchar(150)"), ("", "setting_value", "varchar(4000)"),
                                 ("", "updated_by_user_id", "bigint"), ("", "updated_at", "timestamp")]),
            ("system_setting_audits", [("PK", "id", "bigint"), ("", "setting_key", "varchar(150)"),
                                       ("", "old_value", "varchar(4000)"), ("", "new_value", "varchar(4000)"),
                                       ("", "actor_user_id", "bigint"), ("", "changed_at", "timestamp")])]
# service of each database file -> it must have the settings tables if its Flyway migrations create them
FILES = {"01-user-service": "user", "02-auth-service": "auth", "03-store-service": "store",
         "04-locker-service": "locker", "05-iot-service": "iot", "06-order-service": "order",
         "07-payment-service": "payment", "08-loyalty-service": "loyalty", "09-notification-service": "notification",
         "10-assistant-service": "assistant"}

HEAD, BORDER, KEY_RED, TYPE_GREY = "#DAE8FC", "#6C8EBF", "#C00000", "#555555"


def has_settings(svc):
    mig = os.path.join(ROOT, "backend", f"{svc}-service", "src", "main", "resources", "db", "migration")
    return any(re.search(r"CREATE TABLE[^;(]*system_settings\b", open(os.path.join(mig, f), encoding="utf-8").read())
               for f in os.listdir(mig) if f.endswith(".sql"))


def sset(style, **kv):
    """set / replace keys of a draw.io style string (key=None removes it)."""
    parts = [p for p in (style or "").split(";") if p]
    out, seen = [], set()
    for p in parts:
        k = p.split("=", 1)[0]
        if k in kv:
            seen.add(k)
            if kv[k] is not None:
                out.append(f"{k}={kv[k]}")
        else:
            out.append(p)
    out += [f"{k}={v}" for k, v in kv.items() if k not in seen and v is not None]
    return ";".join(out) + ";"


def label(c):
    return re.sub(r"<[^>]+>", "", c.get("value") or "").split("(")[0].strip()


def geo(c):
    g = c.find("mxGeometry")
    return [float(g.get(k, 0)) for k in ("x", "y", "width", "height")]


def restyle(root):
    """Style of docs/rp4/sdd-assets/drawio/db_order_db.drawio; names, columns and layout are unchanged."""
    cells = list(root.iter("mxCell"))
    kids = {}
    for c in cells:
        kids.setdefault(c.get("parent"), []).append(c)
    for c in cells:
        st = c.get("style") or ""
        if re.search(r"shape=table(;|$)", st) or (st.startswith("swimlane") and c.get("parent") == "1"):
            external = "_db)" in (c.get("value") or "")        # table of another database (reference only)
            c.set("style", sset(st, fillColor=HEAD, strokeColor="#999999" if external else BORDER,
                                swimlaneFillColor="#FFFFFF", fontColor="#000000", strokeWidth="1", fontSize="12",
                                columnLines="0", rowLines="0", dashed="1" if external else None))
        elif "shape=tableRow" in st:
            c.set("style", sset(st, fillColor="none", strokeColor="inherit"))
            row = sorted(kids.get(c.get("id"), []), key=lambda k: geo(k)[0])
            if len(row) >= 3:
                key, name, typ = row[0], row[1], row[-1]
                kv = key.get("value") or ""
                key.set("style", sset(key.get("style"), fontColor=KEY_RED, fontStyle="1", align="left", spacingLeft="6"))
                fs = (4 if "PK" in kv else 0) + (2 if "FK" in kv else 0)
                name.set("style", sset(name.get("style"), fontStyle=str(fs), fontColor="#000000"))
                typ.set("style", sset(typ.get("style"), align="right", spacingRight="8", spacingLeft=None,
                                      fontColor=TYPE_GREY, fontStyle="0"))
        elif "partialRectangle" in st and (c.get("value") or "") in ("PK", "FK", "(FK)", "PK, (FK)"):
            c.set("style", sset(st, fontColor=KEY_RED, fontStyle="1"))
        if "partialRectangle" in st and (c.get("value") or "") == "PK, (FK)":
            c.set("style", sset(c.get("style"), fontSize="9", spacingLeft="2"))
        elif c.get("parent") == "1" and st.startswith("rounded=1;arcSize"):      # database frame
            c.set("style", sset(st, rounded="0", arcSize=None, dashed="1", fillColor="#F9F9F9", strokeColor="#999999",
                                strokeWidth="1"))
        elif c.get("parent") == "1" and st.startswith("text;") and "fontColor" in st:   # database title
            size = int(re.search(r"fontSize=(\d+)", st).group(1)) if "fontSize=" in st else 15
            c.set("style", sset(st, fontColor="#000000", fontSize="15" if size < 28 else str(size)))
        elif c.get("edge") == "1":
            ns = sset(st, strokeColor="#333333", strokeWidth="1")
            if "fontColor" in ns:
                ns = sset(ns, fontColor="#555555")
            c.set("style", ns)


def remove_tables(root, names):
    graph = root.find(".//root")
    cells = list(graph.iter("mxCell"))
    kids = {}
    for c in cells:
        kids.setdefault(c.get("parent"), []).append(c)
    gone = set()

    def walk(cid):
        gone.add(cid)
        for k in kids.get(cid, []):
            walk(k.get("id"))
    removed = []
    for c in cells:
        if c.get("parent") == "1" and c.get("vertex") == "1" and label(c) in names:
            removed.append((label(c), geo(c)))
            walk(c.get("id"))
    for c in cells:
        if c.get("edge") == "1" and (c.get("source") in gone or c.get("target") in gone):
            gone.add(c.get("id"))
    for c in cells:
        if c.get("id") in gone:
            graph.remove(c)
    if removed:                                    # reference tables of another db left without any link
        cells = list(graph.iter("mxCell"))
        kids = {}
        for c in cells:
            kids.setdefault(c.get("parent"), []).append(c)
        owner = {}
        for c in cells:
            if c.get("parent") == "1" and "_db)" in (c.get("value") or ""):
                stack = [c.get("id")]
                while stack:
                    x = stack.pop()
                    owner[x] = c.get("id")
                    stack += [k.get("id") for k in kids.get(x, [])]
        linked = {owner.get(c.get(k)) for c in cells if c.get("edge") == "1" for k in ("source", "target")}
        orphan = {o for o in set(owner.values()) if o not in linked}
        for c in cells:
            if owner.get(c.get("id")) in orphan:
                graph.remove(c)
    return removed


def fit_frames(root, removed):
    """Shrink only the frames that held a removed table."""
    cells = list(root.iter("mxCell"))
    frames = [c for c in cells if c.get("parent") == "1" and c.get("vertex") == "1"
              and (c.get("style") or "").startswith("rounded=")]
    tables = [geo(c) for c in cells if c.get("parent") == "1" and re.search(r"shape=table(;|$)", c.get("style") or "")]
    texts = [c for c in cells if c.get("parent") == "1" and (c.get("style") or "").startswith("text;")]
    for f in frames:
        fx, fy, fw, fh = geo(f)
        held = any(fx <= r[0] and r[0] + r[2] <= fx + fw and fy <= r[1] and r[1] + r[3] <= fy + fh for _, r in removed)
        inside = [t for t in tables if fx <= t[0] and t[0] + t[2] <= fx + fw and fy <= t[1] and t[1] + t[3] <= fy + fh]
        if not held or not inside:
            continue
        top = min(t[1] for t in inside) - 70
        bottom = max(t[1] + t[3] for t in inside) + 40
        for c in cells:                           # keep relationship lines that run inside the frame inside it
            arr = c.find("mxGeometry/Array") if c.get("edge") == "1" else None
            if arr is not None:
                for q in arr:
                    qx, qy = float(q.get("x", 0)), float(q.get("y", 0))
                    if fx <= qx <= fx + fw and fy <= qy <= fy + fh + 40:
                        bottom = max(bottom, qy + 30)
        g = f.find("mxGeometry")
        new_top = top if top > fy + 30 else fy
        new_bottom = bottom if bottom < fy + fh - 30 else fy + fh
        left = min(t[0] for t in inside) - 50
        right = max(t[0] + t[2] for t in inside) + 50
        new_left = left if left > fx + 30 else fx
        new_right = right if right < fx + fw - 30 else fx + fw
        if new_left != fx:
            for t in texts:
                tx, ty, tw_, th = geo(t)
                if fx <= tx <= fx + fw and fy <= ty <= fy + 60:
                    t.find("mxGeometry").set("x", f"{tx + new_left - fx:g}")
        g.set("x", f"{new_left:g}")
        g.set("width", f"{new_right - new_left:g}")
        if new_top != fy:                         # empty band at the top: move the frame and its title down
            for t in texts:
                tx, ty, tw_, th = geo(t)
                if fx <= tx <= fx + fw and fy <= ty <= fy + 60:
                    t.find("mxGeometry").set("y", f"{ty + new_top - fy:g}")
        g.set("y", f"{new_top:g}")
        g.set("height", f"{new_bottom - new_top:g}")


def add_settings(root, name):
    graph = root.find(".//root")
    cells = list(graph.iter("mxCell"))
    kids = {}
    for c in cells:
        kids.setdefault(c.get("parent"), []).append(c)
    frames = [c for c in cells if c.get("parent") == "1" and c.get("vertex") == "1"
              and (c.get("style") or "").startswith("rounded=")]
    box = max(frames, key=lambda c: geo(c)[2] * geo(c)[3])        # the database frame
    bx, by, bw, bh = geo(box)
    own = [c for c in cells if c.get("parent") == "1" and re.search(r"shape=table(;|$)", c.get("style") or "")
           and "_db)" not in (c.get("value") or "") and bx <= geo(c)[0] <= bx + bw]
    tpl = max(own, key=lambda c: len(kids.get(c.get("id"), [])))
    rows = sorted(kids[tpl.get("id")], key=lambda r: geo(r)[1])
    pk_row = next(r for r in rows if "PK" in (sorted(kids[r.get("id")], key=lambda k: geo(k)[0])[0].get("value") or ""))
    plain = next(r for r in rows if not (sorted(kids[r.get("id")], key=lambda k: geo(k)[0])[0].get("value") or ""))
    tx, ty, tw_, th = geo(tpl)
    start = float(re.search(r"startSize=(\d+)", tpl.get("style")).group(1))
    rh = geo(plain)[3]
    gap = 40
    hs = [start + rh * len(cols) for _, cols in SETTINGS]
    others = [geo(c) for c in cells if c.get("parent") == "1" and re.search(r"shape=table(;|$)", c.get("style") or "")]
    pts = []
    for c in cells:                                  # bends of the relationship lines must stay free
        if c.get("edge") == "1":
            arr = c.find("mxGeometry/Array")
            if arr is not None:
                pts += [(float(q.get("x", 0)), float(q.get("y", 0))) for q in arr]

    def free(rects):
        for (x0, y0, w0, h0) in rects:
            if x0 < bx + 20:
                return False
            for (x1, y1, w1, h1) in others:
                if x0 < x1 + w1 + 30 and x1 < x0 + w0 + 30 and y0 < y1 + h1 + 30 and y1 < y0 + h0 + 30:
                    return False
            for (px, py) in pts:
                if x0 - 30 < px < x0 + w0 + 30 and y0 - 30 < py < y0 + h0 + 30:
                    return False
        return True
    cands = sorted({(geo(c)[0], geo(c)[1] + geo(c)[3] + gap) for c in own}, key=lambda p: (p[1], p[0]))
    best = None
    for (cx, cy) in cands:
        side = [(cx, cy, tw_, hs[0]), (cx + tw_ + gap, cy, tw_, hs[1])]
        stack = [(cx, cy, tw_, hs[0]), (cx, cy + hs[0] + gap, tw_, hs[1])]
        for rects in (side, stack):
            if free(rects):
                bottom_ = max(r[1] + r[3] for r in rects)
                right_ = max(r[0] + r[2] for r in rects)
                grow = max(0, bottom_ + 30 - (by + bh)) + max(0, right_ + 30 - (bx + bw))
                if best is None or (grow, bottom_) < best[0]:
                    best = ((grow, bottom_), rects)
    rects = best[1]
    n = [0]

    def nid():
        n[0] += 1
        return f"set{n[0]}"
    for (tname, cols), (x, y0, _, h) in zip(SETTINGS, rects):
        t = copy.deepcopy(tpl)
        for ch in list(t):
            if ch.tag != "mxGeometry":
                t.remove(ch)
        tid = nid()
        t.set("id", tid)
        t.set("value", tname)
        g = t.find("mxGeometry")
        g.set("x", f"{x:g}"); g.set("y", f"{y0:g}"); g.set("width", f"{tw_:g}"); g.set("height", f"{h:g}")
        graph.append(t)
        for i, (k, cname, ctype) in enumerate(cols):
            src = pk_row if k else plain
            r = copy.deepcopy(src)
            rid = nid()
            r.set("id", rid); r.set("parent", tid)
            r.find("mxGeometry").set("y", f"{start + i * rh:g}")
            graph.append(r)
            parts = sorted(kids[src.get("id")], key=lambda q: geo(q)[0])
            if cname == "id":                    # same notation as the other ids of this file (bigint / bigserial)
                ctype = sorted(kids[pk_row.get("id")], key=lambda q: geo(q)[0])[-1].get("value") or ctype
            for p_, val in zip(parts, (k, cname, ctype)):
                q = copy.deepcopy(p_)
                q.set("id", nid()); q.set("parent", rid); q.set("value", val)
                graph.append(q)
    x = max(r[0] + r[2] for r in rects) + gap
    y0, hmax = min(r[1] for r in rects), max(r[1] + r[3] for r in rects) - min(r[1] for r in rects)
    need_r = x - gap + 30
    need_b = y0 + hmax + 30
    bgeo = box.find("mxGeometry")
    bgeo.set("width", f"{max(bw, need_r - bx):g}")
    bgeo.set("height", f"{max(bh, need_b - by):g}")
    return name


def main():
    os.makedirs(DST, exist_ok=True)
    report = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".drawio"):
            continue
        base = f[:-7]
        tree = ET.parse(os.path.join(SRC, f))
        root = tree.getroot()
        rem = remove_tables(root, REMOVED_TABLES)
        if rem:
            fit_frames(root, rem)
        rem = [n for n, _ in rem]
        svc = FILES.get(base)
        added = bool(svc and has_settings(svc))
        restyle(root)
        if added:
            add_settings(root, base)
        tree.write(os.path.join(DST, f), encoding="utf-8", xml_declaration=False)
        report.append((f, rem, added, svc))
    for r in report:
        print(r)


if __name__ == "__main__":
    main()
