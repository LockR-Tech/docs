"""Vẽ các sơ đồ nối dây tủ CAB-TU01 (SVG) cho 03-hardware/tu01-so-do-tong-quan.md.

    python scripts/ve-so-do-tu01.py

Ghi vào 03-hardware/img/tu01-so-do/. Mọi số chân lấy từ các bảng ở đầu file — sửa sơ đồ thì sửa bảng
rồi chạy lại, không sửa tay file SVG. Nguồn: "Sơ đồ tổng quan Tủ Locker CAB-TU01" (03/11/2026).
"""
import os
from html import escape

OUT = os.path.join(os.path.dirname(__file__), "..", "03-hardware", "img", "tu01-so-do")

# ─── số liệu (một nguồn duy nhất cho mọi hình) ───
# Khoá N: (IN relay = chân Pi, GPIO), (dây phản hồi = chân Pi, GPIO)
LOCKS = [
    (1, 29, 5, 7, 4), (2, 31, 6, 12, 18), (3, 33, 13, 18, 24), (4, 35, 19, 22, 25),
    (5, 37, 26, 32, 12), (6, 36, 16, 40, 21), (7, 38, 20, 24, 8),
]
# Transistor: tên, tín hiệu, chân Pi, GPIO, driver, cực E về chân GND
TRANSISTORS = [
    ("T1", "PUL−", 11, 17, 1, 9), ("T2", "DIR−", 13, 27, 1, 9),
    ("T3", "PUL−", 15, 22, 2, 14), ("T4", "DIR−", 16, 23, 2, 14),
]
MOTOR_WIRES = {  # trục: (A+, A−, B+, B−) — màu dây motor
    1: [("A+", "Đỏ", "#d32f2f"), ("A−", "Đen", "#212121"), ("B+", "Xanh dương", "#1565c0"), ("B−", "Vàng", "#f9a825")],
    2: [("A+", "Xanh lá", "#2e7d32"), ("A−", "Đen", "#212121"), ("B+", "Xanh dương", "#1565c0"), ("B−", "Đỏ", "#d32f2f")],
}
DIP = [("S1", True), ("S2", True), ("S3", False), ("S4", True), ("S5", False), ("S6", True)]  # True = ON (gạt xuống)

# Header 40 chân: chân vật lý → (tên, vai trò, loại màu)
PIN_NAME = {
    1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14", 9: "GND", 10: "GPIO15",
    11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23", 17: "3V3", 18: "GPIO24",
    19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25", 23: "GPIO11", 24: "GPIO8", 25: "GND", 26: "GPIO7",
    27: "ID_SD", 28: "ID_SC", 29: "GPIO5", 30: "GND", 31: "GPIO6", 32: "GPIO12", 33: "GPIO13", 34: "GND",
    35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20", 39: "GND", 40: "GPIO21",
}
PIN_USE = {
    2: ("PUL+ và DIR+ của 2 driver", "v5"), 4: ("DC+ module relay", "v5"), 6: ("GND điểm chia 5V", "gnd"),
    9: ("Cột − trái breadboard (E của T1, T2)", "gnd"), 14: ("Cột − phải breadboard (E của T3, T4)", "gnd"),
    30: ("GND chung dây phản hồi khoá", "gnd"), 39: ("DC− module relay", "gnd"),
    3: ("Chưa nối · phần mềm giữ làm công tắc gốc trục 1", "spare"),
    5: ("Chưa nối · phần mềm giữ làm công tắc cuối trục 1", "spare"),
    21: ("Chưa nối · phần mềm giữ làm công tắc gốc trục 2", "spare"),
    23: ("Chưa nối · phần mềm giữ làm công tắc cuối trục 2", "spare"),
}
for name, sig, pin, gpio, drv, _ in TRANSISTORS:
    PIN_USE[pin] = (f"{sig[:3]} trục {drv} ({name})", "motor")
for n, rpin, rg, fpin, fg in LOCKS:
    PIN_USE[rpin] = (f"IN{n} relay – khoá {n}", "relay")
    PIN_USE[fpin] = (f"Phản hồi khoá {n}", "feedback")

C = {
    "v12": "#d32f2f", "gnd": "#212121", "v5": "#ef6c00", "v33": "#c62828", "motor": "#1565c0", "relay": "#6a1b9a",
    "feedback": "#2e7d32", "spare": "#9e9e9e", "none": "#bdbdbd", "text": "#1f2937", "muted": "#6b7280",
    "panel": "#f8fafc", "border": "#cbd5e1",
}
FONT = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"


class Svg:
    def __init__(self, w, h, title, subtitle=""):
        self.w, self.h = w, h
        self.p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
                  f'font-family="{FONT}">',
                  '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                  'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>',
                  f'<rect width="{w}" height="{h}" fill="#ffffff"/>']
        self.text(24, 38, title, 24, weight="700")
        if subtitle:
            self.text(24, 62, subtitle, 14, fill=C["muted"])

    def add(self, s):
        self.p.append(s)

    def rect(self, x, y, w, h, fill="#fff", stroke=C["border"], rx=8, sw=1.5, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{o} stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=13, anchor="start", weight="400", fill=None, italic=False, rotate=None):
        st = ' font-style="italic"' if italic else ""
        rot = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
                 f'fill="{fill or C["text"]}"{st}{rot}>{escape(str(s))}</text>')

    def lines(self, x, y, rows, size=13, gap=None, **kw):
        gap = gap or size + 5
        for i, r in enumerate(rows):
            self.text(x, y + i * gap, r, size, **kw)

    def line(self, x1, y1, x2, y2, color, width=2, dash=None, arrow=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        a = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" '
                 f'stroke-linecap="round"{d}{a}/>')

    def wire(self, pts, color, width=2.5, dash=None, arrow=False, outline=False):
        d = " ".join(f"{x},{y}" for x, y in pts)
        if outline:  # dây sáng màu (vàng) cần viền để đọc được trên nền trắng
            self.add(f'<polyline points="{d}" fill="none" stroke="#555" stroke-width="{width + 2}" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
        da = f' stroke-dasharray="{dash}"' if dash else ""
        a = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{da}{a}/>')

    def dot(self, x, y, color, r=4):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def circle(self, x, y, r, fill="#fff", stroke=C["text"], sw=1.5):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def path(self, d, stroke=C["text"], width=1.8, fill="none"):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" '
                 f'stroke-linecap="round"/>')

    def label(self, x, y, s, color, size=12, anchor="middle", pad=5):
        """Nhãn chữ trắng trên nền màu (đặt trên dây)."""
        w = len(s) * size * 0.58 + pad * 2
        x0 = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
        self.rect(x0, y - size, w, size + 8, fill=color, stroke=color, rx=4, sw=1)
        self.text(x0 + w / 2, y + 1, s, size, anchor="middle", weight="600", fill="#fff")

    def legend(self, x, y, items, title="Chú thích"):
        self.rect(x, y, 260, 30 + 24 * len(items), fill=C["panel"])
        self.text(x + 14, y + 22, title, 13, weight="700")
        for i, (color, name, width) in enumerate(items):
            yy = y + 44 + 24 * i
            self.line(x + 14, yy - 4, x + 58, yy - 4, color, width)
            self.text(x + 68, yy, name, 12)

    def save(self, name):
        self.p.append("</svg>")
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(self.p) + "\n")
        print("ghi", name)


