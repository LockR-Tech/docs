"""Assemble Report4 SDD: keep the template cover/styles, replace the body with the generated design."""
import io, json, os, re, struct, sys, zipfile
from xml.sax.saxutils import escape as xesc

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SCR, "tools"))
from split import split_body  # noqa: E402
import content_text as T  # noqa: E402
import gen_db  # noqa: E402  (ENT, REL, DBS)

TEMPLATE = sys.argv[1]
OUTPUT = sys.argv[2]
PNG = os.path.join(SCR, "out", "png")
FEATURES = json.load(open(os.path.join(SCR, "out", "features.json"), encoding="utf-8"))
SCAN = json.load(open(os.path.join(SCR, "scan.json"), encoding="utf-8"))
TW = 9360  # text width in dxa

body = []
media = []          # (zip name, bytes, rId)
fig_no = [0]


def t(text):
    return f'<w:t xml:space="preserve">{xesc(text)}</w:t>'


def run(text, b=False, i=False, color=None, sz=None):
    rp = ""
    if b:
        rp += "<w:b/>"
    if i:
        rp += "<w:i/>"
    if color:
        rp += f'<w:color w:val="{color}"/>'
    if sz:
        rp += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    return f"<w:r>{'<w:rPr>' + rp + '</w:rPr>' if rp else ''}{t(text)}</w:r>"


def para(content, style=None, jc=None, extra=""):
    pp = ""
    if style:
        pp += f'<w:pStyle w:val="{style}"/>'
    pp += extra
    if jc:
        pp += f'<w:jc w:val="{jc}"/>'
    body.append(f"<w:p>{'<w:pPr>' + pp + '</w:pPr>' if pp else ''}{content}</w:p>")


def H(level, text):
    para(run(text), f"Heading{level}")


def P(text, **kw):
    para(run(text, **kw), jc="both")


def page_break():
    body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')


def png_size(data):
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def figure(png_name, caption, max_h_in=8.3):
    data = open(os.path.join(PNG, png_name + ".png"), "rb").read()
    pw, ph = png_size(data)
    w_in, h_in = pw / 2 / 96, ph / 2 / 96          # exported at scale 2
    scale = min(6.5 / w_in, max_h_in / h_in, 1.0 if w_in < 3 else 99)
    cx, cy = int(w_in * scale * 914400), int(h_in * scale * 914400)
    k = len(media) + 1
    rid = f"rIdSdd{k}"
    media.append((f"word/media/sdd_{k}.png", data, rid))
    pic = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
           f'<wp:docPr id="{1000 + k}" name="Figure {k}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks '
           f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
           f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData '
           f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic '
           f'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{1000 + k}" '
           f'name="sdd_{k}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
           f'<a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/>'
           f'</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
           f'</wp:inline></w:drawing></w:r>')
    para(pic, jc="center", extra='<w:keepNext/><w:spacing w:before="120" w:after="60"/>')
    para(run(caption), "FigureCaption")


def table(headers, rows, widths, caption=None):
    assert abs(sum(widths) - TW) < 5, (sum(widths), headers)
    if caption:
        para(run(caption), "TableCaption", extra="<w:keepNext/>")
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{TW}" w:type="dxa"/><w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for s in
                     ("top", "left", "bottom", "right", "insideH", "insideV"))
           + f'</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/>'
             f'<w:right w:w="80" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']

    def cell(w, content, head=False):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="FFE8E1"/>' if head else ""
        paras = content if isinstance(content, list) else [content]
        ps = "".join(
            f'<w:p><w:pPr><w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>'
            f'{"<w:jc w:val=\"center\"/>" if head else ""}</w:pPr>{run(x, b=head, sz=20)}</w:p>' for x in paras)
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}<w:vAlign w:val="center"/></w:tcPr>{ps}</w:tc>'

    out.append('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' + "".join(cell(w, h, True) for w, h in zip(widths, headers)) + "</w:tr>")
    for r in rows:
        out.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(w, c) for w, c in zip(widths, r)) + "</w:tr>")
    out.append("</w:tbl>")
    body.append("".join(out))
    para("", extra='<w:spacing w:after="60"/>')


def toc(instr, placeholder):
    body.append('<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>{run(placeholder, i=True, color="808080")}'
                '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')


# ====================================================================== front matter
para(run("Table of Contents"), "TOCHeading")
toc('TOC \\o "1-4" \\h \\z \\u', "Table of contents - updated automatically when the document is opened in Word.")
page_break()
para(run("List of Figures"), "TOCHeading")
toc('TOC \\h \\z \\t "FigureCaption,1"', "List of figures.")
page_break()
para(run("List of Tables"), "TOCHeading")
toc('TOC \\h \\z \\t "TableCaption,1"', "List of tables.")
page_break()

H(1, "I. Record of Changes")
roc = [["28/10/2026", "A", "", "Initial Software Design Document: system architecture, package diagrams of the backend "
        "services, admin web, mobile app and IoT controller, database design of the 10 service databases, class "
        "diagrams, sequence diagrams and class specifications of 28 features."]]
