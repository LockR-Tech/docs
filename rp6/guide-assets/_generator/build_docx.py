"""Assemble Report 6 – Software User Guides for Lock.R.

Keeps the cover page and styles of the FPT template (rp6/Report6_Software User Guides.docx) and writes the body in
the structure of chapter "VI. Release Package & User Guides" of the reference final report
(rp3/Copy of SP25SE126_..._FinalReport.docx): Record of Changes, Deliverable Package, Installation Guides,
User Manual (overview + one section per main workflow WF-01..WF-04 of the Review 2 Design Brief).

Workflow steps come from guide-assets/data/wf1..wf4.json; screenshots are the real app screenshots kept in
rp3/srs-assets (plus guide-assets/png). Run:
    python build_docx.py "<template.docx>" "<output.docx>"
then finalize_docx.ps1 (Word updates the TOC / lists and exports a PDF).
"""
import json
import os
import re
import struct
import sys
import zipfile
from xml.sax.saxutils import escape as xesc

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.dirname(HERE)                       # rp6/guide-assets
DOCS = os.path.abspath(os.path.join(ASSETS, "..", ".."))   # docs repo root
TEMPLATE, OUTPUT = sys.argv[1:3]
TW = 9050  # text width (dxa): A4 11906 - margins 1440 / 1416
TW_IN = TW / 1440

body, media = [], []
fig_count, tab_count = {}, {}


# ---------------------------------------------------------------------------------------------- primitives
def run(text, b=False, i=False, sz=None, color=None, font=None, shade=None):
    rp = ""
    if font:
        rp += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
    if b:
        rp += "<w:b/><w:bCs/>"
    if i:
        rp += "<w:i/>"
    if color:
        rp += f'<w:color w:val="{color}"/>'
    if sz:
        rp += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if shade:
        rp += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    return f'<w:r>{"<w:rPr>" + rp + "</w:rPr>" if rp else ""}<w:t xml:space="preserve">{xesc(text)}</w:t></w:r>'


def rich(text, **kw):
    """`code` spans in Consolas, **bold** spans in bold."""
    out = []
    for part in re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text):
        if not part:
            continue
        if part.startswith("`"):
            out.append(run(part[1:-1], font="Consolas", sz=(kw.get("sz") or 21) - 2, shade="F2F2F2",
                           **{k: v for k, v in kw.items() if k not in ("font", "sz")}))
        elif part.startswith("**"):
            out.append(run(part[2:-2], b=True, **{k: v for k, v in kw.items() if k != "b"}))
        else:
            out.append(run(part, **kw))
    return "".join(out)


def para(content, style=None, jc=None, extra=""):
    pp = (f'<w:pStyle w:val="{style}"/>' if style else "") + extra + (f'<w:jc w:val="{jc}"/>' if jc else "")
    body.append(f'<w:p>{"<w:pPr>" + pp + "</w:pPr>" if pp else ""}{content}</w:p>')


def H(level, text):
    para(run(text), f"Heading{level}")


def P(text, **kw):
    para(rich(text, **kw), jc="both", extra='<w:spacing w:before="60" w:after="60"/>')


def bullet(text, level=0):
    ind = 360 + level * 360
    para(run("•\t") + rich(text), jc="both",
         extra=f'<w:tabs><w:tab w:val="left" w:pos="{ind}"/></w:tabs><w:spacing w:before="20" w:after="20"/>'
               f'<w:ind w:left="{ind}" w:hanging="300"/>')


def step(label, text):
    para(run(label + " ", b=True) + rich(text), jc="both",
         extra='<w:keepNext/><w:spacing w:before="100" w:after="40"/>')


def sub(text):
    para(run(text, b=True, color="1F3A5F"), extra='<w:keepNext/><w:spacing w:before="200" w:after="60"/>')


def code(lines):
    """Command block: one shaded paragraph per line, Consolas."""
    lines = lines.strip("\n").split("\n")
    for k, ln in enumerate(lines):
        sp = f'<w:spacing w:before="{60 if k == 0 else 0}" w:after="{60 if k == len(lines) - 1 else 0}" w:line="240" w:lineRule="auto"/>'
        para(run(ln or " ", font="Consolas", sz=18), extra=f'<w:keepLines/>{"<w:keepNext/>" if k < len(lines) - 1 else ""}'
             f'<w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/><w:ind w:left="284" w:right="284"/>{sp}')


def page_break():
    body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')


def toc(instr, placeholder):
    body.append('<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>{run(placeholder, i=True, color="808080")}'
                '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')


# ---------------------------------------------------------------------------------------------- figures
def resolve(path):
    red = os.path.join(ASSETS, "png", "redacted", os.path.basename(path))
    if os.path.exists(red):  # copy with personal data pixelated (redact.py)
        return red
    if os.path.isabs(path):
        return path
    for base in (DOCS, ASSETS):
        p = os.path.join(base, path)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(path)