# ───────────────────────── 0. mặt trước tủ ─────────────────────────
def cabinet_front():
    s = Svg(1420, 840, "Mặt trước tủ CAB-TU01 — số ô, relay và trục nắp",
            "Ô N trên admin = relay IN N = khoá N (slot = N − 1 trong code). Lưới: hàng 1–3 từ trên xuống, cột trái–giữa–phải.")
    x0, y0, cw, rh = 120, 200, 260, 170
    s.rect(x0 - 30, y0 - 30, cw * 3 + 60, rh * 3 + 60, fill="#eceff1", stroke="#78909c", rx=14, sw=3)
    cells = {  # (hàng, cột) → (ô, ghi chú)
        (1, 0): (None, "Không có khoá"), (1, 1): (2, "DRONE · dưới trục 2"), (1, 2): (3, "DRONE · dưới trục 1"),
        (2, 1): (4, ""), (2, 2): (7, ""), (3, 1): (6, ""), (3, 2): (5, ""),
    }
    for (r, c), (box, note) in cells.items():
        x, y = x0 + c * cw, y0 + (r - 1) * rh
        fill = "#fff8e1" if note.startswith("DRONE") else ("#f5f5f5" if box is None else "#ffffff")
        s.rect(x + 8, y + 8, cw - 16, rh - 16, fill=fill, stroke="#607d8b", rx=10, sw=2)
        if box is None:
            s.text(x + cw / 2, y + rh / 2 + 5, note, 15, "middle", fill=C["muted"], italic=True)
            continue
        s.text(x + cw / 2, y + 62, f"Ô {box}", 30, "middle", "700")
        s.text(x + cw / 2, y + 92, f"relay IN{box} · khoá {box}", 14, "middle", fill=C["relay"])
        if note:
            s.text(x + cw / 2, y + 118, note, 13, "middle", "600", fill="#b26a00")
    # ô 1: cửa cao bên trái (hàng 2–3)
    x, y = x0, y0 + rh
    s.rect(x + 8, y + 8, cw - 16, rh * 2 - 16, fill="#e3f2fd", stroke="#607d8b", rx=10, sw=2)
    s.text(x + cw / 2, y + rh - 10, "Ô 1", 30, "middle", "700")
    s.text(x + cw / 2, y + rh + 20, "relay IN1 · khoá 1", 14, "middle", fill=C["relay"])
    s.text(x + cw / 2, y + rh + 46, "XL — cửa cao 2 hàng", 13, "middle", "600", fill="#1565c0")
    # trục nắp trên nóc
    for axis, col in ((2, 1), (1, 2)):
        xx = x0 + col * cw + cw / 2
        s.rect(xx - 90, y0 - 92, 180, 34, fill="#e8eaf6", stroke="#3949ab", rx=6)
        s.text(xx, y0 - 70, f"Trục {axis} (nắp trượt trên nóc)", 13, "middle", "600", fill="#283593")
        s.line(xx, y0 - 58, xx, y0 - 34, "#3949ab", 2, arrow=True)
    s.lines(x0 + cw * 3 + 50, y0 + 10, [
        "Ô 2, ô 3 là ô DRONE — drone thả hàng",
        "qua nắp trượt trên nóc:",
        "  • trục 1 nằm trên ô 3 (LID1_BOXES=3)",
        "  • trục 2 nằm trên ô 2 (LID2_BOXES=2)",
        "",
        "Ô trên cùng bên trái chỉ là tấm che,",
        "không có khoá.",
        "",
        "Vị trí ô đã được đối chiếu bằng cách",
        "mở từng relay (2026-10-04) và ghi vào",
        "bảng ô của tủ trên production.",
    ], 13)
    s.save("00-mat-truoc-tu.svg")


