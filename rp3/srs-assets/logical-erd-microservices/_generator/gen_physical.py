"""Physical ERD: mỗi database một sơ đồ, dữ liệu lấy từ schema thật sau khi chạy hết Flyway migration
(physical_schema.json, sinh bằng introspect_flyway.py).

Mỗi bảng: đủ mọi cột · kiểu PostgreSQL · NOT NULL · default; cuối bảng là index, unique nhiều cột / có điều kiện, CHECK.
Khoá:  PK · FK = khoá ngoại có ràng buộc trong database · (FK) = id tham chiếu chỉ do code đảm bảo · UQ = unique.
Đường: nét liền = khoá ngoại thật (ghi ON DELETE nếu khác NO ACTION); nét đứt xám = tham chiếu trong cùng database
nhưng không có ràng buộc. Tham chiếu sang database khác không vẽ đường (chỉ đánh dấu (FK)).

Chạy: python gen_physical.py [01 04 …]  →  ../../physical-erd-microservices/NN-<db>.drawio + .png"""
import html
import json
import os
import re
import sys

import gen
from gen import D, SVC, FONT, REL, ENT, crow, STRAIGHT_SOLID, label_pos
from route import route_all, anchor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(gen.OUT), "physical-erd-microservices")
SCHEMA = json.load(open(os.path.join(HERE, "physical_schema.json"), encoding="utf-8"))
ROW, HEAD, CH = 20, 28, 6.7               # cao dòng, cao đầu bảng, bề rộng ước lượng một ký tự (font 12)
CODE_REF = STRAIGHT_SOLID.replace("strokeColor=#333333;", "strokeColor=#8A8A8A;") + "dashed=1;dashPattern=7 5;"

# thứ tự file giống bộ Logical ERD; mỗi database: các cột bảng (trái → phải, trên → dưới)
DBS = {
    "user_db": ("01", [["user_profiles"]]),
    "auth_db": ("02", [["auth_accounts"], ["refresh_tokens", "social_identities"], ["email_otps"],
                       ["system_settings", "system_setting_audits"]]),
    "store_db": ("03", [["stores"], ["system_settings", "system_setting_audits"]]),
    "locker_db": ("04", [["repair_logs", "report_attachments", "locker_report_ratings"], ["locker_reports", "locker_boxes"],
                         ["maintenance_schedules", "maintenance_inspection_logs", "drone_delivery_requests"],
                         ["drone_units", "drone_devices", "drone_iot_logs", "drone_maintenance_logs"],
                         ["lockers", "technician_presences"], ["system_settings", "system_setting_audits"]]),
    "iot_db": ("05", [["gateway_devices", "device_statuses", "cabinet_hardware_configs"],
                      ["cabinet_control_logs", "ble_signing_keys", "ble_test_grants"],
                      ["box_access_logs", "access_attempts", "box_hardware_status"],
                      ["system_settings", "system_setting_audits"]]),
    "order_db": ("06", [["drone_technician_presence", "order_details", "order_status_history", "order_ratings", "order_complaints"],
                        ["orders", "promotion_usages"],
                        ["drone_missions", "drone_delivery_sessions", "drone_locker_comm_logs", "drone_pickups", "drone_pickup_offers"],
                        ["drone_parcel_incidents", "drone_incident_evidence", "drone_incident_timeline",
                         "drone_incident_resolution_proposals"],
                        ["promotions", "promotion_claims"],
                        ["drone_flight_blocks", "drone_flight_track_points", "drone_station_suspensions",
                         "drone_station_suspension_logs"],
                        ["system_settings", "system_setting_audits"]]),
    "payment_db": ("07", [["payments", "refunds"], ["wallets", "wallet_transactions"], ["withdrawal_requests", "user_bank_accounts"],
                          ["system_settings", "system_setting_audits"]]),
    "loyalty_db": ("08", [["loyalty_accounts"], ["point_transactions"], ["system_settings", "system_setting_audits"]]),
    "notification_db": ("09", [["notifications"], ["fcm_tokens"]]),
    "assistant_db": ("10", [["assistant_conversations", "assistant_messages"], ["kb_documents", "kb_chunks"], ["eval_cases"],
                            ["system_settings", "system_setting_audits"]]),
}
TABLE_ENT = {v["table"]: k for k, v in ENT.items()}


def short_type(t, default):
    t = (t.replace("character varying", "varchar").replace("timestamp without time zone", "timestamp")
         .replace("timestamp with time zone", "timestamptz").replace("double precision", "double").replace("character(", "char("))
    if default and default.startswith("nextval("):
        return {"bigint": "bigserial", "integer": "serial"}.get(t, t), None
    return t, default


