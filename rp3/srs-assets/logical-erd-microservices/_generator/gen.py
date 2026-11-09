"""Logical ERD theo kiểu microservices (database-per-service) cho Lock.R.

Sinh ra trong thư mục cha:
  00-cross-service-overview   sơ đồ tổng quan: mỗi service một khối (bounded context), chỉ thực thể chính,
                              nét liền = FK trong cùng database, nét đứt xanh = id tham chiếu logic sang service khác
  01..10-<service>            mỗi service một sơ đồ: đủ cột của mọi bảng, quan hệ nội bộ nét liền,
                              thực thể tham chiếu (hộp xám nét đứt) cho dữ liệu thuộc service khác

Dữ liệu: entities.json + REL + fk_notnull.json của bộ sinh Report 3 (../../drawio/_generator) – cùng 58 bảng, 70 quan hệ.
Chạy: python gen.py   (cần Chrome; viewer-static.min.js đặt cạnh file này, tải từ viewer.diagrams.net)
"""
import html, json, os, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "drawio", "_generator"))
sys.path.insert(0, SRC)
from erd_data import ENT, REL, M  # noqa: E402
from route import route_all, anchor  # noqa: E402

NN = json.load(open(os.path.join(SRC, "fk_notnull.json"), encoding="utf-8"))
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")

# ───────────────────────── service ─────────────────────────
#            tên file, database, màu nền khối, màu viền, màu đầu bảng, mô tả ngắn
SVC = {
    "user-service": ("01-user-service", "user_db", "#EEF5FD", "#1E6FB8", "#CFE3F7", "Hồ sơ người dùng"),
    "auth-service": ("02-auth-service", "auth_db", "#FDF0F0", "#B23B3B", "#F6D3D3", "Đăng nhập, token, OTP"),
    "store-service": ("03-store-service", "store_db", "#EFF8F0", "#2E7D32", "#CFEBD2", "Cửa hàng / địa điểm đặt tủ"),
    "locker-service": ("04-locker-service", "locker_db", "#FFF6EA", "#C66A00", "#FFE0B8", "Tủ, ô, sự cố, bảo trì, đội drone"),
    "iot-service": ("05-iot-service", "iot_db", "#F4F0FB", "#5E35B1", "#E0D6F5", "Bộ điều khiển tủ, nhật ký thiết bị"),
    "order-service": ("06-order-service", "order_db", "#EAF8FA", "#00838F", "#C4ECF0", "Đơn hàng, khuyến mãi, chuyến bay drone"),
    "payment-service": ("07-payment-service", "payment_db", "#FFFBE8", "#A67C00", "#FBEDB5", "Thanh toán, hoàn tiền, ví"),
    "loyalty-service": ("08-loyalty-service", "loyalty_db", "#FDF0F5", "#AD1457", "#F8D2E2", "Điểm thưởng"),
    "notification-service": ("09-notification-service", "notification_db", "#F3F9EC", "#558B2F", "#DDEFC9", "Thông báo"),
    "assistant-service": ("10-assistant-service", "assistant_db", "#EFF1FA", "#3949AB", "#D5DAF3", "Trợ lý AI (pgvector)"),
}
# cách service gọi nhau / nhận sự kiện (01-overview/architecture.md)
COMM = {
    "auth-service": "Feign → user-service",
    "user-service": "Feign → auth, notification · phát sự kiện admin.data.changed",
    "store-service": "Feign → order-service · phát sự kiện catalog.changed",
    "locker-service": "Feign → iot, user · phát locker.box.*, locker.report.*, locker.schedule.due",
    "iot-service": "MQTT tới tủ · Feign → locker (sơ đồ ô), order",
    "order-service": "Feign → locker, user, notification · phát order.* · nhận order.payment.events",
    "payment-service": "Feign → order · phát payment.*",
    "loyalty-service": "Feign → order · nhận loyalty.order.events (order.completed, payment.refunded)",
    "notification-service": "nhận notification.events (mọi service phát) → in-app, FCM, STOMP",
    "assistant-service": "Feign → order, locker · không dùng RabbitMQ",
}
# cột chép kèm dữ liệu của service khác (đã ghi trong tài liệu): (bảng chép, cột) -> thực thể gốc
COPIED = {("LockerReport", "order_code"): "LockerOrder", ("MaintenanceInspectionLog", "technician_name"): "UserProfile",
          ("DroneMission", "drone_code"): "DroneUnit"}

svc_of = {c: ENT[c]["service"] for c in ENT}
TBL = {c: ENT[c]["table"] for c in ENT}
INTRA = [r for r in REL if svc_of[r[0]] == svc_of[r[2]]]
CROSS = [r for r in REL if svc_of[r[0]] != svc_of[r[2]]]