# ───────────────────────── 1. sơ đồ khối ─────────────────────────
def block_diagram():
    s = Svg(1680, 980, "Sơ đồ khối — phần công suất 12 V tách riêng phần tín hiệu của Pi",
            "Hai bên chỉ gặp nhau qua opto trong driver TB6600 và tiếp điểm relay. GND của Pi KHÔNG nối vào −V của nguồn 12 V.")
    # vùng
    s.rect(20, 76, 900, 884, fill="#fff5f5", stroke="#ef9a9a", rx=14, dash="8 6")
    s.text(40, 945, "PHẦN CÔNG SUẤT 12 V", 15, weight="700", fill=C["v12"])
    s.rect(950, 76, 710, 884, fill="#f3f8ff", stroke="#90caf9", rx=14, dash="8 6")
    s.text(970, 945, "PHẦN TÍN HIỆU (Raspberry Pi 5)", 15, weight="700", fill=C["motor"])
    # nguồn
    s.rect(50, 380, 220, 200, fill="#eceff1", stroke="#546e7a", rx=10, sw=2)
    s.text(160, 412, "Nguồn tổ ong", 16, "middle", "700")
    s.text(160, 434, "12 V 10 A", 16, "middle", "700")
    s.text(160, 458, "L · N · ⏚ ← 220 V", 12, "middle", fill=C["muted"])
    for i, (lab, col) in enumerate((("+V", C["v12"]), ("+V", C["v12"]), ("+V", C["v12"]),
                                    ("−V", C["gnd"]), ("−V", C["gnd"]), ("−V", C["gnd"]))):
        yy = 480 + i * 16
        s.text(250, yy + 4, lab, 11, "end", "700", fill=col)
        s.dot(262, yy, col, 4)
    # driver + motor
    for k, (axis, yy) in enumerate(((1, 150), (2, 330))):
        s.rect(430, yy, 220, 130, fill="#263238", stroke="#000", rx=8, sw=2)
        s.text(540, yy + 32, f"Driver TB6600 #{axis}", 15, "middle", "700", fill="#fff")
        s.text(540, yy + 54, "200 bước/vòng · 1,0 A", 12, "middle", fill="#cfd8dc")
        s.text(540, yy + 80, "VCC/GND ← 12 V", 12, "middle", fill="#ffcdd2")
        s.text(540, yy + 100, "PUL+/DIR+ ← 5V", 12, "middle", fill="#ffcc80")
        s.text(540, yy + 118, "PUL−/DIR− ← C1815", 12, "middle", fill="#bbdefb")
        s.rect(720, yy + 15, 150, 100, fill="#90a4ae", stroke="#37474f", rx=6, sw=2)
        s.circle(795, yy + 65, 26, fill="#cfd8dc", stroke="#37474f", sw=2)
        s.text(795, yy + 132, f"Motor Nema 17 trục {axis}", 13, "middle", "600")
        for w, (_, _, col) in enumerate(MOTOR_WIRES[axis]):
            s.wire([(650, yy + 30 + w * 22), (720, yy + 30 + w * 22)], col, 3, outline=col == "#f9a825")
        # nguồn driver
        s.wire([(262, 480 + k * 16), (330 + k * 20, 480 + k * 16), (330 + k * 20, yy + 70), (430, yy + 70)], C["v12"], 4)
        s.wire([(262, 528 + k * 16), (370 + k * 20, 528 + k * 16), (370 + k * 20, yy + 95), (430, yy + 95)], C["gnd"], 4)
    # khoá + relay
    s.rect(380, 600, 520, 150, fill="#ede7f6", stroke="#5e35b1", rx=10, sw=2)
    s.text(640, 630, "Module relay 8 kênh 5 V (jumper H)", 15, "middle", "700", fill="#4527a0")
    s.text(640, 652, "Tiếp điểm K1–K7: COM = dây − khoá N, NO = −V", 12, "middle")
    for i in range(8):
        s.rect(400 + i * 62, 668, 50, 60, fill="#1e88e5" if i < 7 else "#90caf9", stroke="#0d47a1", rx=4)
        s.text(425 + i * 62, 703, f"K{i + 1}", 13, "middle", "700", fill="#fff")
    s.rect(380, 800, 520, 120, fill="#fff", stroke="#757575", rx=10, sw=2)
    s.text(640, 830, "7 khoá điện từ 12 V (có 2 dây phản hồi)", 15, "middle", "700")
    for i in range(7):
        s.rect(400 + i * 70, 850, 54, 50, fill="#eeeeee", stroke="#616161", rx=6)
        s.text(427 + i * 70, 881, str(i + 1), 15, "middle", "700")
    s.wire([(262, 512), (300, 512), (300, 875), (380, 875)], C["v12"], 4)
    s.text(276, 700, "+12 V → dây to +", 11, "end", fill=C["v12"])
    s.text(276, 714, "của 7 khoá", 11, "end", fill=C["v12"])
    s.wire([(262, 576), (290, 576), (290, 760), (640, 760), (640, 750)], C["gnd"], 4)
    s.text(470, 778, "−V → NO của K1–K7", 11, fill=C["gnd"])
    s.wire([(640, 800), (640, 750)], "#5d4037", 3)
    s.text(650, 790, "dây to − khoá N → COM N", 11, fill="#5d4037")
    # Pi
    s.rect(1180, 330, 300, 330, fill="#2e7d32", stroke="#1b5e20", rx=14, sw=3)
    s.text(1330, 365, "Raspberry Pi 5", 18, "middle", "700", fill="#fff")
    s.text(1330, 388, "lockr-tu01 · header 40 chân", 12, "middle", fill="#c8e6c9")
    s.rect(1450, 400, 22, 240, fill="#111", stroke="#000", rx=3)
    rows = [("chân 2 · 5V", C["v5"]), ("GPIO17/27/22/23", C["motor"]), ("chân 4 · 5V / 39 · GND", C["v5"]),
            ("7 GPIO → IN1–IN7", C["relay"]), ("7 GPIO ← phản hồi", C["feedback"]), ("chân 30 · GND chung", C["gnd"])]
    for i, (lab, col) in enumerate(rows):
        s.text(1440, 432 + i * 38, lab, 12, "end", "600", fill="#fff")
    # transistor board
    s.rect(1000, 150, 290, 120, fill="#fffde7", stroke="#f9a825", rx=10, sw=2)
    s.text(1145, 178, "Breadboard: 4 × C1815 + 4 × 1 kΩ", 14, "middle", "700")
    s.text(1145, 200, "T1 PUL / T2 DIR → driver 1", 12, "middle")
    s.text(1145, 220, "T3 PUL / T4 DIR → driver 2", 12, "middle")
    s.text(1145, 244, "GPIO cao ⇒ transistor dẫn ⇒ driver nhận xung", 12, "middle", fill=C["muted"])
    # 4 GPIO Pi → breadboard
    s.wire([(1180, 470), (1145, 470), (1145, 270)], C["motor"], 3, arrow=True)
    s.text(1152, 300, "GPIO17/27/22/23", 11, fill=C["motor"])
    # breadboard → cạnh trên driver (đi vòng trên đầu, không cắt motor)
    s.wire([(1000, 190), (945, 190), (945, 125), (560, 125), (560, 150)], C["motor"], 3, arrow=True)
    s.wire([(1000, 230), (960, 230), (960, 305), (560, 305), (560, 330)], C["motor"], 3, arrow=True)
    s.text(700, 119, "C của T1/T2 → PUL−/DIR− driver 1", 11, "middle", "600", fill=C["motor"])
    s.text(700, 299, "C của T3/T4 → PUL−/DIR− driver 2", 11, "middle", "600", fill=C["motor"])
    # 5V Pi → PUL+/DIR+ cả 2 driver (cạnh trên)
    s.wire([(1180, 432), (978, 432), (978, 100), (620, 100), (620, 150)], C["v5"], 3, arrow=True)
    s.wire([(978, 318), (620, 318), (620, 330)], C["v5"], 3, arrow=True)
    s.dot(978, 318, C["v5"])
    s.text(800, 94, "5V (chân 2) → PUL+ và DIR+ của cả 2 driver", 11, "middle", "600", fill=C["v5"])
    # relay
    s.wire([(1180, 508), (1010, 508), (1010, 640), (900, 640)], C["v5"], 3, arrow=True)
    s.text(1016, 530, "chân 4 (5V) + chân 39 (GND)", 11, fill=C["v5"])
    s.text(1016, 545, "nuôi module relay", 11, fill=C["v5"])
    s.wire([(1180, 546), (1040, 546), (1040, 700), (900, 700)], C["relay"], 3, arrow=True)
    s.text(1046, 690, "7 GPIO → IN1–IN7", 11, fill=C["relay"])
    s.wire([(900, 860), (1080, 860), (1080, 584), (1180, 584)], C["feedback"], 3, arrow=True)
    s.text(1086, 820, "dây phản hồi 1 → 7 GPIO", 11, fill=C["feedback"])
    s.wire([(900, 890), (1120, 890), (1120, 622), (1180, 622)], C["gnd"], 3, arrow=True)
    s.text(1126, 908, "dây phản hồi 2 → domino → chân 30 (GND)", 11, fill=C["gnd"])
    s.legend(1390, 700, [(C["v12"], "+12 V", 4), (C["gnd"], "−V / GND", 4), (C["v5"], "5 V từ Pi", 3),
                         (C["motor"], "Tín hiệu motor", 3), (C["relay"], "Kích relay", 3),
                         (C["feedback"], "Phản hồi khoá", 3)])
    s.save("01-so-do-khoi.svg")