roc += [["", "", "", ""] for _ in range(4)]
table(["Date", "A*\nM, D", "In charge", "Change Description"], roc, [1200, 800, 1500, 5860])
P("*A - Added M - Modified D - Deleted")
page_break()

H(1, "II. Software Design Document")
H(2, "1. System Design")
H(3, "1.1 System Architecture")
P(T.ARCH_INTRO)
figure("arch_system", "Figure 1.1: System architecture of Lock.R")
P("The table below explains each component of the architecture diagram.")
table(["No", "Component", "Description"],
      [[f"{i:02d}", n, d] for i, (n, d) in enumerate(T.ARCH_COMPONENTS, 1)], [600, 2200, 6560],
      "Table 1.1: Components of the system architecture")

# ---------------------------------------------------------------------- packages
H(3, "1.2 Package Diagram")
P("The package diagrams show how the source code of each sub-system is organised. The backend is a Maven "
  "multi-module project; every business service follows the same layered structure (API, application, domain, "
  "infrastructure) and depends on common-lib.")
pk = 0
tno = [1]


def pkg_section(title, img, caption, rows, tcaption):
    global pk
    pk += 1
    H(4, f"1.2.{pk} {title}")
    figure(img, f"Figure 1.2.{pk}: {caption}")
    table(["No", "Package", "Description"], [[f"{i:02d}", n, d] for i, (n, d) in enumerate(rows, 1)],
          [600, 2300, 6460], f"Table 1.2.{pk}: {tcaption}")


ov = [("api-gateway", "Spring Cloud Gateway: JWT validation, RBAC by path, routing, correlation id."),
      ("discovery-server", "Eureka service registry.")]
ov += [(s, T.SERVICE_DESC[s]) for s in T.SERVICE_DESC]
ov += [("common-lib/" + n, d) for n, d in T.COMMON_LIB]
pkg_section("Backend Package Diagram", "pkg_backend_overview", "Backend package diagram (modules)", ov,
            "Backend modules and common-lib packages")

for svc in ["auth-service", "user-service", "order-service", "locker-service", "payment-service",
            "notification-service", "iot-service", "store-service", "loyalty-service", "assistant-service"]:
    classes = SCAN[svc]
    rows = []
    for pname in sorted({c["pkg"] for c in classes} - {svc.split("-")[0]}):
        names = sorted(c["name"] for c in classes if c["pkg"] == pname)
        shown = ", ".join(names[:8]) + (f" … ({len(names)} classes)" if len(names) > 8 else "")
        rows.append((pname, f"{T.PKG_DESC.get(pname, '')} Main classes: {shown}."))
    nice = svc.replace("-", " ").title().replace("Iot", "IoT")
    pkg_section(f"{nice} Package Diagram", "pkg_" + svc.replace("-service", ""), f"{nice} package diagram", rows,
                f"Packages of {svc}")

pkg_section("Admin Web Application Package Diagram", "pkg_admin_web", "Admin web application package diagram",
            T.ADMIN_WEB_PKGS, "Packages of the admin web application")
pkg_section("Mobile Application Package Diagram", "pkg_mobile_app", "Mobile application package diagram",
            T.MOBILE_PKGS, "Packages of the mobile application")
pkg_section("Mobile Feature Module Package Diagram", "pkg_mobile_feature",
            "Package structure inside one mobile feature module", T.MOBILE_FEATURE_PKGS,
            "Layers of a mobile feature module")
pkg_section("IoT Locker Controller Package Diagram", "pkg_iot_controller", "IoT locker controller package diagram",
            T.IOT_PKGS, "Packages of the IoT locker controller")

# ---------------------------------------------------------------------- database
H(2, "2. Database Design")
P(T.DB_INTRO)
SRS_DESC = {}
srs = open(os.path.join(SCR, "srs.txt"), encoding="utf-8").read()
for m in re.finditer(r"^\d+ \| (\w+) \| (.*?) / - Primary key", srs, re.M):
    SRS_DESC[m.group(1)] = m.group(2).strip()
SRS_DESC["cabinet_hardware_configs"] = ("Hardware configuration of a cabinet (GPIO / RS485 wiring, lid tuning) edited "
                                        "by technicians and applied to the Pi, with apply status.")
ENT, REL = gen_db.ENT, gen_db.REL
for di, (db, svc, cols) in enumerate(gen_db.DBS, 1):
    H(3, f"2.{di} {db} ({svc})")
    figure("db_" + db, f"Figure 2.{di}: Database diagram of {db}")
    rows = []
    ents = [e for col in cols for e, _ in col]
    for k, e in enumerate(sorted(ents, key=lambda x: ENT[x]["table"]), 1):
        tbl = ENT[e]["table"]
        pks = [f["name"] for f in ENT[e]["fields"] if f["pk"]]
        fks = []
        for child, col, parent, _ in REL:
            if child == e:
                same = ENT[parent]["service"] == ENT[e]["service"]
                fks.append(f"{col} -> {ENT[parent]['table']}" + ("" if same else f" (logical, {ENT[parent]['service']})"))
        rows.append([f"{k:02d}", tbl, [SRS_DESC.get(tbl, ""), "- Primary keys: " + ", ".join(pks),
                                       "- Foreign keys: " + (", ".join(fks) if fks else "none")]])
    table(["No", "Table", "Description"], rows, [600, 2500, 6260], f"Table 2.{di}: Table descriptions of {db}")