def png_size(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    # JPEG: walk the markers to SOF
    i = 2
    while i < len(data):
        marker, ln = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + ln
    raise ValueError("unknown image")


def shrink(data, w_in, h_in, dpi=220):
    """Downscale to ~220 dpi at the printed size (sharp on paper, ~5x smaller .docx). Needs Pillow; without it
    the original bytes are embedded."""
    try:
        import io
        from PIL import Image
    except ImportError:
        return data
    im = Image.open(io.BytesIO(data))
    tw, th = int(w_in * dpi), int(h_in * dpi)
    if im.width <= tw * 1.1:
        return data
    im = im.convert("RGB").resize((tw, th), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue() if len(buf.getvalue()) < len(data) else data


def drawing(path, w_in, h_in):
    data = shrink(open(resolve(path), "rb").read(), w_in, h_in)
    ext = "jpg" if data[:2] == b"\xff\xd8" else "png"
    k = len(media) + 1
    rid = f"rIdUg{k}"
    media.append((f"word/media/ug_{k}.{ext}", data, rid))
    cx, cy = int(w_in * 914400), int(h_in * 914400)
    return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{3000 + k}" name="Picture {k}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks '
            f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData '
            f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic '
            f'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{3000 + k}" '
            f'name="ug_{k}.{ext}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
            f'<a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/>'
            f'</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:ln w="6350"><a:solidFill><a:srgbClr '
            f'val="BFBFBF"/></a:solidFill></a:ln></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def figure(paths, caption, section, max_w=None, max_h=None):
    """One figure = one or more images side by side, one caption numbered per section (Figure 3.2.n)."""
    if isinstance(paths, str):
        paths = [paths]
    sizes = [png_size(open(resolve(p), "rb").read()) for p in paths]
    portrait = all(h / w > 1.4 for w, h in sizes)
    gap = 0.15
    if portrait:  # phone screenshots: same height, side by side
        h_in = max_h or (3.6 if len(paths) == 1 else 3.3)
        widths = [h_in * w / h for w, h in sizes]
        while sum(widths) + gap * (len(paths) - 1) > TW_IN - 0.1:
            h_in -= 0.1
            widths = [h_in * w / h for w, h in sizes]
        dims = [(wd, h_in) for wd in widths]
    else:
        mw = (max_w or TW_IN - 0.05) if len(paths) == 1 else (TW_IN - gap * (len(paths) - 1)) / len(paths)
        mh = max_h or 4.3
        dims = []
        for w, h in sizes:
            s = min(mw / (w / 96), mh / (h / 96), 1e9)
            dims.append((w / 96 * s, h / 96 * s))
    pics = []
    for k, (p, (wd, ht)) in enumerate(zip(paths, dims)):
        if k:
            pics.append(f'<w:r><w:t xml:space="preserve">  </w:t></w:r>')
        pics.append(drawing(p, wd, ht))
    para("".join(pics), jc="center", extra='<w:keepNext/><w:spacing w:before="120" w:after="40"/>')
    fig_count[section] = fig_count.get(section, 0) + 1
    para(run(f"Figure {section}.{fig_count[section]}: {caption}"), "FigureCaption")


def table(headers, rows, widths, caption=None, section=None, center_cols=(), merge_first=False, mono_cols=()):
    """Template table look (as Report 5): single borders, header fill FFE8E1, Arial 10."""
    assert abs(sum(widths) - TW) < 5, (sum(widths), headers)
    if caption:
        tab_count[section] = tab_count.get(section, 0) + 1
        para(run(f"Table {section}.{tab_count[section]}: {caption}"), "TableCaption", extra="<w:keepNext/>")
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{TW}" w:type="dxa"/><w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for s in
                     ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/>'
             '<w:right w:w="80" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="04A0"/></w:tblPr>'
           + f"<w:tblGrid>{grid}</w:tblGrid>"]

    def cell(w, content, head=False, center=False, vmerge=None, mono=False):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="FFE8E1"/>' if head else ""
        vm = "" if vmerge is None else ('<w:vMerge w:val="restart"/>' if vmerge == "restart" else "<w:vMerge/>")
        lines = content.split("\n") if content else [""]
        jc = '<w:jc w:val="center"/>' if head or center else ""
        ps = "".join(
            '<w:p><w:pPr><w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>' + jc + "</w:pPr>"
            + ((run(x, b=True, sz=20, font="Arial") if head else
                run(x, sz=18, font="Consolas") if mono else rich(x, sz=20, font="Arial")) if x else "")
            + "</w:p>" for x in lines)
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{vm}{shd}<w:vAlign w:val="center"/></w:tcPr>{ps}</w:tc>'

    out.append('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>'
               + "".join(cell(w, h, True) for w, h in zip(widths, headers)) + "</w:tr>")
    prev = None
    for r in rows:
        cs = []
        for k, (w, c) in enumerate(zip(widths, r)):
            vm = None
            if merge_first and k == 0:
                vm = "cont" if c == prev else "restart"
                c = "" if c == prev else c
            cs.append(cell(w, c, center=k in center_cols, vmerge=vm, mono=k in mono_cols))
        prev = r[0] if merge_first else None
        out.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cs) + "</w:tr>")
    out.append("</w:tbl>")
    body.append("".join(out))
    para("", extra='<w:spacing w:after="60"/>')