# ───────────────────────── 2. header 40 chân ─────────────────────────
def pi_header():
    s = Svg(1500, 1240, "Header 40 chân của Raspberry Pi 5 — bản đồ chân tủ CAB-TU01",
            "Số trong ô tròn là SỐ CHÂN VẬT LÝ. Chân 1 (ô vuông, 3V3) ở đầu XA cổng USB/Ethernet. Đối chiếu bằng lệnh `pinout` trên Pi.")
    hx, hy, step = 700, 120, 46
    s.rect(hx - 40, hy - 30, 140, step * 20 + 30, fill="#1b5e20", stroke="#0b3d10", rx=10, sw=3)
    s.text(hx + 30, hy - 40, "phía khe thẻ nhớ / đầu xa cổng USB ↑", 12, "middle", fill=C["muted"])
    s.text(hx + 30, hy + step * 20 + 20, "phía cổng USB / Ethernet ↓", 12, "middle", fill=C["muted"])
    s.rect(hx - 20, hy - 18, 100, step * 20 - 6, fill="#111", stroke="#000", rx=6)
    for pin in range(1, 41):
        row, col = (pin - 1) // 2, (pin - 1) % 2
        cx, cy = hx + 8 + col * 44, hy + row * step
        use = PIN_USE.get(pin)
        name = PIN_NAME[pin]
        kind = use[1] if use else ("v5" if name == "5V" else "v33" if name == "3V3" else "gnd" if name == "GND" else "none")
        color = C[kind]
        if pin == 1:
            s.add(f'<rect x="{cx - 13}" y="{cy - 13}" width="26" height="26" fill="#d4af37" stroke="#8d6e00" stroke-width="2"/>')
        else:
            s.circle(cx, cy, 13, fill="#d4af37", stroke="#8d6e00", sw=2)
        s.text(cx, cy + 5, pin, 12, "middle", "700", fill="#111")
        # nhãn
        title = f"{name}" if not use else f"{name} · {use[0]}"
        if use is None:
            title = name if name in ("5V", "3V3", "GND") else f"{name} · không dùng"
        tw = 520
        if col == 0:
            x1 = cx - 30
            s.line(cx - 14, cy, x1, cy, color, 2)
            s.rect(x1 - tw, cy - 15, tw, 30, fill=color if use else "#f5f5f5", stroke=color, rx=6,
                   opacity=0.92 if use else None)
            s.text(x1 - 12, cy + 5, title, 13, "end", "600" if use else "400",
                   fill="#fff" if use and kind != "spare" else (C["text"] if not use else "#fff"))
        else:
            x1 = cx + 30
            s.line(cx + 14, cy, x1, cy, color, 2)
            s.rect(x1, cy - 15, tw, 30, fill=color if use else "#f5f5f5", stroke=color, rx=6,
                   opacity=0.92 if use else None)
            s.text(x1 + 12, cy + 5, title, 13, "start", "600" if use else "400",
                   fill="#fff" if use else C["text"])
    s.legend(160, 1085, [(C["v5"], "5 V", 8), (C["gnd"], "GND", 8), (C["motor"], "Tín hiệu motor (qua transistor)", 8)],
             "Màu theo việc")
    s.legend(440, 1085, [(C["relay"], "Kích relay IN1–IN7", 8), (C["feedback"], "Dây phản hồi khoá 1–7", 8),
                              (C["spare"], "Chưa nối, phần mềm đang giữ", 8)], "")
    s.save("02-header-40-chan.svg")


# ───────────────────────── 3. mạch kích motor ─────────────────────────
def npn(s, x, y, label):
    """Ký hiệu transistor NPN: chân B bên trái tại (x-40,y), C trên (x+22,y-50), E dưới (x+22,y+50)."""
    s.circle(x + 6, y, 34, fill="#fff", stroke=C["text"], sw=2)
    s.line(x - 40, y, x - 8, y, C["text"], 2.5)
    s.line(x - 8, y - 22, x - 8, y + 22, C["text"], 4)
    s.line(x - 8, y - 10, x + 22, y - 32, C["text"], 2.5)
    s.line(x + 22, y - 32, x + 22, y - 50, C["text"], 2.5)
    s.line(x - 8, y + 10, x + 22, y + 32, C["text"], 2.5)
    s.line(x + 22, y + 32, x + 22, y + 50, C["text"], 2.5)
    s.path(f"M{x + 22},{y + 32} l-13,-2 l6,-9 z", fill=C["text"], width=1)
    s.text(x + 50, y + 5, label, 15, weight="700")
    s.text(x - 26, y - 8, "B", 12, "middle", "700", fill=C["muted"])
    s.text(x + 34, y - 40, "C", 12, "middle", "700", fill=C["muted"])
    s.text(x + 34, y + 48, "E", 12, "middle", "700", fill=C["muted"])


def resistor(s, x1, y, x2, label):
    s.line(x1, y, x1 + 20, y, C["text"], 2.5)
    zig = " ".join(f"l8,{-10 if i % 2 == 0 else 20}" if i < 5 else "l8,-10" for i in range(6))
    s.path(f"M{x1 + 20},{y} {zig}", width=2.5)
    s.line(x1 + 68, y, x2, y, C["text"], 2.5)
    s.text((x1 + x2) / 2 + 8, y - 18, label, 13, "middle", "600")