def short_default(dv):
    if dv is None:
        return ""
    dv = re.sub(r"::[a-z ]+(\[\])?(\(\d+\))?", "", dv).replace("ARRAY[", "[")
    dv = {"CURRENT_TIMESTAMP": "now()", "now()": "now()"}.get(dv, dv)
    return ("= " + dv) if len(dv) <= 22 else "= " + dv[:20] + "…"


def clean_sql(s):
    s = re.sub(r"::(text|character varying|bigint|integer|numeric)(\[\])?", "", s)
    s = s.replace("ARRAY[", "[")
    s = re.sub(r"\((\w+)\)", r"\1", s)                # (type) = 'X'  →  type = 'X'
    s = re.sub(r"= ANY \(\(?\[(.*?)\]\)?\)", r"IN (\1)", s)    # = ANY (ARRAY[...])  →  IN (...)
    while s.startswith("(") and s.endswith(")") and _balanced(s[1:-1]):
        s = s[1:-1]
    return s


def _balanced(s):
    n = 0
    for ch in s:
        n += {"(": 1, ")": -1}.get(ch, 0)
        if n < 0:
            return False
    return n == 0


def esc(s):
    return s          # ô bảng là chữ thường (không html): D.v đã escape cho XML, không cần thêm


def table_rows(db, tname):
    t = SCHEMA[db]["tables"][tname]
    real_fk = {f["cols"][0]: f for f in t["fks"] if len(f["cols"]) == 1}
    uq1 = {u["cols"][0] for u in t["uniques"] if len(u["cols"]) == 1}
    for ix in t["indexes"]:
        m = re.search(r"USING (\w+) \(([^()]*)\)( WHERE .*)?$", ix["def"])
        if ix["unique"] and m and "," not in m.group(2) and not m.group(3):
            uq1.add(m.group(2).strip())
    ent = TABLE_ENT.get(tname)
    code_ref = {}
    for c, col, p, _ in REL:
        if c == ent:
            code_ref[col] = p
    rows = []
    for c in t["columns"]:
        keys = []
        if c["name"] in t["pk"]:
            keys.append("PK")
        if c["name"] in real_fk:
            keys.append("FK")
        elif c["name"] in code_ref:
            keys.append("(FK)")
        if c["name"] in uq1 and "PK" not in keys:
            keys.append("UQ")
        typ, dv = short_type(c["type"], c["default"])
        rows.append(("col", ", ".join(keys), c["name"], typ, ("NOT NULL" if c["notnull"] and "PK" not in keys else ""),
                     short_default(dv)))
    order = {"PK": 0, "FK": 1, "(FK)": 1}
    rows.sort(key=lambda r: min([order.get(k.strip(), 2) for k in r[1].split(",")] or [2]) if r[1] else 2)
    extra = []
    for u in t["uniques"]:
        if len(u["cols"]) > 1:
            extra.append(("idx", "UQ", "(" + ", ".join(u["cols"]) + ")", "", "", ""))
    for ix in t["indexes"]:
        m = re.search(r"USING (\w+) \((.*?)\)( WHERE (.*))?$", ix["def"])
        cols, where = m.group(2), m.group(4)
        if ix["unique"] and "," not in cols and not where:
            continue                                   # đã ghi UQ ngay ở cột
        how = ("WHERE " + clean_sql(where)) if where else ("" if m.group(1) == "btree" else m.group(1))
        extra.append(("idx", "UQ" if ix["unique"] else "IDX", "(" + clean_sql(cols) + ")", how, "", ""))
    for ck in t["checks"]:
        extra.append(("idx", "CK", clean_sql(ck["def"].replace("CHECK ", "")), "", "", ""))
    return rows + extra, real_fk, code_ref, t


