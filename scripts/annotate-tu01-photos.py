"""Vẽ nhãn lên ảnh tủ lockr-tu01: locker/*.jpg -> 03-hardware/img/tu01/*.jpg.

Chạy từ gốc repo docs:  python scripts/annotate-tu01-photos.py   (cần Pillow)
Toạ độ trong file là toạ độ trên ảnh gốc sau khi thu cạnh dài về 1500 px (ảnh toàn cảnh giữ nguyên cỡ).
Chụp lại ảnh thì chỉnh lại toạ độ ở từng khối bên dưới.
"""
import os, re
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'locker')
OUT = os.path.join(ROOT, '03-hardware', 'img', 'tu01')
os.makedirs(OUT, exist_ok=True)
BOLD = next(f for f in ['C:/Windows/Fonts/segoeuib.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                        '/System/Library/Fonts/Supplemental/Arial Bold.ttf'] if os.path.exists(f))
YEL, GRN, RED, BLU, GRY, INK, WHT = (255, 214, 10), (34, 197, 94), (255, 59, 48), (56, 189, 248), (148, 163, 184), (16, 22, 27), (255, 255, 255)
# 12 ảnh chi tiết chụp 2026-10-01, giữ tên file gốc; p01…p12 theo thứ tự tên.
DETAIL = sorted(f for f in os.listdir(RAW) if re.match(r'^\d{13}_', f))


def load(name):
    if name == 'first':
        return Image.open(os.path.join(RAW, '00-toan-canh-khoang-dien.jpg')).convert('RGB')
    im = ImageOps.exif_transpose(Image.open(os.path.join(RAW, DETAIL[int(name[1:]) - 1]))).convert('RGB')
    im.thumbnail((1500, 1500), Image.LANCZOS)
    return im


class Canvas:
    def __init__(self, name, box, scale):
        im = load(name).crop(box)
        self.x0, self.y0, self.s = box[0], box[1], scale
        self.im = im.resize((round(im.size[0] * scale), round(im.size[1] * scale)), Image.LANCZOS).convert('RGBA')
        self.layer = Image.new('RGBA', self.im.size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.layer)

    def p(self, x, y):
        return ((x - self.x0) * self.s, (y - self.y0) * self.s)

    def rect(self, x1, y1, x2, y2, color, width=6, radius=10, dash=False):
        a, b = self.p(x1, y1), self.p(x2, y2)
        self.d.rounded_rectangle([a, b], radius=radius, outline=color + (255,), width=width)

    def fillrect(self, x1, y1, x2, y2, color, alpha=70):
        self.d.rectangle([self.p(x1, y1), self.p(x2, y2)], fill=color + (alpha,))

    def circle(self, x, y, r, color, width=5, fill=None):
        cx, cy = self.p(x, y)
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color + (255,), width=width, fill=(fill + (255,)) if fill else None)

    def line(self, x1, y1, x2, y2, color, width=4):
        self.d.line([self.p(x1, y1), self.p(x2, y2)], fill=color + (255,), width=width)

    def pill(self, x, y, text, size=28, bg=INK, fg=WHT, anchor='mm', border=None):
        """Nhãn chữ trên nền bo góc. anchor: l/m/r + t/m/b tính theo (x, y) trong toạ độ ảnh gốc."""
        font = ImageFont.truetype(BOLD, size)
        cx, cy = self.p(x, y)
        l, t, r, b = self.d.textbbox((0, 0), text, font=font)
        w, h = r - l, b - t
        px, py = round(size * 0.42), round(size * 0.28)
        bw, bh = w + 2 * px, h + 2 * py
        left = cx if anchor[0] == 'l' else cx - bw if anchor[0] == 'r' else cx - bw / 2
        top = cy if anchor[1] == 't' else cy - bh if anchor[1] == 'b' else cy - bh / 2
        left = max(4, min(self.im.size[0] - bw - 4, left))
        top = max(4, min(self.im.size[1] - bh - 4, top))
        self.d.rounded_rectangle([left, top, left + bw, top + bh], radius=round(size * 0.35), fill=bg + (235,),
                                 outline=(border + (255,)) if border else None, width=3)
        self.d.text((left + px - l, top + py - t), text, font=font, fill=fg + (255,))

    def save(self, name):
        out = Image.alpha_composite(self.im, self.layer).convert('RGB')
        out.save(os.path.join(OUT, name), quality=86, optimize=True)
        print(name, out.size)


# 1. Toàn cảnh khoang điện (ảnh 30/09, 1506x2000)
c = Canvas('first', (0, 0, 1506, 2000), 0.75)
c.rect(335, 1488, 628, 1556, YEL); c.circle(245, 1512, 26, YEL); c.circle(707, 1515, 26, YEL)
c.rect(135, 975, 905, 1190, YEL); c.rect(350, 335, 550, 910, YEL); c.rect(8, 145, 303, 770, YEL)
c.rect(955, 375, 1485, 1130, YEL); c.rect(1090, 1295, 1500, 1855, YEL)
c.line(1378, 1370, 1447, 1790, GRN, 12)
for letter, x, y in [('A', 480, 1628), ('B', 130, 1622), ('C', 75, 1085), ('D', 630, 560), ('E', 155, 835), ('F', 1220, 1190), ('G', 1290, 1920)]:
    c.circle(x, y, 32, INK, 4, fill=YEL); c.pill(x, y, letter, 34, bg=YEL, fg=INK)
c.line(165, 1590, 228, 1532, YEL, 5)
c.save('01-tong-quan.jpg')

# 2. Header 40 chân của Pi (p11)
c = Canvas('p11', (100, 480, 960, 1080), 1.6)
c.rect(368, 970, 814, 1016, GRN, 6)
for x, y in [(797, 985), (797, 1002), (387, 985), (387, 1002)]:
    c.circle(x, y, 9, INK, 2, fill=YEL)
c.line(797, 985, 800, 948, YEL); c.pill(800, 948, 'Chân 1', 28, bg=YEL, fg=INK, anchor='mb')
c.line(797, 1002, 800, 1034, YEL); c.pill(800, 1034, 'Chân 2', 28, bg=YEL, fg=INK, anchor='mt')
c.line(387, 985, 400, 948, YEL); c.pill(400, 948, 'Chân 39', 28, bg=YEL, fg=INK, anchor='mb')
c.line(387, 1002, 400, 1034, YEL); c.pill(400, 1034, 'Chân 40', 28, bg=YEL, fg=INK, anchor='mt')
c.pill(595, 948, 'Hàng trong (phía quạt): chân lẻ', 26, bg=GRN, fg=INK, anchor='mb')
c.pill(595, 1034, 'Hàng ngoài (mép bo): chân chẵn', 26, bg=GRN, fg=INK, anchor='mt')
c.rect(320, 594, 378, 654, RED, 6); c.line(324, 598, 374, 650, RED, 5); c.line(374, 598, 324, 650, RED, 5)
c.pill(388, 610, 'J14 là PoE: KHÔNG cắm dây vào đây', 28, bg=RED, anchor='lm')
c.pill(190, 760, 'Cổng USB, mạng', 26, anchor='mm')
c.pill(770, 560, 'Nguồn USB-C', 26, anchor='mm')
c.pill(870, 800, 'Đầu xa\ncổng USB', 24, anchor='mm')
c.save('02-pi-header.jpg')

# 3. Module relay (p07)
c = Canvas('p07', (520, 120, 1220, 470), 2.0)
names = ['IN8', 'IN7', 'IN6', 'IN5', 'IN4', 'IN3', 'IN2', 'IN1', 'DC−', 'DC+']
xs = [757, 778, 800, 821, 842, 875, 897, 918, 940, 961]
for i, (n, x) in enumerate(zip(names, xs)):
    ty = 160 if i % 2 else 190
    col = RED if n == 'DC+' else GRY if n == 'DC−' else YEL
    c.line(x, 228 if i < 5 else 235, x, ty + 8, col, 3)
    c.pill(x, ty, n, 22, bg=col, fg=INK if col != RED else WHT, anchor='mm')
c.pill(860, 132, 'Cọc đầu vào, nối về Pi (đối chiếu chữ in trên bo)', 24, anchor='mm')
c.circle(662, 232, 46, GRN, 6); c.circle(1052, 255, 46, GRN, 6)
c.pill(600, 150, 'Jumper H/L: đặt H', 24, bg=GRN, fg=INK, anchor='mm'); c.line(625, 165, 650, 215, GRN, 4)
c.pill(1130, 180, 'Jumper H/L: đặt H', 24, bg=GRN, fg=INK, anchor='mm'); c.line(1100, 195, 1065, 238, GRN, 4)
for k, x in zip(range(8, 0, -1), [598, 678, 757, 836, 913, 992, 1070, 1145]):
    c.pill(x, 300, f'K{k}', 24, anchor='mm')
c.pill(870, 440, 'Đầu ra relay (dây xanh mảnh): nhà cung cấp đã nối, không tháo', 24, bg=BLU, fg=INK, anchor='mm')
c.save('03-relay.jpg')

# 4. Domino 1: dây tín hiệu khoá (p07)
c = Canvas('p07', (490, 440, 1430, 770), 1.48)
top = {12: 560, 11: 625, 10: 695, 9: 768, 8: 838, 7: 905, 6: 972, 5: 1038, 4: 1100, 3: 1168, 2: 1235, 1: 1322}
bot = {12: 548, 11: 615, 10: 690, 9: 762, 8: 838, 7: 908, 6: 975, 5: 1045, 4: 1115, 3: 1188, 2: 1260, 1: 1340}
for n, x in top.items():
    col = GRN if n % 2 else GRY
    c.circle(x, 536, 22, col, 5)
    c.pill(x, 492, str(n), 24, bg=col, fg=INK, anchor='mm')
c.pill(960, 456, 'Hàng TRỐNG phía relay: dây về Pi bắt vào đây.  Xanh lá (cọc lẻ) về GPIO · xám (cọc chẵn) về GND', 22, anchor='mm')
for o, (a, b) in zip(range(6, 0, -1), [(12, 11), (10, 9), (8, 7), (6, 5), (4, 3), (2, 1)]):
    xa, xb = bot[a], bot[b]
    c.line(xa - 14, 722, xb + 14, 722, YEL, 5); c.line(xa - 14, 722, xa - 14, 708, YEL, 5); c.line(xb + 14, 722, xb + 14, 708, YEL, 5)
    c.pill((xa + xb) / 2, 748, f'cặp ô {o}', 24, bg=YEL, fg=INK, anchor='mm')
c.save('04-domino-1.jpg')

# 5. Domino 2: nguồn 12 V, tín hiệu driver, cặp dây vàng (p05)
c = Canvas('p05', (250, 500, 1250, 985), 1.4)
topx = {12: 352, 11: 425, 10: 488, 9: 545, 8: 602, 7: 663, 6: 720, 5: 780, 4: 840, 3: 905, 2: 965, 1: 1040}
botx = {12: 348, 11: 405, 10: 462, 9: 520, 8: 578, 7: 640, 6: 702, 5: 768, 4: 838, 3: 905, 2: 975, 1: 1055}
c.fillrect(935, 655, 1100, 820, RED, 70); c.rect(935, 655, 1100, 820, RED, 6)
c.pill(1020, 628, '1–2: +12 V  KHÔNG chạm', 24, bg=RED, anchor='mm')
c.circle(botx[3], 772, 24, GRY, 5); c.pill(905, 850, '3: −V', 24, bg=GRY, fg=INK, anchor='mm'); c.line(905, 832, 905, 798, GRY, 4)
for n, lab, ly, col in [(4, '4 vàng: đo', 888, YEL), (5, '5 PUL− (xanh)', 850, GRN), (6, '6 DIR+ (nâu)', 888, GRN), (7, '7 vàng: đo', 850, YEL)]:
    c.circle(botx[n], 772, 24, col, 5); c.line(botx[n], 798, botx[n], ly - 14, col, 4)
    c.pill(botx[n], ly, lab, 24, bg=col, fg=INK, anchor='mm')
c.pill(262, 928, 'Phía trống của cọc 4–7: dây về Pi bắt vào đây', 22, anchor='lm')
c.pill(262, 962, 'Cọc 4 và 7 là PUL+ và DIR−: đo thông mạch để biết cọc nào', 22, bg=YEL, fg=INK, anchor='lm')
c.circle(topx[11], 695, 24, YEL, 5); c.circle(topx[12], 695, 24, YEL, 5)
c.pill(388, 640, '11–12: cặp dây vàng, cần xác định', 24, bg=YEL, fg=INK, anchor='lm')
c.pill(600, 540, 'Dây từ driver TB6600 xuống cọc 7 · 6 · 5 · 4', 22, bg=BLU, fg=INK, anchor='mm')
c.save('05-domino-2.jpg')

# 6. Driver TB6600 (p01)
c = Canvas('p01', (430, 40, 1500, 800), 1.3)
sx = [600, 655, 712, 770, 828, 885, 955, 1015, 1080, 1140, 1205, 1272]
c.rect(575, 440, 688, 560, GRY, 5); c.pill(630, 410, 'ENA: để trống', 22, bg=GRY, fg=INK, anchor='mm')
c.rect(690, 440, 915, 560, GRN, 6)
for x, lab, ty, col in [(700, 'cọc 4 hoặc 7', 300, YEL), (770, 'cọc 6', 345, GRN), (828, 'cọc 5', 300, GRN), (910, 'cọc 4 hoặc 7', 345, YEL)]:
    c.pill(x, ty, lab, 24, bg=col, fg=INK, anchor='mm')
c.pill(800, 250, 'Đã nối sẵn về domino 2:', 24, bg=GRN, fg=INK, anchor='mm')
c.rect(925, 430, 1310, 560, RED, 6); c.pill(1120, 380, 'Motor và nguồn 12 V: không chạm', 24, bg=RED, anchor='mm')
c.save('06-tb6600.jpg')

# 7. Nguồn tổ ong (p03)
c = Canvas('p03', (0, 150, 693, 1500), 1.3)
c.rect(52, 612, 222, 880, YEL, 6); c.pill(240, 720, 'Công tắc 110/220 V\nphải ở 220 V', 26, bg=YEL, fg=INK, anchor='lm')
c.rect(62, 1295, 540, 1440, RED, 6); c.pill(300, 1262, 'Cọc nguồn 220 V và 12 V: không nối gì vào Pi', 24, bg=RED, anchor='mm')
c.circle(575, 1388, 34, GRY, 5); c.pill(560, 1470, 'V ADJ: không vặn', 22, bg=GRY, fg=INK, anchor='mm')
c.save('07-nguon.jpg')

# 8. Hai thanh domino và driver nhìn chung (p04)
c = Canvas('p04', (0, 0, 1125, 1500), 1.0)
c.pill(240, 50, 'Module relay', 28, anchor='mm')
c.rect(0, 160, 580, 410, YEL, 6); c.pill(250, 132, 'Domino 1: dây tín hiệu khoá', 28, bg=YEL, fg=INK, anchor='mm')
c.rect(300, 425, 475, 1205, GRN, 6); c.pill(150, 760, 'Domino 2', 30, bg=GRN, fg=INK, anchor='mm')
c.rect(630, 575, 850, 1075, BLU, 6); c.pill(900, 540, 'Driver TB6600', 28, bg=BLU, fg=INK, anchor='mm')
c.pill(640, 1010, '4 dây tín hiệu', 22, bg=BLU, fg=INK, anchor='rm')
c.pill(150, 1250, 'Cọc 1–2: +12 V', 26, bg=RED, anchor='mm')
c.line(230, 1235, 318, 1090, RED, 5)
c.save('08-hai-domino.jpg')