# ───────────────────────── draw.io ─────────────────────────
class D:
    def __init__(self, name):
        self.name, self.cells, self.n = name, [], 1
        self.b = [1e9, 1e9, -1e9, -1e9]

    def id(self):
        self.n += 1
        return f"c{self.n}"

    def v(self, label, x, y, w, h, style, parent="1", grow=True):
        cid = self.id()
        self.cells.append(f'<mxCell id="{cid}" value="{html.escape(label, quote=True)}" style="{style}" vertex="1" parent="{parent}">'
                          f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
        if grow and parent == "1":
            b = self.b
            b[0], b[1], b[2], b[3] = min(b[0], x), min(b[1], y), max(b[2], x + w), max(b[3], y + h)
        return cid

    def e(self, src, tgt, style, label="", points=(), lpos=None):
        cid = self.id()
        pts = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in points)
        arr = f'<Array as="points">{pts}</Array>' if points else ""
        self.cells.append(f'<mxCell id="{cid}" value="{html.escape(label, quote=True)}" style="{style}" edge="1" parent="1" '
                          f'source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry"'
                          f'{f" x={chr(34)}{lpos:.3f}{chr(34)}" if lpos is not None else ""}>{arr}</mxGeometry></mxCell>')
        return cid

    def xml(self):
        return (f'<mxfile host="app.diagrams.net"><diagram name="{self.name}" id="{self.name}"><mxGraphModel grid="0" page="0" '
                f'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(self.cells)}</root></mxGraphModel>'
                f'</diagram></mxfile>')

    def save(self, scale=2, margin=24):
        path = os.path.join(OUT, self.name + ".drawio")
        open(path, "w", encoding="utf-8").write(self.xml())
        render(path, os.path.join(OUT, self.name + ".png"), self.b, scale, margin)
        return path


def render(drawio, png, b, scale, margin):
    xml = open(drawio, encoding="utf-8").read()
    w, h = int(b[2] - b[0] + 2 * margin + 30), int(b[3] - b[1] + 2 * margin + 30)
    cfg = {"xml": xml, "toolbar": "", "highlight": "none", "nav": False, "resize": False, "zoom": 1, "border": margin, "lightbox": False}
    page = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}</style></head><body>'
            f'<div class="mxgraph" style="width:{w}px" data-mxgraph="{html.escape(json.dumps(cfg), quote=True)}"></div>'
            f"<script>window.DRAWIO_BASE_URL='https://app.diagrams.net';</script>"
            f'<script src="file:///{HERE.replace(os.sep, "/")}/viewer-static.min.js"></script></body></html>')
    hp = os.path.join(HERE, "_render_" + os.path.basename(png) + ".html")
    open(hp, "w", encoding="utf-8").write(page)
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--force-device-scale-factor={scale}", f"--window-size={w},{h}", "--virtual-time-budget=25000",
                        f"--screenshot={png}", "file:///" + hp.replace(os.sep, "/")], check=True, capture_output=True, timeout=240)
    finally:
        os.remove(hp)


FONT = "fontFamily=Helvetica;"
ROW, HEAD = 20, 28
KW, NW, TW = 58, 186, 344          # cột khoá, cột tên, bề ngang bảng (cột kiểu = phần còn lại)


def ordered_fields(cls):
    f = ENT[cls]["fields"]
    fks = [r[1] for r in REL if r[0] == cls]
    pk = [x for x in f if x["pk"]]
    fk = sorted([x for x in f if x["name"] in fks and not x["pk"]], key=lambda x: fks.index(x["name"]))
    rest = [x for x in f if not x["pk"] and x["name"] not in fks]
    return pk + fk + rest


def table(d, cls, x, y, head_fill, stroke, w=TW):
    """hộp bảng logical: đầu bảng = tên bảng (thực thể), mỗi dòng = khoá · tên cột · kiểu. Trả (id bảng, {cột: id dòng}, cao)."""
    rows = ordered_fields(cls)
    h = HEAD + ROW * len(rows)
    tid = d.v(f"{TBL[cls]}  ·  {cls}", x, y, w, h,
              f"shape=table;startSize={HEAD};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
              f"align=center;resizeLast=1;html=1;whiteSpace=wrap;fontSize=13;fillColor={head_fill};swimlaneFillColor=#FFFFFF;"
              f"strokeColor={stroke};{FONT}")
    rid = {}
    for i, fl in enumerate(rows):
        r = d.v("", 0, HEAD + i * ROW, w, ROW, "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;"
                "collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;strokeColor=inherit;top=0;left=0;right=0;"
                "bottom=0;fontSize=12;", parent=tid, grow=False)
        rid[fl["name"]] = r
        rel = next((rr for rr in REL if rr[0] == cls and rr[1] == fl["name"]), None)
        key = "PK" if fl["pk"] else ("FK" if rel and svc_of[rel[2]] == svc_of[cls] else ("(FK)" if rel else ""))
        if fl["pk"] and rel:
            key = "PK, FK" if svc_of[rel[2]] == svc_of[cls] else "PK, (FK)"
        base = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" + FONT
        kcol = "#1565C0" if key.endswith("(FK)") else "#000000"
        d.v(key, 0, 0, KW, ROW, base + f"align=center;fontStyle=1;fontColor={kcol};", parent=r, grow=False)
        style = 4 if fl["pk"] else (2 if key else 0)
        d.v(fl["name"], KW, 0, NW, ROW, base + f"align=left;spacingLeft=6;fontStyle={style};", parent=r, grow=False)
        d.v(fl["type"], KW + NW, 0, w - KW - NW, ROW, base + "align=left;spacingLeft=4;fontColor=#555555;", parent=r, grow=False)
    return tid, rid, h