def draw_table(d, tname, rows, x, y, head, stroke):
    kw = 62
    nw = max(150, max(CH * len(r[2]) for r in rows if r[0] == "col") + 18)
    iw = max([CH * len(r[2]) + 18 for r in rows if r[0] == "idx"] + [0])
    tw = max(96, max([CH * len(r[3]) + 14 for r in rows if r[0] == "col"]))
    dw = max([6.4 * len(r[5]) + 14 for r in rows] + [0])
    nnw = 70
    # dòng index: danh sách cột tràn sang ô kiểu, điều kiện WHERE tràn sang ô default – nới cho vừa
    if iw > nw + tw:
        nw = iw - tw
    ww = max([7.0 * len(r[3]) + 20 for r in rows if r[0] == "idx"] + [0])
    if ww > nnw + dw:
        dw = ww - nnw
    w = kw + nw + tw + nnw + dw
    h = HEAD + ROW * len(rows)
    tid = d.v(tname, x, y, w, h,
              f"shape=table;startSize={HEAD};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
              f"align=center;resizeLast=1;html=1;whiteSpace=wrap;fontSize=13;fillColor={head};swimlaneFillColor=#FFFFFF;"
              f"strokeColor={stroke};{FONT}")
    base = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" + FONT
    rid = {}
    for i, (kind, key, name, typ, nn, dv) in enumerate(rows):
        fill = "#F3F3F3" if kind == "idx" else "none"
        r = d.v("", 0, HEAD + i * ROW, w, ROW, "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
                f"fillColor={fill};collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;strokeColor=inherit;"
                "top=0;left=0;right=0;bottom=0;fontSize=12;", parent=tid, grow=False)
        if kind == "col":
            rid[name] = i
        kc = "#1565C0" if "(FK)" in key else ("#6A6A6A" if kind == "idx" else "#000000")
        d.v(esc(key), 0, 0, kw, ROW, base + f"align=center;fontStyle=1;fontColor={kc};", parent=r, grow=False)
        if kind == "col":
            fs = 4 if "PK" in key else (2 if "FK" in key else 0)
            d.v(esc(name), kw, 0, nw, ROW, base + f"align=left;spacingLeft=6;fontStyle={fs};", parent=r, grow=False)
            d.v(esc(typ), kw + nw, 0, tw, ROW, base + "align=left;spacingLeft=4;fontColor=#444444;", parent=r, grow=False)
            d.v(nn, kw + nw + tw, 0, nnw, ROW, base + "align=left;spacingLeft=2;fontSize=10;fontColor=#B23B3B;", parent=r, grow=False)
            d.v(esc(dv), kw + nw + tw + nnw, 0, dw, ROW, base + "align=left;spacingLeft=2;fontSize=11;fontColor=#777777;",
                parent=r, grow=False)
        else:   # index / ràng buộc: cùng 5 ô như dòng cột (draw.io bắt mọi dòng cùng số ô); chữ tràn sang ô trống kế bên
            vis = base.replace("overflow=hidden;", "overflow=visible;")
            d.v(esc(name), kw, 0, nw, ROW, vis + "align=left;spacingLeft=6;fontColor=#444444;", parent=r, grow=False)
            d.v("", kw + nw, 0, tw, ROW, base, parent=r, grow=False)
            d.v(esc(typ), kw + nw + tw, 0, nnw, ROW, vis + "align=left;spacingLeft=2;fontSize=11;fontColor=#777777;",
                parent=r, grow=False)
            d.v("", kw + nw + tw + nnw, 0, dw, ROW, base, parent=r, grow=False)
    return tid, rid, w, h


