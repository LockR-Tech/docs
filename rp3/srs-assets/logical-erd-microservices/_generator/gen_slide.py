"""Logical ERD bản gọn để chiếu slide ngang (ghi đè ../NN-<service>.drawio + .png) cho các service trong CFG.

Khác bản đầy đủ của gen.py:
  - tên bảng chỉ dạng snake_case (bỏ tên lớp Java)
  - bảng xếp sát (khe hẹp, nhiều cột) cho tỉ lệ ngang; màu theo 01-user-service
  - thực thể tham chiếu: tên bảng + (database gốc), id + cột kèm theo đúng kiểu ở bảng gốc; mỗi bảng chỉ vẽ một lần
  - order-service: bảng orders (102 cột) chỉ giữ các cột chính; các service khác giữ đủ cột
Chạy: py gen_slide.py [05 06 07 ...]   (không đối số = mọi service trong CFG; xuất PNG bằng draw.io desktop, biến DRAWIO)
"""
import html, os, subprocess, sys

import gen
from gen import ENT, REL, M, NN, SVC, D, ROW, HEAD, FONT, TBL, svc_of, INTRA, CROSS, crow, STRAIGHT_SOLID, STRAIGHT_DASH, OUT
from route import route_all, anchor

DRAWIO = os.environ.get("DRAWIO", r"C:\Program Files\draw.io\draw.io.exe")
FILL, STROKE, HEADC = SVC["user-service"][2], SVC["user-service"][3], SVC["user-service"][4]   # màu của user-service

KW, NW, TW = 46, 178, 320            # cột khoá, cột tên, bề ngang bảng
COLGAP, VGAP = 96, 40

# cột kèm theo trong thực thể tham chiếu (cột ở bảng gốc; drone_missions.drone_code chép từ drone_units.code)
REF_EXTRA = {"DroneUnit": ["code"]}

# layout: các cột bảng (trái → phải, trên → dưới)
# refs:   thứ tự thực thể tham chiếu trái → phải (để đường không cắt nhau); None = theo trọng tâm bảng dùng nó
# fixed:  vị trí cố định của thực thể tham chiếu: "left" = sát trái, "manual" = ngay trên đường vẽ tay
# manual: (bảng, cột) vẽ tay một đoạn thẳng đứng từ góc phải bảng lên thực thể tham chiếu, không qua bộ đi dây
CFG = {
    "iot-service": dict(
        layout=[["BleTestGrant", "BleSigningKey"], ["GatewayDevice", "DeviceStatus"],
                ["CabinetControlLog", "BoxHardwareStatus"], ["AccessAttempt", "BoxAccessLog"]],
        refs=["UserProfile", "LockerUnit", "LockerBox", "LockerOrder"],
        title="bottom"),                       # box_access_logs → orders cần lề phải phía trên: tiêu đề khối xuống góc dưới
    # orders lẫn promotions/promotion_claims cùng trỏ tới user_profiles và lockers ⇒ buộc có một chỗ cắt:
    # user_profiles sát trái (claims, presence đi thẳng lên theo lề trái), lockers ngay trên góc phải promotions,
    # promotions → lockers là đoạn thẳng đứng vẽ tay; chỉ orders.user_id cắt qua đoạn này.
    "order-service": dict(
        layout=[["Promotion", "PromotionClaim", "DroneTechnicianPresence"],
                ["PromotionUsage", "OrderDetail", "OrderStatusHistory", "OrderRating", "OrderComplaint"],
                ["LockerOrder", "DronePickup", "DronePickupOffer"],
                ["DroneDeliverySession", "DroneLockerCommLog"],
                ["DroneMission"],
                ["DroneParcelIncident"],
                ["DroneIncidentEvidence", "DroneIncidentTimeline", "DroneIncidentResolutionProposal"]],
        fixed={"UserProfile": "left", "LockerUnit": "manual"}, manual=[("Promotion", "locker_id")],
        # orders có 102 cột – chỉ hiện các cột chính
        show={"LockerOrder": ["id", "user_id", "locker_id", "send_box_id", "store_id", "order_code", "type", "service_category",
                              "status", "payment_status", "delivery_stage", "fulfillment_mode", "receiver_name", "receiver_phone",
                              "total_price", "shipping_fee", "discount", "promotion_code", "points_used", "pin_code",
                              "pickup_deadline", "paid_at", "completed_at", "created_at", "updated_at"]}),
    "payment-service": dict(
        layout=[["UserBankAccount", "WithdrawalRecord"], ["Wallet", "WalletTransaction"], ["PaymentRecord"], ["RefundRecord"]],
        refs=["UserProfile", "LockerOrder"]),
    "loyalty-service": dict(layout=[["LoyaltyAccount"], ["PointTransaction"]], refs=["UserProfile", "LockerOrder"]),
    "assistant-service": dict(
        layout=[["AssistantConversation", "AssistantMessage"], ["KbDocument", "KbChunk"], ["EvalCase"]],
        refs=["UserProfile"]),
}
SHOW = {}