# ---------------------------------------------------------------------- detailed design
H(2, "3. Detailed Design")
P("This section gives, for every feature, the class diagram of the classes that take part, the sequence diagram(s) "
  "of its main flows and the specification of the controller and service classes. Controllers receive requests "
  "already authenticated by the API gateway (X-User-Id, X-User-Roles), services hold the business logic, Feign "
  "clients call other services and repositories access the database of the service. Names are the real class and "
  "method names in the source code.")
for fi, f in enumerate(FEATURES, 1):
    H(3, f"3.{fi} {f['title']}")
    P(f["intro"])
    sub = 1
    H(4, f"3.{fi}.{sub} Class Diagram")
    figure(f["class_image"], f"Figure 3.{fi}.{sub}: Class diagram - {f['title']}")
    for s in f["seqs"]:
        sub += 1
        H(4, f"3.{fi}.{sub} {s['title']}")
        figure(s["image"], f"Figure 3.{fi}.{sub}: Sequence diagram - {s['title']}")
    sub += 1
    H(4, f"3.{fi}.{sub} Class Specification")
    for si, sp in enumerate(f["specs"]):
        letter = "abcdefghijklmnop"[si]
        para(run(f"3.{fi}.{sub}.{letter} {sp['cls']}", b=True), extra='<w:keepNext/><w:spacing w:before="120" w:after="60"/>')
        table(["No", "Method", "Description"],
              [[f"{i:02d}", m[0], m[1]] for i, m in enumerate(sp["methods"], 1)], [600, 4300, 4460],
              f"Table 3.{fi}.{sub}.{letter}: {sp['cls']} description")

# ====================================================================== write the package
zin = zipfile.ZipFile(TEMPLATE)
doc = zin.read("word/document.xml").decode("utf-8")
head, items, tail = split_body(doc)
cover = items[:11]  # logo .. date
cover[10] = cover[10].replace("– Hanoi, August 2019 –", "– Ho Chi Minh City, October 2026 –")
cover_txt = "".join(cover)
if "Ho Chi Minh" not in cover_txt:   # date split over runs: rebuild that paragraph
    cover[10] = re.sub(r"(<w:r>.*</w:r>)", run("– Ho Chi Minh City, October 2026 –", sz=28), cover[10], count=1, flags=re.S)
sect = items[-1]
footer = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdSddFooter"/>'
          + sect[len("<w:sectPr>"):] if sect.startswith("<w:sectPr>") else sect)
new_doc = head + "".join(cover) + '<w:p><w:r><w:br w:type="page"/></w:r></w:p>' + "".join(body) + footer + tail

rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
add = "".join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
              f'Target="media/{os.path.basename(n)}"/>' for n, _, rid in media)
add += ('<Relationship Id="rIdSddFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" '
        'Target="footer1.xml"/>')
rels = rels.replace("</Relationships>", add + "</Relationships>")

ct = zin.read("[Content_Types].xml").decode("utf-8")
ct = ct.replace("</Types>", '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-'
                            'officedocument.wordprocessingml.footer+xml"/></Types>')

styles = zin.read("word/styles.xml").decode("utf-8")
styles = styles.replace("</w:styles>",
                        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="FigureCaption"><w:name w:val="FigureCaption"/>'
                        '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="60" w:after="240"/>'
                        '<w:jc w:val="center"/></w:pPr><w:rPr><w:i/><w:color w:val="1F3864"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
                        '</w:rPr></w:style></w:styles>')
settings = zin.read("word/settings.xml").decode("utf-8")

FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
          '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>'
          '<w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')

# well-formedness check before writing
from xml.etree import ElementTree as ET  # noqa: E402
for name, x in (("document", new_doc), ("styles", styles), ("settings", settings), ("rels", rels), ("ct", ct)):
    ET.fromstring(x.encode("utf-8"))

zout = zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    if it.filename == "word/document.xml":
        zout.writestr(it, new_doc)
    elif it.filename == "word/_rels/document.xml.rels":
        zout.writestr(it, rels)
    elif it.filename == "[Content_Types].xml":
        zout.writestr(it, ct)
    elif it.filename == "word/styles.xml":
        zout.writestr(it, styles)
    elif it.filename == "word/settings.xml":
        zout.writestr(it, settings)
    else:
        zout.writestr(it, zin.read(it.filename))
zout.writestr("word/footer1.xml", FOOTER)
for n, data, _ in media:
    zout.writestr(n, data)
zout.close()
print("figures:", len(media), "body elements:", len(body), "->", OUTPUT)