# ================================================================================================ content
para(run("Table of Contents"), "TOCHeading")
toc('TOC \\o "1-3" \\h \\z \\u', "Table of contents - right-click and choose Update Field.")
page_break()
para(run("List of Figures"), "TOCHeading")
toc('TOC \\h \\z \\t "FigureCaption,1"', "List of figures.")
para(run("List of Tables"), "TOCHeading")
toc('TOC \\h \\z \\t "TableCaption,1"', "List of tables.")
page_break()

# ------------------------------------------------------------------------------------------------ I
H(1, "I. Record of Changes")
ROC = [
    ["14/11/2026", "A", "Nguyễn Quốc Bảo Huy",
     "Initial version: Deliverable Package with the release versions of all repositories; Installation Guides "
     "(system requirements; installation of the back-end, admin web, mobile app, locker controller and kiosk; "
     "continuous deployment to production)."],
    ["14/11/2026", "A", "Lê Thị Yến Vi",
     "User Manual: overview of the system, roles and workflows; Workflow 1 – Drone Delivery with Home Pickup."],
    ["14/11/2026", "A", "Nguyễn Quốc Bảo Huy",
     "User Manual: Workflow 2 – Rent a Box or Send a Parcel via Locker (mobile app, kiosk, Bluetooth open, "
     "overdue fee, admin revenue)."],
    ["14/11/2026", "A", "Trương Nguyễn Thái Bình",
     "User Manual: Workflow 3 – Box Incident to Resolution (customer report, locker technician ticket handling)."],
    ["14/11/2026", "A", "Trần Kim Nhã",
     "User Manual: Workflow 4 – Maintenance of Lockers and Drones (inspection schedules, periodic inspection, "
     "drone fleet maintenance)."],
    ["15/11/2026", "M", "Nguyễn Quốc Bảo Huy",
     "Re-captured every screenshot of the installation guides and the four workflows on the current production "
     "build (mobile app, kiosk, admin web) and updated the step descriptions to the new screens; new workflow "
     "diagram for Workflow 1; personal data in screenshots pixelated."],
]
table(["Date", "A*\nM, D", "In charge", "Change Description"], ROC, [1300, 800, 2300, 4650], center_cols=(0, 1))
P("*A - Added M - Modified D - Deleted")
page_break()

# ------------------------------------------------------------------------------------------------ II.1
H(1, "II. Release Package & User Guides")
H(2, "1. Deliverable Package")
P("The release delivered with this report is the state of the six Lock.R repositories on 14/11/2026. All "
  "repositories belong to the GitHub organization **LockR-Tech** (https://github.com/LockR-Tech). Every change "
  "reaches the `main` branch through a reviewed pull request, and merging to `main` deploys the change to "
  "production automatically (Section 2.2.7).")
DELIV = [
    ["1", "Project Schedule/Tracking",
     "Report3_Project Tracking_LockR.xlsx (docs/rp3): work breakdown structure of 88 functions/screens with "
     "planned iteration and status, issues, defects and Q&A sheets. Day-to-day progress, risks and the next "
     "tasks are tracked in docs/STATUS.md; the team meets on Google Meet and chats on Messenger."],
    ["2", "Project Backlog",
     "Gap lists of the four business flows in docs/02-flows (IDs F1-Gxx … F4-Gxx). Each gap is "
     "implemented on a branch named after its ID and merged by a pull request with the footer `Refs: <gap ID>` "
     "(548 merged pull requests across the repositories)."],
    ["3", "Source Codes",
     "Public GitHub repositories (commit on 14/11/2026):\n"
     "• backend – 12 Spring Boot 3.5.14 microservices + common-lib, Java 21 (38f3cee)\n"
     "• frontend – admin web (React 19, Vite 7) + landing page (7a7a040)\n"
     "• mobile – Flutter 3.44 app for customers and technicians, version 1.0.0 (8b0ad34)\n"
     "• iot – Raspberry Pi cabinet controller (Python 3.13), kiosk UI (React), simulators (f7bc145)\n"
     "• docs – reports, business flows, diagrams, ADRs, runbooks (this report)\n"
     "• legal – privacy policy and terms of service pages (df4c316)\n"
     "Tag `review-2` marks the Review 2 baseline in every repository."],
    ["4", "Database Script(s)",
     "PostgreSQL 16, one database per service. Schemas are created by 119 Flyway migration scripts "
     "(backend/<service>/src/main/resources/db/migration, V1…Vn) that run automatically when a service "
     "starts. Seed scripts for local and demo data are in backend/scripts (seed-local-complete.sql, "
     "seed-demo-accounts-ms.sql). The ERDs are in Report 4."],
    ["5", "Final Report Document",
     "Reports 1–6 in the docs repository (rp1 … rp6): Project Introduction, Project Management Plan, Software "
     "Requirement Specification, Software Design Document, Software Test Documentation and Software User Guides."],
    ["6", "Test Cases Document",
     "Report5_Test Documentation_LockR.docx, Report5_Test Report_LockR.xlsx (integration / system test cases and "
     "statistics) and Report5_Unit Test_LockR.xls (unit test matrix with real JUnit results) in docs/rp5. Unit "
     "tests run in GitHub Actions on every pull request."],
    ["7", "Defects List",
     "Sheet “Defects” of Report3_Project Tracking_LockR.xlsx (25 defects with tester, assignee, status and the "
     "fixing pull request) and the failed / pending cases of the test report."],
    ["8", "Issues List",
     "Sheet “Issues” of Report3_Project Tracking_LockR.xlsx (21 project issues incl. security risks SEC-xx with "
     "priority, owner and dates) and the risk table in docs/STATUS.md § 2."],
    ["9", "Slide", "Review presentation slides designed with Canva."],
    ["10", "Release Builds",
     "• Android app: Lock.R 1.0.0 (build 102), GitHub Release apk-1.0.0-102 of the mobile repository "
     "(LockR-latest.apk always points to the newest build)\n"
     "• Admin web: https://admin.locker-drone.tech · Landing page: https://locker-drone.tech\n"
     "• Back-end API: https://api.locker-drone.tech (Swagger UI at /swagger-ui/index.html)\n"
     "• Locker controller + kiosk: iot repository, installed on the Raspberry Pi of cabinet CAB-TU01"],
]
table(["No.", "Deliverable Item", "Description"], DELIV, [700, 2000, 6350], "Deliverable Package", "1",
      center_cols=(0,))