def fields(cls):
    f = gen.ordered_fields(cls)
    if cls in SHOW:
        by = {x["name"]: x for x in f}
        return [by[n] for n in SHOW[cls]]
    return f


def table(d, cls, x, y):
    rows = fields(cls)
    h = HEAD + ROW * len(rows)
    tid = d.v(TBL[cls], x, y, TW, h,
              f"shape=table;startSize={HEAD};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
              f"align=center;resizeLast=1;html=1;whiteSpace=wrap;fontSize=13;fillColor={HEADC};swimlaneFillColor=#FFFFFF;"
              f"strokeColor={STROKE};{FONT}")
    base = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" + FONT
    for i, fl in enumerate(rows):
        r = d.v("", 0, HEAD + i * ROW, TW, ROW, "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;"
                "collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;strokeColor=inherit;top=0;left=0;right=0;"
                "bottom=0;fontSize=12;", parent=tid, grow=False)
        rel = next((rr for rr in REL if rr[0] == cls and rr[1] == fl["name"]), None)
        key = "PK" if fl["pk"] else ("FK" if rel and svc_of[rel[2]] == svc_of[cls] else ("(FK)" if rel else ""))
        if fl["pk"] and rel:
            key = "PK, FK" if svc_of[rel[2]] == svc_of[cls] else "PK, (FK)"
        kcol = "#1565C0" if key.endswith("(FK)") else "#000000"
        d.v(key, 0, 0, KW, ROW, base + f"align=center;fontStyle=1;fontColor={kcol};", parent=r, grow=False)
        style = 4 if fl["pk"] else (2 if key else 0)
        d.v(fl["name"], KW, 0, NW, ROW, base + f"align=left;spacingLeft=6;fontStyle={style};", parent=r, grow=False)
        d.v(fl["type"], KW + NW, 0, TW - KW - NW, ROW, base + "align=left;spacingLeft=4;fontColor=#555555;", parent=r, grow=False)
    return tid, h


RW, RH = 300, 48


def ref_height(cls):
    return RH + ROW * (1 + len(REF_EXTRA.get(cls, [])))


def ref_table(d, cls, x, y):
    """thực thể tham chiếu: hộp xám nét đứt; đầu = tên bảng + (database gốc); id + cột kèm theo với kiểu thật."""
    f = {x_["name"]: x_ for x_ in ENT[cls]["fields"]}
    pk = next(x_ for x_ in ENT[cls]["fields"] if x_["pk"])
    rows = [("PK", pk["name"], pk["type"])] + [("", c, f[c]["type"]) for c in REF_EXTRA.get(cls, [])]
    h = ref_height(cls)
    tid = d.v(f"{TBL[cls]}<br><span style=\"font-weight:normal;font-style:italic;font-size:11px\">({SVC[svc_of[cls]][1]})</span>",
              x, y, RW, h,
              f"shape=table;startSize={RH};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
              f"align=center;resizeLast=1;html=1;whiteSpace=wrap;fontSize=13;fillColor=#E6E6E6;swimlaneFillColor=#FAFAFA;"
              f"strokeColor=#8C8C8C;dashed=1;dashPattern=6 4;fontColor=#444444;{FONT}")
    base = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" + FONT
    for i, (k, n, t) in enumerate(rows):
        r = d.v("", 0, RH + i * ROW, RW, ROW, "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;"
                "collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;",
                parent=tid, grow=False)
        d.v(k, 0, 0, KW + 12, ROW, base + "align=center;fontStyle=1;fontColor=#444444;", parent=r, grow=False)
        d.v(n, KW + 12, 0, 150, ROW, base + f"align=left;spacingLeft=6;fontStyle={4 if k else 2};fontColor=#444444;", parent=r, grow=False)
        d.v(t, KW + 162, 0, RW - KW - 162, ROW, base + "align=left;spacingLeft=4;fontColor=#777777;fontStyle=2;", parent=r, grow=False)
    return tid, h