def ref_table(d, cls, x, y, extra, w=TW - 40):
    """thực thể tham chiếu: hộp xám nét đứt, chỉ id + cột chép kèm; ghi service gốc."""
    pk = next(f for f in ENT[cls]["fields"] if f["pk"])
    rows = [("PK", pk["name"], pk["type"])] + [("", c, "chép kèm") for c in extra]
    s = SVC[svc_of[cls]]
    RH = 48                                   # đầu hộp 2 dòng: tên bảng + service gốc (bảng draw.io bắt mọi dòng cùng số ô)
    h = RH + ROW * len(rows)
    tid = d.v(f"{TBL[cls]}  (tham chiếu)<br><span style=\"font-weight:normal;font-style:italic;font-size:11px\">"
              f"dữ liệu gốc: {svc_of[cls]} · {s[1]}</span>", x, y, w, h,
              f"shape=table;startSize={RH};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
              f"align=center;resizeLast=1;html=1;whiteSpace=wrap;fontSize=13;fillColor=#E6E6E6;swimlaneFillColor=#FAFAFA;"
              f"strokeColor=#8C8C8C;dashed=1;dashPattern=6 4;fontColor=#444444;{FONT}")
    base = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" + FONT
    for i, (k, n, t) in enumerate(rows):
        r = d.v("", 0, RH + i * ROW, w, ROW, "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;"
                "collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;",
                parent=tid, grow=False)
        d.v(k, 0, 0, KW, ROW, base + "align=center;fontStyle=1;fontColor=#444444;", parent=r, grow=False)
        d.v(n, KW, 0, NW - 30, ROW, base + f"align=left;spacingLeft=6;fontStyle={4 if k else 2};fontColor=#444444;", parent=r, grow=False)
        d.v(t, KW + NW - 30, 0, w - KW - NW + 30, ROW, base + "align=left;spacingLeft=4;fontColor=#777777;fontStyle=2;", parent=r, grow=False)
    return tid, h


def crow(child_many, mandatory):
    """ký hiệu chân chim: đầu phía con, đầu phía cha."""
    return ("ERzeroToMany" if child_many else "ERzeroToOne"), ("ERmandOne" if mandatory else "ERzeroToOne")


SOLID = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#333333;strokeWidth=1.6;endFill=0;startFill=0;"
         "endSize=10;startSize=10;jettySize=18;")
DASH = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#1565C0;strokeWidth=1.8;dashed=1;dashPattern=8 5;endFill=0;"
        "startFill=0;endSize=10;startSize=10;jettySize=18;fontSize=11;fontColor=#1565C0;labelBackgroundColor=#FFFFFF;")


def legend(d, x, y, w=560):
    h = 196
    d.v("", x, y, w, h, "rounded=1;arcSize=4;fillColor=#FFFFFF;strokeColor=#9E9E9E;html=1;")
    d.v("<b>Chú thích</b>", x + 14, y + 8, 200, 20, "text;html=1;align=left;fontSize=13;" + FONT)
    items = [("solid", "FK trong cùng database (quan hệ nội bộ của service)"),
             ("dash", "id tham chiếu logic sang service khác – không có FK giữa hai database"),
             ("ref", "thực thể tham chiếu: chỉ id (+ cột chép kèm), dữ liệu gốc ở service khác"),
             ("txt", "PK khoá chính (gạch chân) · FK khoá ngoại cùng DB · (FK) id logic sang service khác"),
             ("txt2", "đầu đường: ┼ đúng một · o┼ không hoặc một · o< không hoặc nhiều")]
    yy = y + 38
    for kind, text in items:
        if kind == "solid":
            a = d.v("", x + 18, yy + 6, 2, 2, "shape=ellipse;fillColor=none;strokeColor=none;")
            b = d.v("", x + 98, yy + 6, 2, 2, "shape=ellipse;fillColor=none;strokeColor=none;")
            d.e(a, b, SOLID + "startArrow=ERzeroToMany;endArrow=ERmandOne;")
        elif kind == "dash":
            a = d.v("", x + 18, yy + 6, 2, 2, "shape=ellipse;fillColor=none;strokeColor=none;")
            b = d.v("", x + 98, yy + 6, 2, 2, "shape=ellipse;fillColor=none;strokeColor=none;")
            d.e(a, b, DASH + "startArrow=ERzeroToMany;endArrow=ERmandOne;")
        elif kind == "ref":
            d.v("", x + 22, yy - 2, 72, 18, "rounded=0;fillColor=#E6E6E6;strokeColor=#8C8C8C;dashed=1;dashPattern=6 4;")
        tx = x + 112 if kind in ("solid", "dash", "ref") else x + 18
        d.v(text, tx, yy - 4, x + w - tx - 10, 22, "text;html=1;align=left;verticalAlign=middle;fontSize=12;whiteSpace=wrap;" + FONT)
        yy += 30
    return h


