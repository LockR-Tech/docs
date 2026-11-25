"""Swimlane workflow diagram of WF-01 (drone delivery with home pickup) as it runs in the code on 2026-11-10
(docs/02-flows/flow-1-drone-delivery.md § 3). The SRS activity diagram 06c still shows the older flow where the
sender drops the parcel at the launch locker, so Report 6 uses this one.
Writes guide-assets/png/wf1-workflow.svg and .png (rendered with Playwright / Chrome).
Run: uv run --with playwright python gen_wf1_diagram.py
"""
import asyncio
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "png")

LANES = ["Customer (sender)\nmobile app", "System\nbackend", "Drone Technician\nmobile app",
         "Drone & Cabinet\nIoT", "Receiver\nkiosk / app"]
# (id, lane, row, text, kind)  kind: start | step | check | end | alt
NODES = [
    ("s", 0, 0, "Start", "start"),
    ("1", 0, 1, "Book a drone delivery: pickup point,\nreceiver locker, parcel, receiver", "step"),
    ("2", 1, 2, "Check distance ≤ 5 km, weight ≤ 5 kg,\nweather, free drone box; quote the fee", "check"),
    ("x", 0, 2, "Booking refused\n(message shown)", "alt"),
    ("3", 0, 3, "Pay by VietQR (SePay)\n→ order PAID, 6-digit pickup code", "step"),
    ("4", 1, 4, "Offer the pickup to the nearest\ndrone technician on shift (180 s)", "step"),
    ("5", 2, 5, "Accept, meet the sender, enter the\npickup code + photo → PICKED_UP", "step"),
    ("6", 2, 6, "Assign an idle drone at the launch\nlocker (battery > 20 %)", "step"),
    ("7", 2, 7, "Confirm loading: weight, seal code,\n3 checks; then Launch", "step"),
    ("8", 3, 8, "Fly to the receiver locker; ArUco read,\nlid opens, servo releases, lid closes", "step"),
    ("9", 1, 9, "Box OCCUPIED, READY_FOR_PICKUP;\nPIN sent to the receiver", "step"),
    ("10", 4, 10, "Enter the PIN at the kiosk\n(or open by Bluetooth) → take parcel", "step"),
    ("11", 1, 11, "Order COMPLETED, box released;\nadmin sees order and revenue", "step"),
    ("e", 1, 12, "End", "end"),
]
DOWN_FIRST = {("3", "4"), ("9", "10")}
EDGES = [("s", "1"), ("1", "2"), ("2", "3", "valid"), ("2", "x", "refused"), ("3", "4"), ("4", "5"), ("5", "6"),
         ("6", "7"), ("7", "8"), ("8", "9"), ("9", "10"), ("10", "11"), ("11", "e")]

LW, HEAD, RH, TOP, LEFT = 330, 70, 92, 10, 10
BW, BH = 276, 62
W = LEFT * 2 + LW * len(LANES)
H = TOP + HEAD + RH * 13 + 20
pos = {}
for nid, lane, row, _, kind in NODES:
    cx = LEFT + lane * LW + LW / 2
    cy = TOP + HEAD + row * RH + RH / 2
    pos[nid] = (cx, cy, kind)

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       'font-family="Segoe UI, Arial, sans-serif">',
       '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
       '<path d="M0,0 L10,5 L0,10 z" fill="#334155"/></marker></defs>',
       f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>']
for k, name in enumerate(LANES):
    x = LEFT + k * LW
    fill = "#F8FAFC" if k % 2 == 0 else "#FFFFFF"
    svg.append(f'<rect x="{x}" y="{TOP}" width="{LW}" height="{H - TOP - 10}" fill="{fill}" stroke="#94A3B8"/>')
    svg.append(f'<rect x="{x}" y="{TOP}" width="{LW}" height="{HEAD}" fill="#1F3A5F" stroke="#94A3B8"/>')
    for j, line in enumerate(name.split("\n")):
        svg.append(f'<text x="{x + LW / 2}" y="{TOP + 30 + j * 22}" text-anchor="middle" fill="white" '
                   f'font-size="{18 if j == 0 else 14}" font-weight="{700 if j == 0 else 400}">{escape(line)}</text>')


def anchor(nid, side):
    cx, cy, kind = pos[nid]
    if kind in ("start", "end"):
        r = 16
        return {"top": (cx, cy - r), "bottom": (cx, cy + r), "left": (cx - r, cy), "right": (cx + r, cy)}[side]
    return {"top": (cx, cy - BH / 2), "bottom": (cx, cy + BH / 2), "left": (cx - BW / 2, cy),
            "right": (cx + BW / 2, cy)}[side]