# ------------------------------------------------------------------------------------------------ II.2
H(2, "2. Installation Guides")
P("Lock.R has four installable parts: the back-end on a Linux server, the admin web in the browser, the mobile "
  "app on Android phones, and the locker controller with its kiosk screen on a Raspberry Pi inside each cabinet. "
  "End users only need Section 2.2.1 (mobile app) or 2.2.2 (admin web); the other sections are for developers "
  "and operators who build the system from source.")
H(3, "2.1 System Requirements")
H(4, "2.1.1 Hardware requirements")
HW = [
    ["Back-end server", "2 vCPU, 8 GB RAM + 4 GB swap, SSD storage, public IPv4, ports 22/80/443 open",
     "Azure VM Standard_B2as_v2 (2 vCPU, 8 GB), Ubuntu 24.04, Standard SSD"],
    ["Developer computer", "4-core CPU, 16 GB RAM, 30 GB free disk (Docker images, Android emulator)",
     "Windows 11 laptops, 16 GB RAM"],
    ["Admin computer", "Any PC or laptop with a modern browser, screen ≥ 1366 × 768", "Windows 11, Chrome"],
    ["Mobile phone", "Android 7.0 (API 24) or later, Bluetooth Low Energy, GPS, camera, Internet",
     "Android phones (Android 11–15)"],
    ["Locker controller", "Raspberry Pi 5 (4 GB), microSD ≥ 32 GB or USB SSD, Wi-Fi or LAN",
     "Raspberry Pi 5 + 7-inch touch screen (1024 × 600) as kiosk"],
    ["Cabinet hardware", "Relay module (one channel per box, 3.3 V-triggerable), 12 V solenoid locks with door "
     "signal, 12 V power supply; for the drone port: TB6600 driver, Nema 17 stepper, limit switches",
     "Cabinet CAB-TU01: 7 boxes, sliding lid on the roof (drone landing pad)"],
    ["Drone (WF-01, optional)", "Multirotor with flight controller (MAVLink), companion Raspberry Pi with camera "
     "(ArUco marker) and a release servo", "Demo orders can run with the built-in drone simulator"],
]
table(["Component", "Minimum requirement", "Used in this project"], HW, [2100, 4100, 2850],
      "Hardware requirements", "2.1")
H(4, "2.1.2 Software requirements")
SW = [
    ["Back-end", "Java Development Kit (Temurin / Oracle)", "21"],
    ["Back-end", "Apache Maven", "3.9 or later"],
    ["Back-end", "Docker Engine / Docker Desktop with Compose v2", "Latest stable"],
    ["Back-end (in Docker)", "PostgreSQL · pgvector · RabbitMQ · Eclipse Mosquitto", "16 · pg16 · 3 · 2"],
    ["Admin web, kiosk", "Node.js with npm", "24.x (22.x on the Raspberry Pi)"],
    ["Mobile app", "Flutter SDK (Dart ^3.11.5)", "3.44.9 stable"],
    ["Mobile app", "Android Studio with Android SDK and an emulator", "Latest stable"],
    ["Locker controller", "Raspberry Pi OS (64-bit, Trixie)", "Latest"],
    ["Locker controller", "Python with uv package manager", "Python 3.13, uv 0.12"],
    ["Locker controller", "PostgreSQL (local buffer) · Chromium (kiosk)", "From Raspberry Pi OS"],
    ["All", "Git · Visual Studio Code · Google Chrome", "Latest stable"],
    ["External services", "Firebase (phone / Google sign-in, push), SePay (VietQR), Cloudinary (images), "
     "Gmail SMTP, Anthropic Claude + Voyage AI (assistant), OpenStreetMap / OSRM, Open-Meteo", "Accounts / API keys"],
]
table(["Purpose", "Software", "Version"], SW, [2000, 4850, 2200], "Software requirements", "2.1")

H(3, "2.2 Installation Instruction")
# ---- 2.2.1 mobile app (end users)
H(4, "2.2.1 Mobile app (customers and technicians)")
P("Customers, locker technicians and drone technicians use the same Android app; the app opens the home screen of "
  "the role of the signed-in account.")