# ───────────────────────── sơ đồ từng service ─────────────────────────
# các cột bảng (trái → phải, trên → dưới) của từng service
LAYOUT = {
    "user-service": [["UserProfile"]],
    "auth-service": [["AuthAccount"], ["RefreshToken", "SocialIdentity"], ["EmailOtp"]],
    "store-service": [["StoreLocation"]],
    # LockerReport và LockerUnit cùng nằm hàng trên (đều có dây lên dải tham chiếu); LockerBox nối cả hai nên đặt dưới
    # LockerReport, các bảng chỉ nối nội bộ nằm giữa – bố cục này cho phép đi dây không cắt nhau
    "locker-service": [["RepairLog", "ReportAttachment", "LockerReportRating"], ["LockerReport", "LockerBox"],
                       ["MaintenanceSchedule", "MaintenanceInspectionLog", "DroneDeliveryRequest"],
                       ["DroneUnit", "DroneDevice", "DroneIotLog", "DroneMaintenanceLog"], ["LockerUnit", "TechnicianPresence"]],
    "iot-service": [["GatewayDevice", "DeviceStatus"], ["CabinetControlLog", "BleSigningKey"], ["BleTestGrant", "BoxAccessLog"],
                    ["BoxHardwareStatus", "AccessAttempt"]],
    # bảng có dây lên dải tham chiếu đặt đầu cột (hoặc ở cột ngoài cùng) để dây không phải cắt qua quan hệ nội bộ
    "order-service": [["DroneTechnicianPresence", "OrderDetail", "OrderStatusHistory", "OrderRating", "OrderComplaint"],
                      ["LockerOrder", "PromotionUsage"],
                      ["DroneMission", "DroneDeliverySession", "DroneLockerCommLog", "DronePickup", "DronePickupOffer"],
                      ["DroneParcelIncident", "DroneIncidentEvidence", "DroneIncidentTimeline", "DroneIncidentResolutionProposal"],
                      ["Promotion", "PromotionClaim"]],
    "payment-service": [["PaymentRecord", "RefundRecord"], ["UserBankAccount"]],
    "loyalty-service": [["LoyaltyAccount"], ["PointTransaction"]],
    "notification-service": [["NotificationMessage"], ["FcmToken"]],
    "assistant-service": [["AssistantConversation", "AssistantMessage"], ["KbDocument", "KbChunk"], ["EvalCase"]],
}
COLGAP, VGAP = 150, 70
# service nhiều bảng, nhiều đường: khe giữa cột / giữa bảng rộng hơn để đủ chỗ đi dây không cắt nhau
GAPS = {"locker-service": (190, 80), "order-service": (190, 80), "iot-service": (170, 70)}


