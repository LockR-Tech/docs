"""Tiny draw.io (mxGraph) XML builder + headless-Chrome PNG export via the official viewer."""
import html, json, os, subprocess, itertools

class Diagram:
    def __init__(self, name):
        self.name = name
        self.cells = []
        self._ids = itertools.count(2)
        self.bounds = [10**9, 10**9, -10**9, -10**9]

    def _id(self):
        return f"c{next(self._ids)}"

    def _grow(self, x, y, w, h):
        b = self.bounds
        b[0] = min(b[0], x); b[1] = min(b[1], y); b[2] = max(b[2], x + w); b[3] = max(b[3], y + h)

    def vertex(self, label, x, y, w, h, style, parent="1", cid=None, grow=True):
        cid = cid or self._id()
        self.cells.append(f'<mxCell id="{cid}" value="{html.escape(label, quote=True)}" style="{style}" vertex="1" parent="{parent}">'
                          f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
        if grow and parent == "1":
            self._grow(x, y, w, h)
        return cid

    def edge(self, src, tgt, style, label="", points=(), parent="1", src_pt=None, tgt_pt=None, label_x=None):
        cid = self._id()
        pts = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in points)
        arr = f'<Array as="points">{pts}</Array>' if points else ""
        sp = f'<mxPoint x="{src_pt[0]:.1f}" y="{src_pt[1]:.1f}" as="sourcePoint"/>' if src_pt else ""
        tp = f'<mxPoint x="{tgt_pt[0]:.1f}" y="{tgt_pt[1]:.1f}" as="targetPoint"/>' if tgt_pt else ""
        s = f' source="{src}"' if src else ""
        t = f' target="{tgt}"' if tgt else ""
        geo = f'<mxGeometry x="{label_x}" relative="1" as="geometry">' if label_x is not None else '<mxGeometry relative="1" as="geometry">'
        self.cells.append(f'<mxCell id="{cid}" value="{html.escape(label, quote=True)}" style="{style}" edge="1" parent="{parent}"{s}{t}>'
                          f'{geo}{sp}{tp}{arr}</mxGeometry></mxCell>')
        return cid

    def xml(self):
        body = "".join(self.cells)
        return (f'<mxfile host="app.diagrams.net"><diagram name="{html.escape(self.name)}" id="{self.name}">'
                f'<mxGraphModel dx="1600" dy="1000" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
                f'fold="1" page="0" pageScale="1" pageWidth="1600" pageHeight="1200" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram></mxfile>')

    def save(self, out_dir, scale=1.5, margin=30):
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, self.name + ".drawio")
        open(path, "w", encoding="utf-8").write(self.xml())
        png = os.path.join(out_dir, self.name + ".png")
        render(path, png, self.bounds, scale, margin)
        return path, png

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")

def render(drawio_path, png_path, bounds, scale=1.5, margin=30):
    xml = open(drawio_path, encoding="utf-8").read()
    w = int(bounds[2] - bounds[0] + 2 * margin + 40)
    h = int(bounds[3] - bounds[1] + 2 * margin + 40)
    cfg = {"xml": xml, "toolbar": "", "highlight": "none", "nav": False, "resize": False, "zoom": 1, "border": margin, "lightbox": False}
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}</style></head>
<body><div class="mxgraph" style="width:{w}px" data-mxgraph="{html.escape(json.dumps(cfg), quote=True)}"></div>
<script>window.DRAWIO_BASE_URL='https://app.diagrams.net';</script>
<script src="file:///{HERE.replace(os.sep, '/')}/viewer-static.min.js"></script></body></html>"""
    hp = os.path.join(HERE, "_render.html")
    open(hp, "w", encoding="utf-8").write(page)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--force-device-scale-factor={scale}", f"--window-size={w},{h}", "--virtual-time-budget=20000",
                    f"--screenshot={png_path}", "file:///" + hp.replace(os.sep, "/")],
                   check=True, capture_output=True, timeout=180)