step("Step 1:", "On the Android phone, open https://github.com/LockR-Tech/mobile/releases/latest and download "
     "**LockR-latest.apk** (direct link: https://github.com/LockR-Tech/mobile/releases/latest/download/LockR-latest.apk).")
figure("png/i01-github-release-apk.png", "GitHub release page of the Android app", "2.2", max_h=3.6)
step("Step 2:", "Open the downloaded file. When Android asks, allow the browser to “Install unknown apps”, then "
     "tap “Install”. A newer build installs over the old one without uninstalling (all builds are signed with "
     "the same key).")
step("Step 3:", "Open Lock.R and allow the permissions it asks for: notifications (order updates), location "
     "(nearby lockers, technician shift), Bluetooth (open a box by Bluetooth) and camera (QR codes and photos).")
step("Step 4:", "Sign in with email or phone number and password, with an email OTP, with Google or with a phone "
     "number (SMS OTP). New customers tap “Đăng ký” (Sign up). Technician accounts are created by the admin.")
figure("png/install/i06-mobile-login.png", "Sign-in screen (mobile app)", "2.2", max_h=3.6)

# ---- 2.2.2 admin web (administrators)
H(4, "2.2.2 Admin web (administrators)")
P("The admin web needs no installation; it is a web application served by Cloudflare.")
step("Step 1:", "Open https://admin.locker-drone.tech in Google Chrome or Microsoft Edge. The language can be "
     "switched between Vietnamese, English and Japanese at the top right.")
step("Step 2:", "Enter the admin email and password, then click “Đăng nhập” (Sign in).")
figure("png/install/i05-admin-login.png", "Sign-in screen (admin web)", "2.2")
step("Step 3:", "Enter the 6-digit code sent to the admin email (two-factor authentication, valid 300 seconds, "
     "5 wrong attempts close the session) and click “Xác nhận” (Confirm). The dashboard opens.")
figure("png/install/i07-admin-otp.png", "Two-factor authentication screen (admin web)", "2.2")

# ---- 2.2.3 back-end
H(4, "2.2.3 Back-end (developers)")
step("Step 1:", "Install Git, JDK 21, Maven 3.9+ and Docker Desktop (Section 2.1.2).")
step("Step 2:", "Clone the repository and open it:")
code("git clone https://github.com/LockR-Tech/backend.git\ncd backend")
step("Step 3:", "Create the file `backend/.env` (it is ignored by Git). `APP_SECURITY_JWT_SECRET` and the three "
     "`SEPAY_*` variables are required – Docker Compose refuses to start without them; the others enable optional "
     "integrations. Only variable names are listed here; real values are never committed.")
ENV = [
    ["APP_SECURITY_JWT_SECRET", "Required", "Secret that signs JWT access tokens (e.g. `openssl rand -base64 48`)"],
    ["SEPAY_API_KEY, SEPAY_BANK_BIN, SEPAY_BANK_ACCOUNT_NO", "Required", "VietQR bank transfer and SePay webhook"],
    ["BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_PASSWORD", "Recommended", "First admin account created at start-up"],
    ["SPRING_MAIL_*", "Optional", "SMTP for OTP and pickup-code emails"],
    ["FIREBASE_CREDENTIALS_JSON", "Optional", "Phone / Google sign-in and push notifications"],
    ["CLOUDINARY_URL", "Optional", "Photo upload (incident reports, avatars)"],
    ["ANTHROPIC_API_KEY, EMBEDDING_API_KEY", "Optional", "AI assistant (Claude answers, Voyage embeddings)"],
    ["MQTT_BROKER_URL, MQTT_USERNAME, MQTT_PASSWORD", "Optional", "MQTT broker of the locker controllers"],
    ["API_GATEWAY_PORT", "Optional", "Host port of the API gateway (default 18080)"],
]
table(["Variable", "Need", "Purpose"], ENV, [3850, 1300, 3900], "Back-end environment variables", "2.2",
      mono_cols=(0,))
step("Step 4:", "Build the services (the Dockerfiles copy the built jar files) and start the whole stack – "
     "PostgreSQL, RabbitMQ, Eureka, the API gateway and 11 services:")
code("mvn -B clean package -DskipTests\ndocker compose up -d --build\ndocker compose ps")
step("Step 5:", "Wait 1–2 minutes until every service has registered, then check the addresses below. Flyway "
     "creates all database tables on the first start.")
LOCAL = [
    ["http://localhost:18080", "API gateway – the only entry point of the REST API (/actuator/health returns UP)"],
    ["http://localhost:18080/swagger-ui/index.html", "Swagger UI of every service (select a definition)"],
    ["http://localhost:8761", "Eureka – 11 registered services"],
    ["http://localhost:15672", "RabbitMQ management"],
    ["localhost:15432 · localhost:15433", "PostgreSQL (business data) · PostgreSQL + pgvector (assistant)"],
]
table(["Address", "Description"], LOCAL, [3700, 5350], "Local back-end addresses", "2.2", mono_cols=(0,))
figure("png/i02-swagger-ui.png", "Swagger UI of the back-end API (iot-service definition)", "2.2")
step("Step 6 (optional):", "Load the sample data (this wipes business data, so only on a developer machine):")
code("Get-Content scripts\\seed-local-complete.sql -Raw | docker exec -i ll-ms-postgres psql -U postgres -v ON_ERROR_STOP=1")
step("Step 7:", "After changing the code of one service, rebuild and restart only that service, e.g.:")
code("mvn -B clean package -DskipTests -pl order-service -am\ndocker compose up -d --build order-service")