def per_service(svc):
    fname, db, fill, stroke, head, desc = SVC[svc]
    d = D(fname)
    cols = LAYOUT[svc]
    own = [c for col in cols for c in col]
    assert sorted(own) == sorted(c for c in ENT if svc_of[c] == svc), svc
    ci_of = {c: i for i, col in enumerate(cols) for c in col}
    refs = defaultdict(list)                    # thực thể của service khác -> [(con, cột)]
    for c, col, p, _ in CROSS:
        if c in own:
            refs[p].append((c, col))
    # bảng dùng chung một tham chiếu mà nằm xa nhau (cách ≥ 3 cột): mỗi cụm một bản tham chiếu đặt gần, tránh dây vòng xa
    split = {}
    for p, users in refs.items():
        users = sorted(users, key=lambda u: ci_of[u[0]])
        k, prev = 0, None
        for u in users:
            if prev is not None and ci_of[u[0]] - prev >= 3:
                k += 1
            split.setdefault((p, k), []).append(u)
            prev = ci_of[u[0]]
    refs = split
    incoming = defaultdict(list)                # service khác tham chiếu vào đây
    for c, col, p, _ in CROSS:
        if p in own:
            incoming[svc_of[c]].append(f"{TBL[c]}.{col} → {TBL[p]}")
    intra = [r for r in INTRA if r[0] in own]
    far = [r for r in intra if abs(ci_of[r[0]] - ci_of[r[2]]) >= 2]
    # ── bố cục ──
    ref_h = max((48 + ROW * (1 + sum(1 for (c, col), src in COPIED.items() if src == p[0] and c in own)) for p in refs), default=0)
    n_cross = sum(len(v) for v in refs.values())
    x0, MARGIN = 60, 150
    y0 = (100 + ref_h + 60 + 9 * n_cross) if refs else 90       # mỗi đường tham chiếu một làn ngang phía trên khối
    t_top = y0 + 110 + 9 * len(far)                               # mỗi đường nội bộ đi xa một làn ngang trong khối
    COLGAP, VGAP = GAPS.get(svc, (150, 70))
    natural = len(cols) * (TW + COLGAP) - COLGAP + 2 * MARGIN
    min_w = 1240
    pos, rows, tids, colx = {}, {}, {}, []
    x = x0 + MARGIN + max(0, (min_w - natural) / 2)
    heights = []
    for col in cols:
        y = t_top
        colx.append(x)
        for c in col:
            tid, rid, h = table(d, c, x, y, head, stroke)
            tids[c], rows[c], pos[c] = tid, rid, (x, y, TW, h)
            y += h + VGAP
        heights.append(y - VGAP)
        x += TW + COLGAP
    right = max(x - COLGAP + MARGIN, x0 + min_w)
    bottom = max(heights) + 150                 # chỗ cho đường vòng dưới các cột bảng
    # khối service (chèn lên đầu để nằm dưới các bảng)
    box = (f'<mxCell id="svcbox" value="" style="rounded=1;arcSize=1.2;fillColor={fill};strokeColor={stroke};strokeWidth=3;html=1;" '
           f'vertex="1" parent="1"><mxGeometry x="{x0}" y="{y0}" width="{right - x0}" height="{bottom - y0}" as="geometry"/></mxCell>')
    title = (f'<mxCell id="svctitle" value="{html.escape(f"<b>{svc}</b>  ·  {db}", quote=True)}" '
             f'style="text;html=1;align=left;verticalAlign=middle;fontSize=20;fontColor={stroke};{FONT}" vertex="1" parent="1">'
             f'<mxGeometry x="{x0 + 20}" y="{y0 + 10}" width="{right - x0 - 40}" height="36" as="geometry"/></mxCell>')
    d.cells[0:0] = [box, title]
    d.b[0], d.b[1], d.b[2], d.b[3] = min(d.b[0], x0), min(d.b[1], y0), max(d.b[2], right), max(d.b[3], bottom)
    d.v(f"<b>Logical ERD – {svc}</b>", x0, 14, right - x0, 34,
        "text;html=1;align=left;verticalAlign=middle;fontSize=24;" + FONT)

    def row_y(c, col):
        idx = [f_["name"] for f_ in ordered_fields(c)].index(col)
        return pos[c][1] + HEAD + ROW * idx + ROW / 2

    # ── thực thể tham chiếu: dải trên, đặt gần các bảng dùng nó ──
    placed, refid, refbox = [], {}, {}
    rw = TW - 40
    if refs:
        want = sorted((sum(pos[c][0] + TW / 2 for c, _ in users) / len(users), p) for p, users in refs.items())
        xcur = x0 + 30
        for cx, p in want:
            xx = max(xcur, cx - rw / 2)
            placed.append((xx, p)); xcur = xx + rw + 40
        if placed[-1][0] + rw > right - 20:                     # tràn phải: dời sang trái vừa đủ, giữ gần bảng dùng nó
            xmax = right - 20 - rw
            for i in range(len(placed) - 1, -1, -1):
                xx, p = placed[i]
                xx = min(xx, xmax)
                placed[i] = (xx, p)
                xmax = xx - rw - 40
        for xx, p in placed:
            extra = sorted({col for (c, col), src in COPIED.items() if src == p[0] and c in own})
            refid[p], h = ref_table(d, p[0], xx, 100, extra)
            refbox[p] = (xx, 100, rw, h)

    # ── đi dây: không cắt, không trùng, không xuyên bảng ──
    boxes = {c: pos[c] for c in own}
    boxes.update({("ref", p): refbox[p] for p in refbox})
    boxes["_title"] = (x0 + 16, y0 + 8, 12 * len(f"{svc}  ·  {db}") + 10, 40)
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
            mult = next(r[3] for r in REL if r[0] == c and r[1] == col)
            yf = row_y(c, col)
            rcx = refbox[p][0] + refbox[p][2] / 2       # ra ở cạnh bảng quay về phía bảng tham chiếu
            rl, rr = refbox[p][0], refbox[p][0] + refbox[p][2]
            face = "L" if rr < pos[c][0] else ("R" if rl > pos[c][0] + pos[c][2] else "LR")
            top_row = cols[ci_of[c]][0] == c                # bảng đầu cột: có thể đi thẳng lên dải tham chiếu
            edges.append({"key": ("x", c, col), "a": c, "b": ("ref", p), "cross": True, "c": c, "col": col, "mult": mult,
                          "tries": [(face, "LRB", yf, None)] + ([("T", "LRB", None, None)] if top_row else []) + [
                                    ("LR", "LRB", yf, None), ("LRTB", "LRTB", None, None)]})
    if edges:
        big = svc in ("locker-service", "order-service")
        done = None
        for sp in ((1,) if big else (2, 1)):          # ưu tiên khoảng cách rộng giữa các đường, không được thì hẹp lại
            try:
                done = route_all(boxes, edges, walls=[(x0, y0, right - x0, bottom - y0)], wall_doors=["T"], tag=svc,
                                 pin_internal=True, polish=(1 if big else 6), attempts=int(os.environ.get("ERD_ATTEMPTS", 60 if sp == 1 else 25)), spacing=sp)
                break
            except RuntimeError:
                if sp == 1:
                    raise
        for e in edges:
            if e["key"] not in done:
                print("  THIẾU:", e["key"])
                continue
            pts = done[e["key"]][0]
            s, t = crow(e["mult"] == M, NN.get(f"{e['c']}.{e['col']}", False))
            base = STRAIGHT_DASH if e["cross"] else STRAIGHT_SOLID
            dst = refid[e["b"][1]] if e["cross"] else tids[e["b"]]
            d.e(tids[e["a"]], dst, base + f"startArrow={s};endArrow={t};" + anchor("exit", boxes[e["a"]], pts[0])
                + anchor("entry", boxes[e["b"]], pts[-1]), points=pts[1:-1])
    return d.save()