for e in EDGES:
    a, b = e[0], e[1]
    label = e[2] if len(e) > 2 else None
    ax, ay, _ = pos[a]
    bx, by, _ = pos[b]
    if abs(ax - bx) < 1:                       # same lane: straight down
        p0, p1 = anchor(a, "bottom"), anchor(b, "top")
        d = f"M{p0[0]},{p0[1]} L{p1[0]},{p1[1]}"
        lx, ly = p0[0] + 8, (p0[1] + p1[1]) / 2
    elif abs(ay - by) < 1:                     # same row: horizontal
        p0 = anchor(a, "left" if bx < ax else "right")
        p1 = anchor(b, "right" if bx < ax else "left")
        d = f"M{p0[0]},{p0[1]} L{p1[0]},{p1[1]}"
        lx, ly = min(p0[0], p1[0]) + 4, p0[1] + 22
    elif bx > ax and (a, b) in DOWN_FIRST:     # to the right, down first: avoids sharing a line with another edge
        p0 = anchor(a, "bottom")
        p1 = anchor(b, "left")
        d = f"M{p0[0]},{p0[1]} L{p0[0]},{p1[1]} L{p1[0]},{p1[1]}"
        lx, ly = p0[0] + 8, (p0[1] + p1[1]) / 2
    elif bx > ax:                              # to the right: leave from the side, go down into the target
        p0 = anchor(a, "right")
        p1 = anchor(b, "top")
        d = f"M{p0[0]},{p0[1]} L{p1[0]},{p0[1]} L{p1[0]},{p1[1]}"
        lx, ly = p1[0] + 8, (p0[1] + p1[1]) / 2 + 4
    else:                                      # to the left: go down first, then into the side of the target
        p0 = anchor(a, "bottom")
        p1 = anchor(b, "right")
        d = f"M{p0[0]},{p0[1]} L{p0[0]},{p1[1]} L{p1[0]},{p1[1]}"
        lx, ly = p0[0] + 8, (p0[1] + p1[1]) / 2
    dash = ' stroke-dasharray="6 4"' if label == "refused" else ""
    svg.append(f'<path d="{d}" fill="none" stroke="#334155" stroke-width="2"{dash} marker-end="url(#a)"/>')
    if label:
        svg.append(f'<text x="{lx}" y="{ly}" font-size="13" font-style="italic" fill="#475569">{label}</text>')

for nid, lane, row, text, kind in NODES:
    cx, cy, _ = pos[nid]
    if kind in ("start", "end"):
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="{"#0F172A" if kind == "start" else "white"}" '
                   f'stroke="#0F172A" stroke-width="{2 if kind == "start" else 5}"/>')
        continue
    fill, stroke = {"step": ("#E0F2FE", "#0369A1"), "check": ("#FEF3C7", "#B45309"),
                    "alt": ("#FEE2E2", "#B91C1C")}[kind]
    svg.append(f'<rect x="{cx - BW / 2}" y="{cy - BH / 2}" width="{BW}" height="{BH}" rx="10" fill="{fill}" '
               f'stroke="{stroke}" stroke-width="2"/>')
    if kind == "step" or kind == "check":
        svg.append(f'<circle cx="{cx - BW / 2}" cy="{cy - BH / 2}" r="13" fill="{stroke}"/>'
                   f'<text x="{cx - BW / 2}" y="{cy - BH / 2 + 5}" text-anchor="middle" font-size="13" '
                   f'font-weight="700" fill="white">{nid}</text>')
    lines = text.split("\n")
    for j, line in enumerate(lines):
        y = cy + (j - (len(lines) - 1) / 2) * 19 + 6
        svg.append(f'<text x="{cx}" y="{y}" text-anchor="middle" font-size="15" fill="#0F172A">{escape(line)}</text>')
svg.append("</svg>")
svg_text = "\n".join(svg)
open(os.path.join(OUT, "wf1-workflow.svg"), "w", encoding="utf-8").write(svg_text)


async def render():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        await pg.set_content(f'<html><body style="margin:0">{svg_text}</body></html>')
        await pg.locator("svg").screenshot(path=os.path.join(OUT, "wf1-workflow.png"))
        await b.close()


asyncio.run(render())
print("wrote", os.path.join(OUT, "wf1-workflow.png"), W, H)