def motor_driver_circuit():
    s = Svg(1500, 980, "Mạch kích tín hiệu motor — GPIO 3,3 V → 1 kΩ → C1815 → opto TB6600",
            "Mỗi tín hiệu PUL/DIR một transistor. GPIO lên CAO ⇒ transistor dẫn ⇒ kéo PUL−/DIR− xuống ⇒ opto sáng ⇒ driver nhận xung (active-high).")
    # Pi
    s.rect(40, 150, 230, 380, fill="#2e7d32", stroke="#1b5e20", rx=12, sw=3)
    s.text(155, 182, "Raspberry Pi 5", 16, "middle", "700", fill="#fff")
    for lab, yy, col in (("chân 2 · 5V", 230, C["v5"]), ("chân 11 · GPIO17", 330, C["motor"]),
                         ("chân 9 · GND", 470, C["gnd"])):
        s.rect(150, yy - 16, 120, 32, fill="#fff", stroke=col, rx=6, sw=2)
        s.text(210, yy + 5, lab, 12, "middle", "700", fill=col)
    # driver
    s.rect(1000, 150, 300, 380, fill="#263238", stroke="#000", rx=12, sw=3)
    s.text(1150, 182, "Driver TB6600 #1", 16, "middle", "700", fill="#fff")
    for lab, yy, col in (("PUL+", 230, C["v5"]), ("PUL−", 330, C["motor"])):
        s.rect(1000, yy - 16, 70, 32, fill="#fff", stroke=col, rx=6, sw=2)
        s.text(1035, yy + 5, lab, 13, "middle", "700", fill=col)
    # opto bên trong driver
    s.rect(1100, 210, 170, 160, fill="#37474f", stroke="#90a4ae", rx=8, dash="5 4")
    s.text(1185, 232, "opto bên trong", 12, "middle", fill="#cfd8dc")
    s.path("M1130,250 l0,20", stroke="#fff", width=2)
    s.path("M1120,270 l20,0 l-10,18 z", stroke="#fff", width=2, fill="#ffeb3b")
    s.path("M1120,288 l20,0", stroke="#fff", width=2)
    s.path("M1130,288 l0,22", stroke="#fff", width=2)
    s.path("M1150,272 l14,-10 M1150,284 l14,-10", stroke="#ffeb3b", width=2)
    s.text(1200, 300, "điện trở", 11, fill="#cfd8dc")
    s.text(1200, 314, "hạn dòng", 11, fill="#cfd8dc")
    s.wire([(1070, 230), (1130, 230), (1130, 250)], "#fff", 2)
    s.wire([(1070, 330), (1130, 330), (1130, 310)], "#fff", 2)
    s.text(1150, 400, "Dòng chạy: 5V → PUL+ → LED opto", 12, "middle", fill="#ffcc80")
    s.text(1150, 418, "→ PUL− → C → E → GND Pi", 12, "middle", fill="#ffcc80")
    s.text(1150, 450, "DIR dùng mạch y hệt:", 12, "middle", fill="#cfd8dc")
    s.text(1150, 468, "DIR+ = 5V, DIR− ← C của T2", 12, "middle", fill="#cfd8dc")
    # dây 5V
    s.wire([(270, 230), (1000, 230)], C["v5"], 3.5)
    s.text(560, 222, "5V (chân 2) → PUL+ và DIR+ của CẢ 2 driver", 13, "middle", "600", fill=C["v5"])
    # GPIO → điện trở → B
    resistor(s, 270, 330, 520, "R1 = 1 kΩ")
    npn(s, 560, 330, "T1  C1815 (NPN)")
    # C → PUL−
    s.wire([(582, 280), (582, 260), (900, 260), (900, 330), (1000, 330)], C["motor"], 3.5)
    s.text(760, 252, "C → ốc PUL− driver 1", 13, "middle", "600", fill=C["motor"])
    # E → GND
    s.wire([(582, 380), (582, 470), (270, 470)], C["gnd"], 3.5)
    s.text(430, 462, "E → cột − trái breadboard → chân 9 (GND)", 13, "middle", "600", fill=C["gnd"])
    # điện áp đo
    s.rect(620, 380, 330, 110, fill="#fffde7", stroke="#f9a825", rx=8)
    s.text(636, 404, "Đo DC so với GND Pi khi GPIO17 CAO:", 13, weight="700")
    s.text(636, 428, "• chân B ≈ 0,7 V", 13)
    s.text(636, 450, "• ốc PUL− ≈ 0,1–0,2 V (transistor dẫn)", 13)
    s.text(636, 472, "Khi GPIO17 THẤP: PUL− ≈ 5 V (opto tắt)", 13, fill=C["muted"])
    # C1815 chân
    bx, by = 120, 640
    s.text(bx, by - 40, "Chân C1815 (vỏ TO-92) — nhìn từ mặt phẳng có chữ", 16, weight="700")
    s.rect(bx + 40, by - 10, 120, 70, fill="#263238", stroke="#000", rx=8, sw=2)
    s.text(bx + 100, by + 22, "C1815", 15, "middle", "700", fill="#fff")
    s.text(bx + 100, by + 42, "mặt phẳng, có chữ", 10, "middle", fill="#b0bec5")
    for i, pinname in enumerate(("E", "C", "B")):
        xx = bx + 60 + i * 40
        s.line(xx, by + 60, xx, by + 150, "#9e9e9e", 5)
        s.text(xx, by + 175, pinname, 18, "middle", "700")
    s.lines(bx + 230, by + 30, [
        "Cầm transistor: MẶT PHẲNG CÓ CHỮ hướng về phía mình,",
        "chân chĩa xuống ⇒ từ trái sang phải là  E – C – B.",
        "",
        "• E (emitter)  → cột − cùng bên của breadboard → GND Pi",
        "• C (collector) → PUL− hoặc DIR− của driver",
        "• B (base)      → điện trở 1 kΩ → GPIO của Pi",
        "",
        "GPIO KHÔNG BAO GIỜ nối thẳng vào driver — luôn qua điện trở + transistor.",
        "Đề xuất khi hàn lên board: thêm 10 kΩ từ B xuống GND cho mỗi transistor",
        "(giữ transistor tắt chắc chắn lúc Pi khởi động).",
    ], 14, gap=22)
    # bảng 4 kênh
    tx, ty = 1000, 600
    s.text(tx, ty - 20, "4 kênh giống hệt nhau", 16, weight="700")
    head = ("Transistor", "GPIO (chân)", "C nối vào", "E về")
    widths = (110, 130, 150, 90)
    xx = tx
    for h, w in zip(head, widths):
        s.rect(xx, ty, w, 32, fill="#eceff1", stroke=C["border"], rx=0)
        s.text(xx + 8, ty + 21, h, 13, weight="700")
        xx += w
    for r, (name, sig, pin, gpio, drv, gnd) in enumerate(TRANSISTORS):
        xx, yy = tx, ty + 32 + r * 32
        for val, w in zip((name, f"GPIO{gpio} ({pin})", f"{sig} driver {drv}", f"chân {gnd}"), widths):
            s.rect(xx, yy, w, 32, fill="#fff", stroke=C["border"], rx=0)
            s.text(xx + 8, yy + 21, val, 13)
            xx += w
    s.save("03-mach-kich-motor.svg")