def build(svc):
    cfg = CFG[svc]
    FNAME, DB, SVC_NAME = SVC[svc][0], SVC[svc][1], svc
    SHOW.clear(); SHOW.update(cfg.get("show", {}))
    MANUAL = cfg.get("manual", [])
    fixed = cfg.get("fixed", {})
    d = D(FNAME)
    cols = cfg["layout"]
    own = [c for col in cols for c in col]
    assert sorted(own) == sorted(c for c in ENT if svc_of[c] == SVC_NAME)
    ci_of = {c: i for i, col in enumerate(cols) for c in col}
    refs = {}                                     # thực thể service khác -> [(con, cột)]  (mỗi thực thể một hộp)
    for c, col, p, _ in CROSS:
        if c in own:
            refs.setdefault(p, []).append((c, col))
    intra = [r for r in INTRA if r[0] in own]
    far = [r for r in intra if abs(ci_of[r[0]] - ci_of[r[2]]) >= 2]

    ref_h = max(ref_height(p) for p in refs)
    n_cross = sum(len(v) for v in refs.values())
    x0, MARGIN = 60, 110
    REF_Y = 70
    y0 = REF_Y + ref_h + 40 + 9 * n_cross
    t_top = y0 + 70 + 9 * len(far)
    pos, tids = {}, {}
    x = x0 + MARGIN
    heights = []
    for col in cols:
        y = t_top
        for c in col:
            tids[c], h = table(d, c, x, y)
            pos[c] = (x, y, TW, h)
            y += h + VGAP
        heights.append(y - VGAP)
        x += TW + COLGAP
    right = x - COLGAP + MARGIN
    bottom = max(heights) + 70
    box = (f'<mxCell id="svcbox" value="" style="rounded=1;arcSize=1.2;fillColor={FILL};strokeColor={STROKE};strokeWidth=3;html=1;" '
           f'vertex="1" parent="1"><mxGeometry x="{x0}" y="{y0}" width="{right - x0}" height="{bottom - y0}" as="geometry"/></mxCell>')
    ty = bottom - 46 if cfg.get("title") == "bottom" else y0 + 10    # góc phải trên (mặc định) hoặc dưới
    title = (f'<mxCell id="svctitle" value="{html.escape(f"<b>{SVC_NAME}</b>  ·  {DB}", quote=True)}" '
             f'style="text;html=1;align=right;verticalAlign=middle;fontSize=20;fontColor={STROKE};{FONT}" vertex="1" parent="1">'
             f'<mxGeometry x="{right - 360}" y="{ty}" width="340" height="36" as="geometry"/></mxCell>')   # góc phải: lề trái để đi dây
    d.cells[0:0] = [box, title]
    d.b[0], d.b[1], d.b[2], d.b[3] = min(d.b[0], x0), min(d.b[1], y0), max(d.b[2], right), max(d.b[3], bottom)
    d.v(f"<b>Logical ERD – {SVC_NAME}</b>", x0, 14, right - x0, 34, "text;html=1;align=left;verticalAlign=middle;fontSize=24;" + FONT)

    def row_y(c, col):
        idx = [f_["name"] for f_ in fields(c)].index(col)
        return pos[c][1] + HEAD + ROW * idx + ROW / 2

    # thực thể tham chiếu: dải trên, mỗi hộp đặt gần trọng tâm các bảng dùng nó
    line_x = pos[MANUAL[0][0]][0] + TW - 35 if MANUAL else None
    if cfg.get("refs"):
        assert sorted(cfg["refs"]) == sorted(refs), (svc, sorted(refs))
    cen = {p: sum(pos[c][0] + TW / 2 for c, _ in users) / len(users) for p, users in refs.items()}
    rest = [p for p in (cfg.get("refs") or sorted(refs, key=lambda p: (cen[p], p))) if p not in fixed]
    placed, xcur = [], x0 + 10
    for p in list(fixed) + rest:
        xx = {"left": x0 + 10, "manual": (line_x or 0) - 55}.get(fixed.get(p), max(xcur, cen[p] - RW / 2))
        placed.append([xx, p])
        xcur = xx + RW + 30
    if placed[-1][0] + RW > right - 10:            # tràn phải: dời sang trái vừa đủ (không đụng hộp cố định)
        xmax = right - 10 - RW
        for i in range(len(placed) - 1, -1, -1):
            if placed[i][1] in fixed:
                break
            placed[i][0] = min(placed[i][0], xmax)
            xmax = placed[i][0] - RW - 30
    refid, refbox = {}, {}
    for xx, p in placed:
        refid[p], h = ref_table(d, p, xx, REF_Y)
        refbox[p] = (xx, REF_Y, RW, h)

    boxes = {c: pos[c] for c in own}
    boxes.update({("ref", p): refbox[p] for p in refbox})
    boxes["_title"] = (right - 20 - (12 * len(f"{SVC_NAME}  ·  {DB}") + 10), ty - 2, 12 * len(f"{SVC_NAME}  ·  {DB}") + 10, 40)
    boxes["_top"] = (x0, -10, right - x0, REF_Y - 18)     # chặn đường vòng lên trên dải tham chiếu
    edges = []
    for c, col, p, mult in intra:
        yf = row_y(c, col)
        colc = cols[ci_of[c]]
        stacked = ci_of[c] == ci_of[p] and abs(colc.index(c) - colc.index(p)) == 1
        tries = []
        if stacked:
            down = pos[p][1] > pos[c][1]
            tries.append(("B" if down else "T", "T" if down else "B", None, None))
        tries += [("LR", "LR", yf, None), ("LR", "LRTB", yf, None), ("LRTB", "LRTB", None, None)]
        edges.append({"key": ("i", c, col), "a": c, "b": p, "tries": tries, "cross": False, "c": c, "col": col, "mult": mult})
    for p, users in refs.items():
        for c, col in users:
            if (c, col) in MANUAL:
                continue
            mult = next(r[3] for r in REL if r[0] == c and r[1] == col)
            yf = row_y(c, col)
            rl, rr = refbox[p][0], refbox[p][0] + refbox[p][2]
            face = "L" if rr < pos[c][0] else ("R" if rl > pos[c][0] + pos[c][2] else "LR")
            top_row = cols[ci_of[c]][0] == c
            edges.append({"key": ("x", c, col), "a": c, "b": ("ref", p), "cross": True, "c": c, "col": col, "mult": mult,
                          "tries": [(face, "LRB", yf, None)] + ([("T", "LRB", None, None)] if top_row else []) + [
                                    ("LR", "LRB", yf, None), ("LRTB", "LRB", None, None)]})
    done = {} if not edges else route_all(boxes, edges, walls=[(x0, y0, right - x0, bottom - y0)], wall_doors=["T"], tag=SVC_NAME,
                     pin_internal=True, polish=int(os.environ.get("ERD_POLISH", 1)),
                     attempts=int(os.environ.get("ERD_ATTEMPTS", 60)), spacing=1)
    for e in edges:
        pts = done[e["key"]][0]
        s, t = crow(e["mult"] == M, NN.get(f"{e['c']}.{e['col']}", False))
        base = STRAIGHT_DASH if e["cross"] else STRAIGHT_SOLID
        dst = refid[e["b"][1]] if e["cross"] else tids[e["b"]]
        d.e(tids[e["a"]], dst, base + f"startArrow={s};endArrow={t};" + anchor("exit", boxes[e["a"]], pts[0])
            + anchor("entry", boxes[e["b"]], pts[-1]), points=pts[1:-1])

    for c, col in MANUAL:                          # vd. promotions.locker_id → lockers: thẳng đứng, không qua bộ đi dây
        p = next(r[2] for r in REL if r[0] == c and r[1] == col)
        mult = next(r[3] for r in REL if r[0] == c and r[1] == col)
        s, t = crow(mult == M, NN.get(f"{c}.{col}", False))
        ex, en = (line_x - pos[c][0]) / TW, (line_x - refbox[p][0]) / RW
        d.e(tids[c], refid[p], STRAIGHT_DASH + f"startArrow={s};endArrow={t};exitX={ex:.4f};exitY=0;exitDx=0;exitDy=0;"
            f"exitPerimeter=0;entryX={en:.4f};entryY=1;entryDx=0;entryDy=0;entryPerimeter=0;")

    path = os.path.join(OUT, FNAME + ".drawio")
    open(path, "w", encoding="utf-8").write(d.xml())
    png = os.path.join(OUT, FNAME + ".png")
    subprocess.run([DRAWIO, "-x", "-f", "png", "-s", "2", "-b", "24", "-o", png, path], check=True, capture_output=True, timeout=240)
    print(path, f"{right - x0 + 0:.0f} x {bottom - 14:.0f}")


if __name__ == "__main__":
    want = sys.argv[1:]
    for svc in CFG:
        if not want or SVC[svc][0][:2] in want:
            build(svc)