# ---- 2.2.4 admin web from source
H(4, "2.2.4 Admin web and landing page (developers)")
step("Step 1:", "Install Node.js 24 and clone the repository:")
code("git clone https://github.com/LockR-Tech/frontend.git\ncd frontend/fe\nnpm install")
step("Step 2:", "By default the admin web calls the production API https://api.locker-drone.tech. To use the "
     "local back-end, create `frontend/fe/.env` with `VITE_API_BASE_URL=http://localhost:18080`.")
step("Step 3:", "Start the development server and open http://localhost:3000; build the production bundle with "
     "`npm run build`:")
code("npm run dev")
step("Step 4:", "The landing page is a separate project: `cd ../landingPage`, `npm install`, `npm run dev` → "
     "http://localhost:5173.")

# ---- 2.2.5 mobile from source
H(4, "2.2.5 Mobile app (developers)")
step("Step 1:", "Install Flutter 3.44.9 and Android Studio. In Android Studio open “Device Manager” and create an "
     "Android emulator, or connect a phone with USB debugging (Bluetooth open needs a real phone).")
step("Step 2:", "Clone the repository and get the packages:")
code("git clone https://github.com/LockR-Tech/mobile.git\ncd mobile\nflutter pub get")
step("Step 3:", "Copy `.env.example` to `.env`. `API_BASE_URL` points to the production API; for the local "
     "back-end use `http://10.0.2.2:18080` on the Android emulator. After every change of `.env`, regenerate the "
     "configuration class:")
code("dart run build_runner build --delete-conflicting-outputs")
step("Step 4:", "Run the app on the emulator or phone, or build an installable APK:")
code("flutter run -d emulator-5554\nflutter build apk --release")

# ---- 2.2.6 locker controller + kiosk
H(4, "2.2.6 Locker controller and kiosk (Raspberry Pi)")
P("Each cabinet has one Raspberry Pi that drives the lock relays, reads the door sensors, moves the sliding lid, "
  "talks to the back-end over MQTT, accepts signed Bluetooth open codes and shows the kiosk on the touch screen. "
  "The wiring is described in docs/03-hardware/controller-wiring-guide.md.")
step("Step 1:", "Write **Raspberry Pi OS (64-bit)** to the microSD card with Raspberry Pi Imager; in the "
     "customisation step set the hostname (e.g. `lockr-tu01`), a user with password, Wi-Fi and enable SSH.")
step("Step 2:", "Install the runtime and the controller code:")
code("sudo apt update && sudo apt full-upgrade -y\nsudo apt install -y postgresql\n"
     "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs\n"
     "curl -LsSf https://astral.sh/uv/install.sh | sh\n"
     "git clone https://github.com/LockR-Tech/iot.git ~/iot && cd ~/iot && uv sync\n"
     "sudo -u postgres createdb iot_locker")
step("Step 3:", "Create `~/iot/.env` (not committed): `HARDWARE_BACKEND=gpio`, the relay / door / lid pins "
     "(`GPIO_RELAY_PINS`, `GPIO_DOOR_PINS`, `LID_*`), the MQTT broker (`MQTT_BROKER`, `MQTT_TRANSPORT`, "
     "`MQTT_USERNAME`, `MQTT_PASSWORD`) and the local database (`POSTGRES_*`).")
step("Step 4:", "Run the controller as a systemd service `lockr-controller` (`ExecStart=uv run python main.py`, "
     "restart on failure, all relays forced off when it stops), then follow its log until “System is READY”:")
code("sudo systemctl enable --now lockr-controller\njournalctl -u lockr-controller -f")
step("Step 5:", "Check every box, door sensor and the lid with `uv run python debug_gpio.py` (pins, doors, open n, "
     "lid) or the technician panel `/service` of the controller.")
step("Step 6:", "Build the kiosk: set `VITE_LOCKER_ID` and `VITE_LOCKER_CODE` of the cabinet in `ui/.env.local`, "
     "then `cd ~/iot/ui && npm ci && npm run build`; the service `lockr-kiosk` serves it on port 3002 and Chromium "
     "opens it full screen at login.")
step("Step 7:", "On the admin web open “Tủ” (Lockers) → the cabinet → “Bộ điều khiển tủ” (Cabinet controller), "
     "choose the Pi by its MAC address and click “Gán vào tủ” (Assign); with “Mở thử lần lượt từng ô” (test-open "
     "each box) ticked every door opens once and the cabinet shows Ready.")
step("Step 8 (optional):", "Enable automatic updates: `sudo bash ~/iot/scripts/install-pi-auto-update.sh` installs a "
     "timer that pulls `main` every 5 minutes, rebuilds the kiosk and restarts the controller when the code changes.")