# ───────────────────────── 4. breadboard ─────────────────────────
def breadboard():
    rows = 30
    s = Svg(1500, 1620, "Breadboard mạch transistor — vị trí T1–T4 và điện trở 1 kΩ",
            "Bảng cầm dọc: hàng 1–30 từ trên xuống, cột a–e bên trái, f–j bên phải, rãnh giữa ngăn hai nửa. Mỗi nửa hàng (a–e hoặc f–j) nối thông.")
    ox, oy, p = 470, 130, 42  # gốc, bước lỗ
    cols = "abcde fghij"
    colx = {}
    for i, ch in enumerate(cols):
        if ch != " ":
            colx[ch] = ox + 70 + i * p
    left_minus, left_plus = ox + 6, ox + 34
    right_plus, right_minus = colx["j"] + 66, colx["j"] + 94
    s.rect(ox - 20, oy - 40, (right_minus - ox) + 50, rows * p + 50, fill="#fafafa", stroke="#bdbdbd", rx=14, sw=2)
    s.rect(colx["e"] + 12, oy - 25, p - 24, rows * p + 30, fill="#eeeeee", stroke="none", rx=4)
    for x, sign, col in ((left_minus, "−", "#1565c0"), (left_plus, "+", "#c62828"),
                         (right_plus, "+", "#c62828"), (right_minus, "−", "#1565c0")):
        s.line(x, oy - 18, x, oy + rows * p - 10, col, 2, dash="4 4")
        s.text(x, oy - 22, sign, 16, "middle", "700", fill=col)
    for ch, x in colx.items():
        s.text(x, oy - 18, ch, 14, "middle", "700", fill=C["muted"])
    for r in range(1, rows + 1):
        y = oy + (r - 1) * p + 10
        s.text(ox + 50, y + 4, r, 11, "end", fill=C["muted"])
        s.text(colx["j"] + 22, y + 4, r, 11, "start", fill=C["muted"])
        for x in colx.values():
            s.add(f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" rx="2" fill="#cfd8dc"/>')
        for x in (left_minus, left_plus, right_plus, right_minus):
            if r % 5:
                s.add(f'<rect x="{x - 4}" y="{y - 4}" width="8" height="8" rx="2" fill="#e0e0e0"/>')

    def hole(col, row):
        return colx[col], oy + (row - 1) * p + 10

    def transistor(name, col, rE, info):
        x, _ = hole(col, rE)
        y1, y3 = hole(col, rE)[1], hole(col, rE + 2)[1]
        s.rect(x - 16, y1 - 14, 32, y3 - y1 + 28, fill="#263238", stroke="#000", rx=10)
        for k, pn in enumerate("ECB"):
            s.dot(x, y1 + k * p, "#ffca28", 5)
            s.text(x + 22 if col in "abcde" else x - 22, y1 + k * p + 5, pn, 12,
                   "start" if col in "abcde" else "end", "700", fill="#795548")
        s.rect(x - 20, y1 - 46, 40, 24, fill="#fff", stroke="#000", rx=5, sw=1.5)
        s.text(x, y1 - 28, name, 15, "middle", "700", fill="#000")

    def res(c1, r1, c2, r2, label):
        x1, y1 = hole(c1, r1)
        x2, y2 = hole(c2, r2)
        s.line(x1, y1, x2, y2, "#8d6e63", 3)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        horiz = abs(x2 - x1) > abs(y2 - y1)
        w, h = (46, 16) if horiz else (16, 46)
        s.rect(mx - w / 2, my - h / 2, w, h, fill="#ffe0b2", stroke="#8d6e63", rx=6, sw=2)
        for k, color in enumerate(("#795548", "#000", "#c62828")):  # nâu-đen-đỏ = 1 kΩ
            if horiz:
                s.line(mx - 12 + k * 9, my - 8, mx - 12 + k * 9, my + 8, color, 3)
            else:
                s.line(mx - 8, my - 12 + k * 9, mx + 8, my - 12 + k * 9, color, 3)
        s.dot(x1, y1, "#8d6e63", 5)
        s.dot(x2, y2, "#8d6e63", 5)
        s.text(mx + (48 if not horiz else 0), my + (5 if not horiz else -16), label, 12,
               "start" if not horiz else "middle", "600", fill="#5d4037")

    # T1: hàng 10–12, nửa trái (cột không ghi trong bản gốc — vẽ ở cột c)
    transistor("T1", "c", 10, "")
    res("e", 12, "e", 21, "1 kΩ (12↔21)")
    # T2: c24 c25 c26, điện trở e26↔f26, dây j26
    transistor("T2", "c", 24, "")
    res("e", 26, "f", 26, "1 kΩ")
    # T3: h3 h4 h5, điện trở j5↔j9, dây f9
    transistor("T3", "h", 3, "")
    res("j", 5, "j", 9, "1 kΩ (j5↔j9)")
    # T4: h13 h14 h15, điện trở j15↔j19, dây f19
    transistor("T4", "h", 13, "")
    res("j", 15, "j", 19, "1 kΩ (j15↔j19)")

    def jumper(c, r, to_x, to_y, color, label, side):
        x, y = hole(c, r)
        s.wire([(x, y), (to_x, y), (to_x, to_y)], color, 3)
        s.dot(x, y, color, 5)

    # E → rail −
    for c, r, rail in (("a", 10, left_minus), ("a", 24, left_minus)):
        x, y = hole(c, r)
        s.wire([(x, y), (rail, y)], C["gnd"], 3)
        s.dot(x, y, C["gnd"], 5)
        s.dot(rail, y, C["gnd"], 5)
    for c, r, rail in (("j", 3, right_minus), ("j", 13, right_minus)):
        x, y = hole(c, r)
        s.wire([(x, y), (rail, y)], C["gnd"], 3)
        s.dot(x, y, C["gnd"], 5)
        s.dot(rail, y, C["gnd"], 5)
    # rail − → Pi
    yb = oy + rows * p + 40
    s.wire([(left_minus, oy + rows * p - 10), (left_minus, yb), (ox - 160, yb)], C["gnd"], 3, arrow=True)
    s.label(ox - 240, yb + 5, "cột − trái → chân 9 GND", C["gnd"])
    s.wire([(right_minus, oy + rows * p - 10), (right_minus, yb), (right_minus + 120, yb)], C["gnd"], 3, arrow=True)
    s.label(right_minus + 210, yb + 5, "cột − phải → chân 14 GND", C["gnd"])

    # dây GPIO vào đầu còn lại của điện trở
    def gpio_in(c, r, side, text_):
        x, y = hole(c, r)
        tx = ox - 190 if side == "L" else right_minus + 150
        s.wire([(tx, y), (x, y)], C["motor"], 3)
        s.dot(x, y, C["motor"], 5)
        s.label(tx - 70 if side == "L" else tx + 80, y + 5, text_, C["motor"])

    gpio_in("a", 21, "L", "chân 11 · GPIO17")
    gpio_in("j", 26, "R", "chân 13 · GPIO27")
    gpio_in("f", 9, "R", "chân 15 · GPIO22")
    gpio_in("f", 19, "R", "chân 16 · GPIO23")

    # C → driver
    def collector(c, r, side, text_):
        x, y = hole(c, r)
        tx = ox - 190 if side == "L" else right_minus + 150
        s.wire([(x, y), (tx, y)], "#00838f", 3, arrow=True)
        s.dot(x, y, "#00838f", 5)
        s.label(tx - 70 if side == "L" else tx + 80, y + 5, text_, "#00838f")

    collector("b", 11, "L", "→ PUL− driver 1")
    collector("b", 25, "L", "→ DIR− driver 1")
    collector("i", 4, "R", "→ PUL− driver 2")
    collector("i", 14, "R", "→ DIR− driver 2")

    s.lines(40, 1520, [
        "• T1: bản gốc chỉ ghi \"E hàng 10, C hàng 11, B hàng 12; điện trở hàng 12 ↔ hàng 21\" — không ghi cột. Hình vẽ ở cột c (nửa trái, cùng phía cột − trái/chân 9).",
        "  Trong một nửa hàng mọi lỗ nối thông, nên cắm cột nào trong a–e cũng như nhau. Dây E, C, GPIO của các transistor cũng vậy — chỉ cần đúng HÀNG và đúng NỬA.",
        "• Hai cột + không dùng: PUL+/DIR+ lấy 5V thẳng từ chân 2 của Pi tới ốc của driver. Bảng hiện cắm tạm — nên hàn lên board đục lỗ (T1 từng tiếp xúc kém ở đoạn điện trở – chân B).",
    ], 14, gap=24)
    s.legend(40, 120, [(C["motor"], "Từ GPIO của Pi", 3), ("#00838f", "Tới PUL−/DIR− driver", 3),
                       (C["gnd"], "E → cột − → GND Pi", 3), ("#8d6e63", "Điện trở 1 kΩ", 3)])
    s.save("04-breadboard-transistor.svg")


# ───────────────────────── 5. driver + motor ─────────────────────────
def driver_motor():
    s = Svg(1600, 1220, "Driver TB6600 và motor Nema 17 — đấu dây hai trục",
            "Driver lấy 12 V bằng cặp dây to đi thẳng về nguồn. Hai dây của CÙNG một cuộn motor phải chung A hoặc chung B (đo ≈ 11,6 Ω).")
    sig_terms = ["ENA−", "ENA+", "DIR−", "DIR+", "PUL−", "PUL+"]
    pwr_terms = ["B−", "B+", "A−", "A+", "GND", "VCC"]
    for k, axis in enumerate((1, 2)):
        y0 = 110 + k * 520
        s.rect(30, y0, 1540, 490, fill=C["panel"], stroke=C["border"], rx=14)
        s.text(50, y0 + 30, f"TRỤC {axis}", 18, weight="700", fill="#283593")
        # driver
        dx, dy = 520, y0 + 60
        s.rect(dx, dy, 360, 380, fill="#263238", stroke="#000", rx=10, sw=3)
        for f in range(9):
            s.rect(dx + 30 + f * 34, dy + 70, 20, 150, fill="#37474f", stroke="#455a64", rx=3)
        s.text(dx + 180, dy + 40, f"TB6600 #{axis}", 20, "middle", "700", fill="#fff")
        # khối cọc tín hiệu (trái), nguồn (phải)
        tpos = {}
        for i, t in enumerate(sig_terms):
            ty = dy + 250 + i * 20
            s.rect(dx - 70, ty - 9, 70, 18, fill="#2e7d32", stroke="#1b5e20", rx=2)
            s.text(dx - 35, ty + 5, t, 11, "middle", "700", fill="#fff")
            tpos[t] = (dx - 70, ty)
        for i, t in enumerate(pwr_terms):
            ty = dy + 250 + i * 20
            s.rect(dx + 360, ty - 9, 70, 18, fill="#2e7d32", stroke="#1b5e20", rx=2)
            s.text(dx + 395, ty + 5, t, 11, "middle", "700", fill="#fff")
            tpos[t] = (dx + 430, ty)
        # DIP
        s.rect(dx + 70, dy + 228, 220, 60, fill="#c62828", stroke="#7f0000", rx=4)
        for i, (name, on) in enumerate(DIP):
            sx = dx + 86 + i * 33
            s.rect(sx, dy + 236, 22, 44, fill="#fff", stroke="#7f0000", rx=2)
            s.rect(sx + 3, dy + 260 if on else dy + 240, 16, 16, fill="#212121", stroke="none", rx=2)
            s.text(sx + 11, dy + 300, name, 10, "middle", "700", fill="#fff")
        s.text(dx + 180, dy + 330, "DIP: gạt XUỐNG = ON", 12, "middle", "600", fill="#ffcdd2")
        s.text(dx + 180, dy + 350, "S1 ON · S2 ON · S3 OFF ⇒ 200 bước/vòng", 12, "middle", fill="#fff")
        s.text(dx + 180, dy + 368, "S4 ON · S5 OFF · S6 ON ⇒ 1,0 A", 12, "middle", fill="#fff")
        # tín hiệu
        trans = [t for t in TRANSISTORS if t[4] == axis]
        pul, dirt = trans[0], trans[1]
        for term, (tname, sig, pin, gpio, _, gnd), yoff in (("PUL−", pul, 0), ("DIR−", dirt, 1)):
            x, y = tpos[term]
            vx = 300 + yoff * 30
            s.wire([(x, y), (vx, y), (vx, y0 + 90 + yoff * 60), (vx - 10, y0 + 90 + yoff * 60)], "#00838f", 3)
            s.label(vx - 110, y0 + 96 + yoff * 60, f"C của {tname} (GPIO{gpio}, chân {pin})", "#00838f", 12)
        for term in ("PUL+", "DIR+"):
            x, y = tpos[term]
            s.wire([(x, y), (380, y), (380, y0 + 230)], C["v5"], 3)
        s.dot(380, tpos["DIR+"][1], C["v5"])
        s.label(260, y0 + 236, "5V · chân 2 của Pi", C["v5"], 12)
        for term in ("ENA−", "ENA+"):
            x, y = tpos[term]
            s.text(x - 10, y + 4, "để trống", 11, "end", fill=C["muted"], italic=True)
        # nguồn
        for term, col, lab in (("VCC", C["v12"], "+V nguồn 12 V"), ("GND", C["gnd"], "−V nguồn 12 V")):
            x, y = tpos[term]
            vx, ly = (990, y0 + 70) if term == "VCC" else (1015, y0 + 110)
            s.wire([(x, y), (vx, y), (vx, ly), (1050, ly)], col, 5)
            s.label(1110, ly + 6, lab, col, 12)
        # motor
        mx, my = 1270, y0 + 140
        s.rect(mx, my, 200, 200, fill="#90a4ae", stroke="#37474f", rx=14, sw=3)
        s.circle(mx + 100, my + 100, 60, fill="#cfd8dc", stroke="#37474f", sw=3)
        s.circle(mx + 100, my + 100, 12, fill="#eceff1", stroke="#37474f", sw=2)
        for cx, cy in ((22, 22), (178, 22), (22, 178), (178, 178)):
            s.circle(mx + cx, my + cy, 7, fill="#eceff1", stroke="#37474f")
        s.text(mx + 100, my + 230, f"Nema 17 · trục {axis}", 14, "middle", "700")
        s.text(mx + 100, my + 250, "cuộn ≈ 11,6 Ω", 12, "middle", fill=C["muted"])
        for i, (term, name, col) in enumerate(MOTOR_WIRES[axis]):
            x, y = tpos[term]
            yy = my + 40 + i * 40
            s.wire([(x, y), (1140 + i * 18, y), (1140 + i * 18, yy), (mx, yy)], col, 4, outline=col == "#f9a825")
            s.text(mx - 8, yy - 8, f"{term} · {name}", 12, "end", "700", fill="#000")
        s.text(1150, y0 + 460, "Cuộn A: A+ / A−   ·   Cuộn B: B+ / B−", 12, "middle", fill=C["muted"])
    s.save("05-driver-motor.svg")


# ───────────────────────── 6. khoá + relay ─────────────────────────
def locks_relay():
    s = Svg(1780, 1220, "Khoá điện từ 12 V, module relay 8 kênh và dây phản hồi",
            "Dây to + mọi khoá → +V 12 V; dây to − khoá N → COM relay N; NO mỗi relay → −V 12 V. Không cấp điện khoá quá ~10 giây, mở từng khoá một.")
    # module relay
    rx, ry, rw = 300, 150, 1300
    s.rect(rx, ry, rw, 260, fill="#1565c0", stroke="#0d47a1", rx=10, sw=3)
    s.text(rx + rw / 2, ry + 30, "Module relay 8 kênh 5 V — jumper chọn mức kích đặt ở H (GPIO cao ⇒ relay đóng)", 15,
           "middle", "700", fill="#fff")
    chw = rw / 8
    term_x = {}
    for i in range(8):
        cx = rx + chw * i + chw / 2
        s.rect(cx - 50, ry + 90, 100, 90, fill="#2196f3" if i < 7 else "#64b5f6", stroke="#0d47a1", rx=6)
        s.text(cx, ry + 130, f"K{i + 1}", 18, "middle", "700", fill="#fff")
        s.text(cx, ry + 152, "SRD-05VDC", 10, "middle", fill="#e3f2fd")
        for j, t in enumerate(("NO", "COM", "NC")):
            tx = cx - 40 + j * 40
            s.rect(tx - 15, ry + 200, 30, 44, fill="#0d47a1", stroke="#000", rx=3)
            s.circle(tx, ry + 222, 9, fill="#b0bec5", stroke="#37474f")
            s.text(tx, ry + 194, t, 11, "middle", "700", fill="#fff")
            term_x[(i + 1, t)] = tx
        if i == 7:
            s.text(cx, ry + 70, "K8 không dùng", 12, "middle", "600", fill="#bbdefb")
    # đầu vào module
    ix, iy = 40, ry + 20
    s.rect(ix, iy, 150, 300, fill="#e3f2fd", stroke="#0d47a1", rx=8, sw=2)
    s.text(ix + 75, iy + 24, "Đầu vào module", 13, "middle", "700")
    inputs = ["DC+", "DC−"] + [f"IN{n}" for n in range(1, 9)]
    in_y = {}
    for k, name in enumerate(inputs):
        yy = iy + 46 + k * 25
        s.circle(ix + 132, yy - 4, 7, fill="#b0bec5", stroke="#37474f")
        s.text(ix + 116, yy, name, 12, "end", "700")
        in_y[name] = yy - 4
    # dây từ Pi tới đầu vào
    pin_of = {"DC+": ("chân 4 · 5V", C["v5"]), "DC−": ("chân 39 · GND", C["gnd"])}
    for n, rpin, rg, _, _ in LOCKS:
        pin_of[f"IN{n}"] = (f"chân {rpin} · GPIO{rg}", C["relay"])
    for name, (lab, col) in pin_of.items():
        yy = in_y[name]
        s.wire([(ix, yy), (ix - 10, yy)], col, 3)
    s.text(ix + 75, iy + 300 + 22, "IN8 để trống", 12, "middle", fill=C["muted"], italic=True)
    # bảng chân Pi cho đầu vào
    s.rect(30, 640, 230, 290, fill="#fff", stroke=C["border"], rx=8)
    s.text(42, 664, "Đầu vào ← chân Pi", 13, weight="700")
    for k, name in enumerate(inputs[:9]):
        lab, col = pin_of[name]
        s.text(42, 690 + k * 26, f"{name}", 13, weight="700", fill=col)
        s.text(100, 690 + k * 26, lab, 13, fill=col)
    # thanh nguồn 12V
    bus_plus_y, bus_minus_y = 560, 600
    s.wire([(200, bus_plus_y), (1700, bus_plus_y)], C["v12"], 6)
    s.label(1650, bus_plus_y - 12, "+V 12 V (nguồn)", C["v12"], 13)
    s.wire([(200, bus_minus_y), (1700, bus_minus_y)], C["gnd"], 6)
    s.label(1650, bus_minus_y + 30, "−V 12 V (nguồn)", C["gnd"], 13)
    # domino phản hồi
    dom_y = 1100
    s.rect(300, dom_y - 20, 1360, 40, fill="#fff3e0", stroke="#ef6c00", rx=6, sw=2)
    s.text(980, dom_y + 6, "Domino gom dây phản hồi thứ 2 của 7 khoá → chân 30 (GND) của Pi", 13, "middle", "700",
           fill="#e65100")
    s.wire([(300, dom_y), (260, dom_y)], C["gnd"], 3, arrow=True)
    s.label(200, dom_y + 5, "chân 30 · GND", C["gnd"], 12)
    # khoá
    lw = 150
    for idx, (n, rpin, rg, fpin, fg) in enumerate(LOCKS):
        cx = rx + chw * idx + chw / 2
        ly = 700
        s.rect(cx - lw / 2, ly, lw, 200, fill="#eceff1", stroke="#455a64", rx=10, sw=2)
        s.rect(cx - 40, ly + 30, 80, 70, fill="#b0bec5", stroke="#455a64", rx=6)
        for t in range(6):
            s.line(cx - 32 + t * 13, ly + 36, cx - 32 + t * 13, ly + 94, "#78909c", 2)
        s.rect(cx + 40, ly + 55, 26, 20, fill="#78909c", stroke="#455a64", rx=3)
        s.text(cx, ly + 128, f"Khoá {n}", 16, "middle", "700")
        s.text(cx, ly + 148, f"ô {n}", 12, "middle", fill=C["muted"])
        # dây to +
        s.wire([(cx - 50, ly), (cx - 50, bus_plus_y)], C["v12"], 4)
        s.dot(cx - 50, bus_plus_y, C["v12"], 5)
        # dây to − → COM
        s.wire([(cx - 20, ly), (cx - 20, 470), (term_x[(n, "COM")], 470), (term_x[(n, "COM")], ry + 244)], "#5d4037", 4)
        # NO → −V
        s.wire([(term_x[(n, "NO")], ry + 244), (term_x[(n, "NO")], 500), (cx - 80, 500), (cx - 80, bus_minus_y)],
               C["gnd"], 3)
        s.dot(cx - 80, bus_minus_y, C["gnd"], 5)
        # phản hồi
        s.wire([(cx - 10, ly + 200), (cx - 10, 980)], C["feedback"], 2.5)
        s.label(cx - 10, 1000, f"chân {fpin} · GPIO{fg}", C["feedback"], 11)
        s.wire([(cx + 58, ly + 200), (cx + 58, dom_y - 20)], "#9e9e9e", 2.5)
    s.lines(1460, 730, ["Màu dây trong hình:",
                      "đỏ = dây to + khoá",
                      "nâu = dây to − khoá → COM",
                      "đen = NO → −V",
                      "xanh lá = phản hồi 1 → GPIO",
                      "xám = phản hồi 2 → domino",
                      "",
                      "Hai dây phản hồi không có cực.",
                      "Cửa đóng ⇒ GPIO đọc THẤP.",
                      "K8 / IN8 dự phòng."], 12, gap=19)
    s.save("06-khoa-relay.svg")


if __name__ == "__main__":
    cabinet_front()
    block_diagram()
    pi_header()
    motor_driver_circuit()
    breadboard()
    driver_motor()
    locks_relay()