def re_strip(s):
    import re
    return re.sub(r"<[^>]+>|&nbsp;", " ", s)


# ───────────────────────── sơ đồ tổng quan ─────────────────────────
# user-service ở giữa (gần như mọi service tham chiếu user_profiles.id), các service khác xếp quanh;
# đường thẳng giữa hai thực thể, bố cục đã chọn để không đường nào đi xuyên qua hộp thực thể.
# khối service: x, y, w, h ; thực thể chính bên trong: (thực thể, dx, dy)
OV = {
    "store-service": ((80, 150, 440, 240), [("StoreLocation", 50, 80)]),
    "auth-service": ((1080, 150, 440, 240), [("AuthAccount", 50, 80)]),
    "notification-service": ((1760, 150, 440, 240), [("NotificationMessage", 50, 80)]),
    "assistant-service": ((2340, 150, 440, 440), [("AssistantConversation", 50, 80), ("KbDocument", 50, 260)]),
    "locker-service": ((80, 520, 800, 520), [("LockerUnit", 40, 80), ("LockerReport", 420, 80), ("DroneUnit", 40, 320), ("LockerBox", 420, 320)]),
    "user-service": ((1040, 560, 520, 360), [("UserProfile", 90, 100)]),
    "loyalty-service": ((1760, 640, 440, 660), [("LoyaltyAccount", 50, 90), ("PointTransaction", 50, 460)]),
    "iot-service": ((80, 1180, 800, 300), [("GatewayDevice", 40, 80), ("BoxAccessLog", 420, 80)]),
    "order-service": ((1080, 1060, 440, 640), [("LockerOrder", 50, 80), ("DroneMission", 50, 300), ("Promotion", 50, 490)]),
    "payment-service": ((2340, 1380, 440, 280), [("PaymentRecord", 50, 80)]),
}
CORE_W = 340
# đường liên-service chọn lọc: (con, cột, cha, nhãn); đủ 33 tham chiếu: xem 01–10
OV_CROSS = [("AuthAccount", "user_id", "UserProfile", "auth_accounts.user_id"),
            ("NotificationMessage", "user_id", "UserProfile", "notifications.user_id"),
            ("AssistantConversation", "user_id", "UserProfile", "assistant_conversations.user_id"),
            ("LoyaltyAccount", "user_id", "UserProfile", "loyalty_accounts.user_id"),
            ("LockerOrder", "user_id", "UserProfile", "orders.user_id"),
            ("LockerReport", "user_id", "UserProfile", "locker_reports.user_id"),
            ("LockerUnit", "store_id", "StoreLocation", "lockers.store_id"),
            ("PointTransaction", "order_id", "LockerOrder", "point_transactions.order_id"),
            ("PaymentRecord", "order_id", "LockerOrder", "payments.order_id"),
            ("BoxAccessLog", "order_id", "LockerOrder", "box_access_logs.order_id"),
            ("LockerOrder", "send_box_id", "LockerBox", "orders.send_box_id"),
            ("DroneMission", "drone_unit_id", "DroneUnit", "drone_missions.drone_unit_id"),
            ("GatewayDevice", "locker_id", "LockerUnit", "gateway_devices.locker_id"),
            ("BoxAccessLog", "box_id", "LockerBox", "box_access_logs.box_id")]