def build(db):
    num, cols = DBS[db]
    meta = SCHEMA[db]
    svc = meta["service"]
    tables = [t for col in cols for t in col]
    assert sorted(tables) == sorted(meta["tables"]), (db, set(tables) ^ set(meta["tables"]))
    _, _, fill, stroke, head, _ = SVC[svc]
    d = D(f"{num}-{db}")
    x0, y0, MARGIN, COLGAP, VGAP = 60, 90, 110, 170, 80
    info = {t: table_rows(db, t) for t in tables}
    # đo trước bề rộng từng bảng để xếp cột
    probe = D("_probe")
    widths = {t: draw_table(probe, t, info[t][0], 0, 0, head, stroke)[2] for t in tables}
    pos, tids, rids = {}, {}, {}
    x = x0 + MARGIN
    t_top = y0 + 90
    heights = []
    for col in cols:
        y = t_top
        cw = max(widths[t] for t in col)
        for t in col:
            tid, rid, w, h = draw_table(d, t, info[t][0], x, y, head, stroke)
            tids[t], rids[t], pos[t] = tid, rid, (x, y, w, h)
            y += h + VGAP
        heights.append(y - VGAP)
        x += cw + COLGAP
    right = max(x - COLGAP + MARGIN, x0 + 900)
    bottom = max(heights) + 110
    box = (f'<mxCell id="svcbox" value="" style="rounded=1;arcSize=1.2;fillColor={fill};strokeColor={stroke};strokeWidth=3;html=1;" '
           f'vertex="1" parent="1"><mxGeometry x="{x0}" y="{y0}" width="{right - x0}" height="{bottom - y0}" as="geometry"/></mxCell>')
    title = (f'<mxCell id="svctitle" value="{html.escape(f"<b>{db}</b>  ·  schema {meta["schema"]}  ·  PostgreSQL 16  ·  {svc}", quote=True)}" '
             f'style="text;html=1;align=left;verticalAlign=middle;fontSize=20;fontColor={stroke};{FONT}" vertex="1" parent="1">'
             f'<mxGeometry x="{x0 + 20}" y="{y0 + 12}" width="{right - x0 - 40}" height="36" as="geometry"/></mxCell>')
    d.cells[0:0] = [box, title]
    d.b[0], d.b[1], d.b[2], d.b[3] = min(d.b[0], x0), min(d.b[1], y0), max(d.b[2], right), max(d.b[3], bottom)
    d.v(f"<b>Physical ERD – {db}</b>", x0, 20, right - x0, 34, "text;html=1;align=left;verticalAlign=middle;fontSize=24;" + FONT)

    # ── quan hệ trong database: khoá ngoại thật + tham chiếu chỉ do code đảm bảo ──
    ci_of = {t: i for i, col in enumerate(cols) for t in col}
    edges, seen = [], set()
    for t in tables:
        rows, real_fk, code_ref, tinfo = info[t]
        for colname, f in real_fk.items():
            edges.append({"a": t, "b": f["ref"], "col": colname, "real": True, "on_delete": f["on_delete"]})
            seen.add((t, colname))
        for colname, pent in code_ref.items():
            ptab = ENT[pent]["table"]
            if (t, colname) not in seen and ptab in pos and colname in rids[t]:
                edges.append({"a": t, "b": ptab, "col": colname, "real": False, "on_delete": None})
    for e in edges:
        a, b, colname = e["a"], e["b"], e["col"]
        yf = pos[a][1] + HEAD + ROW * rids[a][colname] + ROW / 2
        colc = cols[ci_of[a]]
        stacked = ci_of[a] == ci_of[b] and abs(colc.index(a) - colc.index(b)) == 1
        tries = []
        if stacked:
            down = pos[b][1] > pos[a][1]
            tries.append(("B" if down else "T", "T" if down else "B", None, None))
        tries += [("LR", "LR", yf, None), ("LR", "LRTB", yf, None), ("LRTB", "LRTB", None, None)]
        e.update({"key": (a, colname), "tries": tries, "cross": False})
    boxes = dict(pos)
    boxes["_title"] = (x0 + 16, y0 + 8, 11 * len(f"{db}  ·  schema {meta['schema']}  ·  PostgreSQL 16  ·  {svc}") + 10, 40)
    if edges:
        done = None
        for sp in (2, 1):
            try:
                done = route_all(boxes, edges, walls=[(x0, y0, right - x0, bottom - y0)], wall_doors=[""], tag=db,
                                 pin_internal=False, polish=4, attempts=int(os.environ.get("ERD_ATTEMPTS", 40)), spacing=sp)
                break
            except RuntimeError:
                if sp == 1:
                    raise
        walls = [(x0, y0, right - x0, bottom - y0)]
        for e in edges:
            pts = done[e["key"]][0]
            tinfo = SCHEMA[db]["tables"][e["a"]]
            col = next(c for c in tinfo["columns"] if c["name"] == e["col"])
            one = e["col"] in tinfo["pk"] or any(u["cols"] == [e["col"]] for u in tinfo["uniques"])
            s, t = crow(not one, col["notnull"])
            label = "" if not e["real"] or e["on_delete"] == "NO ACTION" else f"ON DELETE {e['on_delete']}"
            style = (STRAIGHT_SOLID + "fontSize=11;fontColor=#333333;labelBackgroundColor=#FFFFFF;") if e["real"] else CODE_REF
            others = [done[k][0] for k in done if k != e["key"]]
            d.e(tids[e["a"]], tids[e["b"]], style + f"startArrow={s};endArrow={t};" + anchor("exit", boxes[e["a"]], pts[0])
                + anchor("entry", boxes[e["b"]], pts[-1]), label=label, points=pts[1:-1],
                lpos=label_pos(pts, walls, list(pos.values()), others, label) if label else None)
    os.makedirs(OUT, exist_ok=True)
    gen.OUT = OUT
    return d.save()


if __name__ == "__main__":
    only = sys.argv[1:]
    failed = []
    for db, (num, _) in DBS.items():
        if only and num not in only:
            continue
        try:
            print(build(db))
        except RuntimeError as ex:
            failed.append(str(ex))
    for f in failed:
        print("LỖI:", f)
    sys.exit(1 if failed else 0)