P("Without a Raspberry Pi, `uv run python simulate_demo_cabinet.py` simulates cabinets on MQTT so that the whole "
  "open-box flow can be tested from the app and the kiosk (`cd iot/ui && npm run dev` → http://localhost:3002).")

# ---- 2.2.7 CI/CD
H(4, "2.2.7 Continuous deployment to production")
P("Production is updated only by GitHub Actions; nobody edits the server by hand. A merge to `main` triggers:")
CD = [
    ["backend", "Deploy to Azure VM", "mvn verify (build + tests) → package → copy to the VM over SSH → keep the "
     "running release as .previous → docker compose up → wait for Eureka and the gateway → automatic rollback if "
     "unhealthy → acceptance checks through https://api.locker-drone.tech"],
    ["backend", "Backend CI · Backend Security", "Unit tests on every pull request; CodeQL, dependency review, SBOM "
     "and Trivy image scan"],
    ["frontend", "Deploy to Cloudflare Workers", "Build and publish the admin web and the landing page"],
    ["mobile", "Build APK · Deploy mobile web", "Build a signed APK and publish a GitHub Release "
     "apk-<version>-<build> (LockR-latest.apk); publish the mobile web build"],
    ["iot", "Pi auto-update timer", "Every 5 minutes the Pi pulls `main`, rebuilds the kiosk and restarts the "
     "controller when needed"],
]
table(["Repository", "Pipeline", "What it does"], CD, [1500, 2600, 4950], "Deployment pipelines", "2.2")
figure("png/i03-github-actions-deploy.png", "Back-end deployment runs on GitHub Actions", "2.2")
page_break()

# ------------------------------------------------------------------------------------------------ II.3
H(2, "3. User Manual")
H(3, "3.1 Overview")
P("**Lock.R** is a smart locker system with drone delivery. Customers send parcels to receivers through "
  "self-service lockers, rent a box by the hour to keep their belongings, or book a drone that picks a parcel up at "
  "home and flies it to the receiver’s locker. Boxes are opened with a 6-digit PIN on the kiosk screen of the "
  "cabinet, with the “Mở ô” (Open box) button of the app over Bluetooth, or with a QR code. Payment is a VietQR "
  "bank transfer confirmed automatically. Locker and drone technicians keep the cabinets and drones working, and "
  "the administrator manages the whole system on the admin web.")
figure("rp3/srs-assets/drawio/01-context-diagram.png", "Context diagram of the Lock.R system", "3.1")
ROLES = [
    ["Customer", "Mobile app, kiosk", "Rent a box, send a parcel, book a drone delivery, pay by VietQR, open boxes, "
     "report a faulty box, request a refund, earn points, ask the AI assistant"],
    ["Receiver", "Kiosk (no account needed), mobile app", "Pick up a parcel with the PIN / QR code received by app, "
     "email or SMS"],
    ["Locker Technician", "Mobile app", "Shifts, incident tickets of assigned lockers, periodic inspections, emergency "
     "open, IoT devices, recovery of dropped drone parcels"],
    ["Drone Technician", "Mobile app", "Home pickup, drone dispatch, loading and launch, drone fleet status, drone "
     "tickets and inspections"],
    ["Administrator", "Admin web", "Dashboard and revenue, accounts, stores / lockers / boxes, drones, orders, refunds, "
     "promotions, business settings, maintenance schedules, knowledge base"],
    ["Locker Controller", "Raspberry Pi in the cabinet", "Executes open / lid commands, reports door states and "
     "heartbeats, verifies Bluetooth open codes"],
]
table(["Role", "Application", "Main functions"], ROLES, [2000, 2200, 4850], "Roles and applications", "3.1")
P("The user manual follows the four main workflows of the system:")

WFS = []
for n in range(1, 5):
    p = os.path.join(ASSETS, "data", f"wf{n}.json")
    WFS.append(json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None)

SUMMARY = [
    ("Workflow 1: Drone Delivery with Home Pickup", [
        "The customer books a drone delivery in the app: pickup address, receiver locker, parcel and receiver; the "
        "system checks distance, weight and weather, then the customer pays by VietQR.",
        "The nearest drone technician on shift accepts the pickup, collects the parcel at the sender’s home with "
        "the pickup code and confirms it.",
        "The technician assigns an idle drone, confirms the loading (weight, seal code, checklist) and launches.",
        "The drone flies to the receiver locker; the cabinet opens its roof lid, the parcel is released into a "
        "drone box and the receiver gets a PIN.",
        "The receiver opens the box at the kiosk; the order is completed and the administrator follows it on the "
        "admin web."]),
    ("Workflow 2: Rent a Box or Send a Parcel via Locker", [
        "The customer chooses a locker and a box in the app (or on the kiosk), rents it by the hour or creates a "
        "send order with the receiver’s contact, and pays by VietQR.",
        "The customer opens the box with the PIN on the kiosk or with the “Open box” button (Bluetooth), puts the "
        "items in and closes the door.",
        "For a send order the receiver gets the pickup code and opens the box at the kiosk; for a rental the "
        "customer can reopen, extend and finally end the rental.",
        "An overdue rental opens only after the overtime fee is paid; the administrator sees the payments in the "
        "revenue report."]),
    ("Workflow 3: Box Incident to Resolution", [
        "The customer reports a faulty box with a description and photos in the app.",
        "The locker technician in charge claims the ticket, inspects the box and records the progress with photos.",
        "The technician resolves the ticket (fix on site, move the items, lock the box) with an after-repair photo, "
        "or rejects it with feedback; the customer follows the progress and rates the work.",
        "The administrator monitors tickets, SLA and technicians on the admin web."]),
    ("Workflow 4: Maintenance of Lockers and Drones", [
        "The administrator creates an inspection schedule with a checklist for a locker or a drone and assigns a "
        "technician.",
        "When the schedule is due the technician is notified, inspects every item and submits the result with "
        "photos.",
        "A failed item opens a repair ticket automatically; the drone technician also keeps the drone fleet status, "
        "battery and maintenance log up to date.",
        "The administrator follows schedules, tickets and devices on the admin web."]),
]
for title, items in SUMMARY:
    sub(title)
    for k, it in enumerate(items, 1):
        para(run(f"{k}.\t") + rich(it), jc="both",
             extra='<w:tabs><w:tab w:val="left" w:pos="360"/></w:tabs><w:spacing w:before="20" w:after="20"/>'
                   '<w:ind w:left="360" w:hanging="360"/>')