# đường cần bẻ góc vòng ra lề trái (đi thẳng sẽ xuyên qua DroneUnit)
OV_POINTS = {("GatewayDevice", "locker_id"): ([(50, 1320), (50, 650)], "exitX=0;exitY=0.5;", "entryX=0;entryY=0.5;")}
KEY_ATTR = {"UserProfile": ["email", "phone_number", "first_name", "last_name", "status", "roles"], "AuthAccount": ["email", "password_hash"], "StoreLocation": ["name", "latitude"],
            "LockerUnit": ["code", "status"], "LockerBox": ["box_number", "status"], "LockerReport": ["category", "status"],
            "DroneUnit": ["code", "status"], "GatewayDevice": ["mac_address", "setup_status"], "BoxAccessLog": ["credential_type", "result"],
            "LockerOrder": ["order_code", "status"], "DroneMission": ["status", "payload_weight_grams"], "Promotion": ["code", "discount_value"],
            "PaymentRecord": ["amount", "reference_id"], "LoyaltyAccount": ["points", "tier"],
            "PointTransaction": ["points", "type"], "NotificationMessage": ["title", "is_read"], "AssistantConversation": ["title"],
            "KbDocument": ["title", "allowed_roles"]}
CORE = {c for _, items in OV.values() for c, _, _ in items}
STRAIGHT_SOLID = SOLID.replace("edgeStyle=orthogonalEdgeStyle;rounded=1;", "edgeStyle=none;rounded=0;")
STRAIGHT_DASH = DASH.replace("edgeStyle=orthogonalEdgeStyle;rounded=1;", "edgeStyle=none;rounded=0;")


def core_box(d, cls, x, y, head, stroke):
    """thực thể chính: tên + PK + cột tham chiếu có vẽ trên sơ đồ + 1–2 thuộc tính tiêu biểu."""
    f = {x_["name"]: x_ for x_ in ENT[cls]["fields"]}
    pk = next(n for n, v in f.items() if v["pk"])
    cross = [col for c, col, _, _ in OV_CROSS if c == cls]
    if cls == "LockerOrder":
        cross = ["user_id", "locker_id", "send_box_id", "store_id"]
    if cls == "LockerUnit":
        cross = ["store_id", "assigned_technician_id"]
    intra = [r[1] for r in INTRA if r[0] == cls and r[2] in CORE]
    lines = [("PK", pk)] + [("(FK)", k) for k in dict.fromkeys(cross)] + [("FK", k) for k in dict.fromkeys(intra) if k not in cross]
    lines += [("", a) for a in KEY_ATTR.get(cls, []) if a in f]
    h = HEAD + ROW * len(lines)
    label = cls + '  <span style="font-weight:normal;color:#555555">(' + TBL[cls] + ')</span>'
    tid = d.v(label, x, y, CORE_W, h,
              f"shape=table;startSize={HEAD};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
              f"align=center;resizeLast=1;html=1;fontSize=14;fillColor={head};swimlaneFillColor=#FFFFFF;strokeColor={stroke};{FONT}")
    base = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" + FONT
    for i, (k, n) in enumerate(lines):
        r = d.v("", 0, HEAD + i * ROW, CORE_W, ROW, "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;"
                "collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;", parent=tid, grow=False)
        kc = "#1565C0" if k == "(FK)" else "#000000"
        d.v(k, 0, 0, 46, ROW, base + f"align=center;fontStyle=1;fontColor={kc};", parent=r, grow=False)
        fs = 4 if k == "PK" else (2 if k else 0)
        d.v(n, 46, 0, CORE_W - 46, ROW, base + f"align=left;spacingLeft=6;fontStyle={fs};", parent=r, grow=False)
    return tid, h


def label_pos(pts, walls=(), boxes=(), others=(), text=""):
    """Vị trí nhãn (-1..1 dọc đường): nhãn không đè bảng, không đè đường khác, xa viền khối và góc bẻ nhất."""
    segs = [abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(segs) or 1
    lw, lh = 6.3 * len(text) + 8, 16

    def hits(rx, ry, a, b):      # đoạn thẳng đứng/ngang a-b có đi qua hình chữ nhật nhãn không
        (x1, y1), (x2, y2) = a, b
        return (min(x1, x2) <= rx + lw and max(x1, x2) >= rx and min(y1, y2) <= ry + lh and max(y1, y2) >= ry)
    best, bpos = None, 0.0
    for k, L in enumerate(segs):
        (x1, y1), (x2, y2) = pts[k], pts[k + 1]
        for t in [i / 40 for i in range(1, 40)]:
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            rx, ry = x - lw / 2, y - lh / 2
            d = min(t * L, (1 - t) * L)
            if y1 == y2:
                d = min(d, (min(t * L, (1 - t) * L) - lw / 2) + 40)   # nhãn nằm gọn trong đoạn ngang
            for (wx, wy, ww, wh) in walls:
                if wy - lh <= y <= wy + wh + lh:
                    d = min(d, abs(x - wx) - lw / 2, abs(x - wx - ww) - lw / 2)
                if wx - lw <= x <= wx + ww + lw:
                    d = min(d, abs(y - wy) - lh / 2, abs(y - wy - wh) - lh / 2)
            pen = 0
            for (bx, by, bw, bh) in boxes:
                if rx < bx + bw and rx + lw > bx and ry < by + bh and ry + lh > by:
                    pen += 1000
            for o in others:
                pen += 500 * sum(hits(rx, ry, o[q], o[q + 1]) for q in range(len(o) - 1))
            sc = d - pen
            if best is None or sc > best:
                best, bpos = sc, (sum(segs[:k]) + t * L) / total
    return 2 * bpos - 1


def overview():
    d = D("00-cross-service-overview")
    d.v("<b>Logical ERD tổng quan – liên kết giữa các database</b>", 80, 40, 2700, 40,
        "text;html=1;align=left;verticalAlign=middle;fontSize=28;" + FONT)
    tids, boxes, walls = {}, {}, []
    for svc, ((x, y, w, h), items) in OV.items():
        fname, db, fill, stroke, head, desc = SVC[svc]
        d.v("", x, y, w, h, f"rounded=1;arcSize=3;fillColor={fill};strokeColor={stroke};strokeWidth=3;html=1;")
        d.v(f"<b>{svc}</b> · {db}", x + 16, y + 12, w - 32, 30,
            f"text;html=1;align=left;verticalAlign=middle;fontSize=17;fontColor={stroke};" + FONT)
        boxes[("_title", svc)] = (x + 14, y + 10, 10 * len(f"{svc} · {db}") + 10, 34)   # chỉ phần chữ
        walls.append((x, y, w, h))
        for c, dx, dy in items:
            tids[c], hh = core_box(d, c, x + dx, y + dy, head, stroke)
            boxes[c] = (x + dx, y + dy, CORE_W, hh)
    # đi dây cả nét liền (trong cùng database) và nét đứt (liên-service): không cắt, không trùng, không xuyên hộp
    edges = []
    for c, col, p, mult in INTRA:
        if c in CORE and p in CORE:
            edges.append({"key": ("i", c, col), "a": c, "b": p, "cross": False, "col": col, "mult": mult, "label": "",
                          "tries": [("LRTB", "LRTB", None, None)]})
    for c, col, p, label in OV_CROSS:
        mult = next(r[3] for r in REL if r[0] == c and r[1] == col)
        edges.append({"key": ("x", c, col), "a": c, "b": p, "cross": True, "col": col, "mult": mult, "label": label,
                      "tries": [("LRTB", "LRTB", None, None)]})
    done = route_all(boxes, edges, walls=walls, tag="tổng quan", spacing=2, pin_internal=True, polish=12, attempts=80)
    for e in edges:
        pts = done[e["key"]][0]
        s, t = crow(e["mult"] == M, NN.get(f"{e['a']}.{e['col']}", False))
        base = STRAIGHT_DASH if e["cross"] else STRAIGHT_SOLID
        d.e(tids[e["a"]], tids[e["b"]], base + f"startArrow={s};endArrow={t};" + anchor("exit", boxes[e["a"]], pts[0])
            + anchor("entry", boxes[e["b"]], pts[-1]), label=e["label"], points=pts[1:-1], lpos=label_pos(pts, walls, [b for n, b in boxes.items() if n in CORE], [done[k][0] for k in done if k != e["key"]], e["label"]))
    return d.save()


if __name__ == "__main__":
    only = sys.argv[1:]
    failed = []
    if not only or "00" in only:
        try:
            print(overview())
        except RuntimeError as ex:
            failed.append(str(ex))
    for svc in SVC:
        if not only or SVC[svc][0][:2] in only:
            try:
                print(per_service(svc))
            except RuntimeError as ex:
                failed.append(str(ex))
    for f in failed:
        print("LỖI:", f)
    sys.exit(1 if failed else 0)