# ------------------------------------------------------------------------------------------------ workflows
for n, wf in enumerate(WFS, 1):
    sec = f"3.{n + 1}"
    if n > 1 or True:
        page_break()
    if wf is None:
        H(3, f"{sec} Workflow {n}")
        P("[Content pending]")
        continue
    H(3, f"{sec} Workflow {n}: {wf['title']}")
    P(wf["purpose"])
    sub("Actors")
    for a in wf.get("actors", []):
        bullet(a)
    diagrams = wf.get("diagrams") or ([wf["diagram"]] if wf.get("diagram") else [])
    for dg in diagrams:
        figure(dg["path"], dg["caption"], sec, max_h=4.6)
    for part in wf["parts"]:
        sub(part["heading"])
        for k, st in enumerate(part["steps"], 1):
            step(f"Step {k}:", st["text"])
            if st.get("images"):
                figure(st["images"], st.get("caption") or "Screen", sec)

# ================================================================================================ package
zin = zipfile.ZipFile(TEMPLATE)
doc = zin.read("word/document.xml").decode("utf-8")
b0 = doc.index("<w:body>") + len("<w:body>")
b1 = doc.rindex("<w:sectPr")
head, inner, tail = doc[:b0], doc[b0:b1], doc[b1:]
cover = inner[:inner.index("<w:sdt>")]
cover = re.sub(r"Hanoi, August 2019", "Ho Chi Minh City, November 2026", cover)
assert "Ho Chi Minh City" in cover
tail = re.sub(r"(<w:sectPr[^>]*>)", r'\1<w:footerReference w:type="default" r:id="rIdUgFooter"/>', tail, count=1)
new_doc = head + cover + "".join(body) + tail

rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
rels = rels.replace("</Relationships>", "".join(
    f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
    f'Target="media/{os.path.basename(nm)}"/>' for nm, _, rid in media)
    + '<Relationship Id="rIdUgFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" '
      'Target="footer1.xml"/></Relationships>')
ct = zin.read("[Content_Types].xml").decode("utf-8")
for ext, mime in (("png", "image/png"), ("jpg", "image/jpeg")):
    if f'Extension="{ext}"' not in ct:
        ct = ct.replace("</Types>", f'<Default Extension="{ext}" ContentType="{mime}"/></Types>')
ct = ct.replace("</Types>", '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-'
                            'officedocument.wordprocessingml.footer+xml"/></Types>')
styles = zin.read("word/styles.xml").decode("utf-8")
CAP = ('<w:style w:type="paragraph" w:customStyle="1" w:styleId="{id}"><w:name w:val="{id}"/><w:basedOn w:val="Normal"/>'
       '<w:next w:val="Normal"/><w:qFormat/><w:pPr>{ppr}<w:spacing w:before="60" w:after="160"/>{jc}</w:pPr>'
       '<w:rPr><w:i/><w:color w:val="595959"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>')
styles = styles.replace("</w:styles>", CAP.format(id="TableCaption", ppr="<w:keepNext/>", jc="")
                        + CAP.format(id="FigureCaption", ppr="", jc='<w:jc w:val="center"/>') + "</w:styles>")
FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
          '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>'
          '<w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')

from xml.etree import ElementTree as ET  # noqa: E402
for x in (new_doc, styles, rels, ct):
    ET.fromstring(x.encode("utf-8"))

zout = zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = {"word/document.xml": new_doc, "word/_rels/document.xml.rels": rels, "[Content_Types].xml": ct,
            "word/styles.xml": styles}.get(it.filename)
    zout.writestr(it, data if data is not None else zin.read(it.filename))
zout.writestr("word/footer1.xml", FOOTER)
for nm, data, _ in media:
    zout.writestr(nm, data)
zout.close()
print(f"images {len(media)}, figures {sum(fig_count.values())}, tables {sum(tab_count.values())}, "
      f"workflows {sum(1 for w in WFS if w)} -> {OUTPUT}")
