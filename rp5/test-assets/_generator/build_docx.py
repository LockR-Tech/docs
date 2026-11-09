"""Assemble Report5 Test Documentation: keep the template cover / styles, body in the structure of the
'V. Software Testing Documentation' chapter of the reference final report."""
import json
import os
import re
import struct
import sys
import zipfile
from xml.sax.saxutils import escape as xesc

TEMPLATE, DATA, ASSETS, OUTPUT = sys.argv[1:5]
D = json.load(open(DATA, encoding="utf-8"))
TW = 9050  # text width (dxa): A4 11906 - margins 1440 / 1416

body, media = [], []


def run(text, b=False, i=False, sz=None, color=None, font=None):
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
    return f'<w:r>{"<w:rPr>" + rp + "</w:rPr>" if rp else ""}<w:t xml:space="preserve">{xesc(text)}</w:t></w:r>'


def para(content, style=None, jc=None, extra=""):
    pp = (f'<w:pStyle w:val="{style}"/>' if style else "") + extra + (f'<w:jc w:val="{jc}"/>' if jc else "")
    body.append(f'<w:p>{"<w:pPr>" + pp + "</w:pPr>" if pp else ""}{content}</w:p>')


def H(level, text):
    para(run(text), f"Heading{level}")


def P(text, **kw):
    para(run(text, **kw), jc="both")


def page_break():
    body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')


def toc(instr, placeholder):
    body.append('<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>{run(placeholder, i=True, color="808080")}'
                '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')


def figure(png, caption):
    data = open(os.path.join(ASSETS, png), "rb").read()
    pw, ph = struct.unpack(">II", data[16:24])
    scale = min(6.2 / (pw / 96), 8.6 / (ph / 96))
    cx, cy = int(pw / 96 * scale * 914400), int(ph / 96 * scale * 914400)
    k = len(media) + 1
    rid = f"rIdTd{k}"
    media.append((f"word/media/td_{k}.png", data, rid))
    pic = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
           f'<wp:docPr id="{2000 + k}" name="Figure {k}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks '
           f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
           f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData '
           f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic '
           f'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{2000 + k}" '
           f'name="td_{k}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
           f'<a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/>'
           f'</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
           f'</wp:inline></w:drawing></w:r>')
    para(pic, jc="center", extra='<w:keepNext/><w:spacing w:before="120" w:after="60"/>')
    para(run(caption), "FigureCaption")


def table(headers, rows, widths, caption=None, center_cols=(), merge_first=False, header_rows=None):
    """Template table look: single borders, header fill FFE8E1, Arial 10. merge_first: vertically merge
    equal consecutive values of column 0 (feature groups)."""
    assert abs(sum(widths) - TW) < 5, (sum(widths), headers)
    if caption:
        para(run(caption), "TableCaption", extra="<w:keepNext/>")
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{TW}" w:type="dxa"/><w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for s in
                     ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/>'
             '<w:right w:w="80" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="04A0"/></w:tblPr>'
           + f"<w:tblGrid>{grid}</w:tblGrid>"]

    def cell(w, content, head=False, center=False, vmerge=None, span=1):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="FFE8E1"/>' if head else ""
        vm = "" if vmerge is None else ('<w:vMerge w:val="restart"/>' if vmerge == "restart" else "<w:vMerge/>")
        gs = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
        lines = content.split("\n") if content else [""]
        jc = '<w:jc w:val="center"/>' if head or center else ""
        ps = "".join(
            '<w:p><w:pPr><w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>'
            + jc + "</w:pPr>" + (run(x, b=head, sz=20, font="Arial") if x else "") + "</w:p>" for x in lines)
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{gs}{vm}{shd}<w:vAlign w:val="center"/></w:tcPr>{ps}</w:tc>'

    for hr in (header_rows or [[(h, 1, None) for h in headers]]):
        cells, ci = [], 0
        for text, span, vm in hr:
            w = sum(widths[ci:ci + span])
            cells.append(cell(w, text, True, vmerge=vm, span=span))
            ci += span
        out.append('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' + "".join(cells) + "</w:tr>")
    prev = None
    for r in rows:
        cs = []
        for k, (w, c) in enumerate(zip(widths, r)):
            vm = None
            if merge_first and k == 0:
                vm = "cont" if c == prev else "restart"
                c = "" if c == prev else c
            cs.append(cell(w, c, center=k in center_cols, vmerge=vm))
        prev = r[0] if merge_first else None
        out.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cs) + "</w:tr>")
    out.append("</w:tbl>")
    body.append("".join(out))
    para("", extra='<w:spacing w:after="60"/>')


# ====================================================================== content
SCOPE = [
    ("Authentication", "Sign Up", "Guest", "Ensure the guest can create a CUSTOMER account with valid information or by phone OTP, and the system shows an error for invalid inputs."),
    ("Authentication", "Sign In with Password", "All Roles", "Check that the user can sign in with email / phone and password and is taken to the home page of the account's role."),
    ("Authentication", "Sign In with Phone OTP or Google", "Guest, Customer", "Ensure the Firebase phone OTP and Google sign-in are verified on the server and wrong codes are rejected."),
    ("Authentication", "Sign In with Email OTP", "All Roles", "Ensure the 6-digit email OTP is accepted when correct and rejected when wrong or expired (300 s)."),
    ("Authentication", "Reset Password", "All Roles", "Test the password-reset flow: request the OTP by email, verify it and set a new password."),
    ("Authentication", "Admin Login with 2FA", "Admin", "Ensure the admin needs the password and the email OTP, and the session is closed after 5 wrong OTPs."),
    ("Authentication", "Log in to Kiosk by QR", "Customer", "Ensure the customer can scan the kiosk QR (valid 2 minutes) and confirm, and expired or reused sessions are refused."),
    ("Profile Management", "Update Profile", "All Roles", "Ensure all users can update their personal information and avatar."),
    ("Profile Management", "Change Password", "All Roles", "Verify a registered user can change the password and the other sessions are revoked."),
    ("Profile Management", "Delete Account", "Customer", "Ensure the account is deleted, its email / phone are released and it can no longer sign in."),
    ("Store & Locker Search", "Search Stores and Lockers", "Guest, Customer", "Ensure users can search stores and lockers on the list and the map with online status and free boxes."),
    ("Store & Locker Search", "View Locker Box Map", "Customer", "Check that the real box layout shows the state of every box and only free boxes can be booked."),
    ("Locker Send", "Send Parcel", "Customer", "Ensure the customer can create a SEND order with receiver, voucher and points, and the box is held until payment."),
    ("Locker Send", "Drop Parcel and Share Pickup Code", "Customer", "Ensure the sender can open the paid box, confirm the drop and share the pickup code; the receiver receives the code."),
    ("Locker Send", "Change PIN and Delegate Pickup", "Customer", "Ensure the sender can regenerate the PIN or delegate the pickup and the old PIN stops working."),
    ("Locker Send", "Pick Up Parcel at Kiosk", "Receiver", "Ensure the receiver opens the box with the PIN or QR, and the box is locked after 5 wrong attempts."),
    ("Locker Rental", "Rent Locker", "Customer", "Ensure the customer can rent a box by the hour, pay and reopen it with the rental PIN."),
    ("Locker Rental", "Extend and End Rental", "Customer", "Ensure the customer can extend a rental (only the difference is charged) and end it."),
    ("Locker Rental", "Pay Overdue Fee", "Customer, Receiver", "Ensure the box opens only after the overtime fee is paid and overdue orders expire after 72 hours."),
    ("Payment", "Pay by VietQR (SePay)", "Customer", "Ensure the order becomes PAID only when the SePay webhook confirms the full amount, and duplicated webhooks are ignored."),
    ("Payment", "Pay with Loyalty Points", "Customer", "Ensure point redemption follows the limits (at least 1,000 points, at most 50 % of the order) and the rest is paid by VietQR."),
    ("Payment", "Request Refund", "Customer", "Ensure the customer can request a refund within 7 days with a reason and follow its status."),
    ("Order Management", "View My Orders and Incoming Orders", "Customer, Receiver", "Ensure the customer and the receiver see only their own orders with status history and payments."),
    ("Order Management", "Rate Order and Send Complaint", "Customer", "Ensure the customer can rate a completed order once or send a complaint and receive the admin reply."),
    ("Promotion & Loyalty", "Save and Apply Vouchers", "Customer", "Ensure vouchers can be saved, applied with their scope and minimum amount, and exchanged for points."),
    ("Promotion & Loyalty", "Earn Loyalty Points", "Customer", "Ensure completed orders earn 10 % as points, tiers follow lifetime points and points are reversed on refund."),
    ("Incident Report", "Report Locker Incident", "Customer", "Ensure the customer can report a faulty box with title and photos and the box becomes PENDING_CHECK."),
    ("Drone Delivery", "Book Drone Delivery", "Customer", "Ensure booking checks the receiver locker, weight (<= 5,000 g), distance (<= 5 km), weather and calculates the fee by weight."),
    ("Drone Delivery", "Track Drone Delivery", "Customer, Receiver", "Ensure the customer sees every stage, the live position and can cancel only while awaiting dispatch."),
    ("Drone Delivery", "Drone Home Pickup", "Customer, Drone Technician", "Ensure the pickup is offered to the nearest technician on duty and fails with a refund when not served in time."),
    ("Drone Operation", "Dispatch and Confirm Loading", "Drone Technician", "Ensure the technician accepts an order with an idle drone (battery >= 20 %) and confirms weight, seal code and checklist."),
    ("Drone Operation", "Launch and Report Flight Failure", "Drone Technician", "Ensure launch respects flight hours and suspensions, and a failed flight puts the order in refund."),
    ("Drone Operation", "Manage Drone Fleet", "Drone Technician", "Ensure the technician can claim drones, change status with reason and update battery and maintenance notes."),
    ("Maintenance", "Manage Shift", "Locker Technician, Drone Technician", "Ensure only technicians on shift with location on receive tickets, offers and missions."),
    ("Maintenance", "Handle Incident Ticket", "Locker Technician", "Ensure the technician can claim, extend the SLA (max 2 x 24 h), return and resolve tickets with photos."),
    ("Maintenance", "Perform Periodic Inspection", "Locker Technician", "Ensure passing all items advances the due date and a failed item opens a ticket automatically."),
    ("Maintenance", "Emergency Open and IoT Devices", "Locker Technician", "Ensure the technician can open boxes, control the lid and restart controllers only of assigned lockers."),
    ("Administration", "View Dashboard and Revenue Report", "Admin", "Check that the dashboard and the revenue report use the money actually collected and refunds are deducted."),
    ("Administration", "Manage Accounts", "Admin", "Ensure the admin can search users, create staff, lock / unlock and delete accounts."),
    ("Administration", "Manage Stores, Lockers and Boxes", "Admin", "Test CRUD of stores, lockers and boxes, batch creation and that occupied boxes cannot be deleted."),
    ("Administration", "Manage Drones and Drop Incidents", "Admin", "Ensure the admin can register drones and decide free redelivery or compensation for dropped parcels."),
    ("Administration", "Process Refunds", "Admin", "Ensure the admin approves with a transfer receipt or rejects with a reason."),
    ("Administration", "Manage Promotions and Loyalty Rules", "Admin", "Ensure the admin can create promotions with period, usage limit, locker scope and point price."),
    ("Administration", "Configure Business Settings and Jobs", "Admin", "Ensure business rules can be changed without restart, are audited, and scheduled jobs can be run on demand."),
    ("Notification", "Receive Notifications", "All Roles", "Ensure push and in-app notifications are delivered in Vietnamese and only the owner can read or delete them."),
    ("AI Assistant", "Ask AI Assistant", "All Roles", "Ensure answers cite only documents the role may read and the asker's own orders, and off-topic questions are refused."),
    ("AI Assistant", "Manage Knowledge Base", "Admin", "Ensure uploaded documents are indexed with their allowed roles and the retrieval evaluation can be run."),
    ("IoT Locker", "Open Box via Bluetooth", "Customer", "Ensure only granted accounts get a one-time signed token valid for 120 s to open a box over Bluetooth."),
    ("IoT Locker", "Execute Cabinet Command", "Locker Controller", "Ensure the Pi executes open / lid / restart commands over MQTT and reports heartbeats, door states and results."),
]

TYPES = [
    ("Verify and validate each individual code unit (service methods, controllers, listeners) in isolation with mocked dependencies.",
     "Unit testing", "- All unit tests pass in CI on every pull request.\n- Every main service class of the backend is covered by tests."),
    ("Check the requests, responses and error codes exchanged through the REST API, the API gateway rules and the MQTT / STOMP message contracts.",
     "Interface testing", "- Requests and responses match the API contract (status codes, error codes, payload fields)."),
    ("Check correct interaction among services, the PostgreSQL databases, RabbitMQ events and the payment webhook.",
     "Integration testing", "- Data passed between services matches the expected schemas.\n- Repository queries pass on a real PostgreSQL database."),
    ("Test the five business flows end to end on the deployed system with the mobile app, kiosk, admin web, cabinet and drone.",
     "End-to-end testing", "- Every test case of the test report is executed in round 1.\n- No open defect blocks a business flow."),
    ("Check that the Raspberry Pi controller drives relays, door sensors and the sliding lid of the real cabinet correctly.",
     "Hardware testing", "- Every box of the cabinet opens on command and reports its door state."),
]

LEVELS = [("Unit testing", "X", "", "", ""), ("Interface testing", "X", "X", "", ""),
          ("Integration testing", "", "X", "", ""), ("End-to-end testing", "", "", "X", "X"),
          ("Hardware testing", "", "X", "X", "")]

TOOLS = [("Unit testing (backend)", "JUnit 5, Mockito, AssertJ", "Open Source", "JUnit 5.12.2, Mockito 5.17.0, AssertJ 3.27.7"),
         ("Integration testing (database)", "Testcontainers (PostgreSQL)", "Open Source", "1.21.4"),
         ("Build and test runner", "Apache Maven, GitHub Actions", "Open Source / GitHub", "Maven 3.9.10"),
         ("API testing", "Postman / Swagger UI (springdoc)", "Open Source", "Latest stable"),
         ("Mobile app testing", "flutter_test", "Google (Open Source)", "Flutter 3.44"),
         ("Cabinet hardware testing", "Pi service panel (/service)", "In-house", "1.0")]

HR = [("Nguyễn Quốc Bảo Huy", "Leader", "Plan the testing, assign test functions to members, review test cases and verify test results."),
      ("Trương Nguyễn Thái Bình", "Member", "Write and execute the test cases of accounts, locker send / rental, payment and admin web; prepare the test report."),
      ("Lê Thị Yến Vi", "Member", "Write and execute the test cases of drone delivery and drone operation; write unit tests and report defects."),
      ("Trần Kim Nhã", "Member", "Write and execute the test cases of technicians, kiosk, IoT devices and the cabinet controller; report defects.")]

ENV = [("Back-end server", "Azure virtual machine + Docker Compose", "Microsoft Azure", "Ubuntu 24.04"),
       ("Database", "PostgreSQL, pgvector", "PostgreSQL Global Development Group", "16"),
       ("Message broker", "RabbitMQ, Eclipse Mosquitto (MQTT)", "Broadcom, Eclipse Foundation", "RabbitMQ 3, Mosquitto 2"),
       ("Admin web testing", "Google Chrome", "Google", "Latest stable"),
       ("Mobile app testing", "Android phone", "Google", "Android 11 or later"),
       ("Locker cabinet testing", "Raspberry Pi 5 with kiosk touch screen", "Raspberry Pi Ltd", "Raspberry Pi OS (64-bit)"),
       ("Unit test execution", "Windows 11 PC, JDK", "Microsoft, Oracle", "Windows 11, JDK 21")]

dates = sorted(c["date"] for m in D["modules"] for c in m["cases"] if c["date"])


def fmt(oa):
    import datetime as dt
    return (dt.date(1899, 12, 30) + dt.timedelta(days=oa)).strftime("%d/%m/%Y")


MILESTONES = [("Unit test", "13/09/2026", fmt(D["run_date"])),
              ("Other Test Case (IT, ST, AT)", fmt(dates[0]), fmt(dates[-1]))]

# ====================================================================== body
para(run("Table of Contents"), "TOCHeading")
toc('TOC \\o "1-3" \\h \\z \\u', "Table of contents - right-click and choose Update Field.")
page_break()
para(run("List of Figures"), "TOCHeading")
toc('TOC \\h \\z \\t "FigureCaption,1"', "List of figures.")
para(run("List of Tables"), "TOCHeading")
toc('TOC \\h \\z \\t "TableCaption,1"', "List of tables.")
page_break()

H(1, "I. Record of Changes")
roc = [["09/11/2026", "A", "Trương Nguyễn Thái Bình (SE182370)",
        "Initial software test documentation: scope of testing, test strategy, test plan, unit test cases "
        f"({len(D['funcs'])} functions) and integration / system test cases ({len(D['modules'])} modules) with their statistics."]]
roc += [["", "", "", ""] for _ in range(4)]
table(["Date", "A*\nM, D", "In charge", "Change Description"], roc, [1300, 800, 2300, 4650], center_cols=(0, 1))
P("*A - Added M - Modified D - Deleted")
page_break()

H(1, "II. Testing Documentation")
H(2, "1. Scope of Testing")
table(["Feature", "Function", "Role", "Description"], [list(r) for r in SCOPE], [1700, 2100, 1550, 3700],
      "Table 1: Scope of Testing", merge_first=True)

H(2, "2. Test Strategy")
H(3, "2.1 Testing Types")
table(["Objective", "Technique", "Completion criteria"], [list(r) for r in TYPES], [3900, 1700, 3450],
      "Table 2.1: Testing Types")
H(3, "2.2 Test Levels")
w5 = [2650, 1600, 1600, 1600, 1600]
table(None, [list(r) for r in LEVELS], w5, "Table 2.2: Test Levels", center_cols=(1, 2, 3, 4),
      header_rows=[[("Type of Tests", 1, "restart"), ("Test Level", 4, None)],
                   [("", 1, "cont"), ("Unit", 1, None), ("Integration", 1, None), ("System", 1, None), ("Acceptance", 1, None)]])
H(3, "2.3 Supporting Tools")
table(["Purpose", "Tool", "Vendor/In-house", "Version"], [list(r) for r in TOOLS], [2300, 2600, 1900, 2250],
      "Table 2.3: Supporting Tools")

H(2, "3. Test Plan")
H(3, "3.1 Human Resources")
table(["Worker/Doer", "Role", "Specific Responsibilities/Comments"], [list(r) for r in HR], [2400, 1100, 5550],
      "Table 3.1: Human Resources", center_cols=(1,))
H(3, "3.2 Test Environment")
table(["Purpose", "Tool", "Provider", "Version"], [list(r) for r in ENV], [2100, 2950, 2100, 1900],
      "Table 3.2: Test Environment")
H(3, "3.3 Test Milestones")
table(["Milestone Task", "Start Date", "End Date"], [list(r) for r in MILESTONES], [4250, 2400, 2400],
      "Table 3.3: Test Milestones", center_cols=(1, 2))

H(2, "4. Test Cases")
para(run("Unit Test Cases: Report5_Unit Test_LockR.xls"), jc="both")
figure("unit_test_statistics.png", "Figure 4.1: Unit test case")
para(run("Test Cases and Test Reports: Report5_Test Report_LockR.xlsx"), jc="both")
figure("test_statistics.png", "Figure 4.2: Test Statistic")

# ====================================================================== package
zin = zipfile.ZipFile(TEMPLATE)
doc = zin.read("word/document.xml").decode("utf-8")
b0 = doc.index("<w:body>") + len("<w:body>")
b1 = doc.rindex("<w:sectPr")
head, inner, tail = doc[:b0], doc[b0:b1], doc[b1:]
cover = inner[:inner.index("<w:sdt>")]
cover = re.sub(r"Hanoi, August 2019", "Ho Chi Minh City, November 2026", cover)
assert "Ho Chi Minh City" in cover
new_doc = head + cover + "".join(body) + tail.replace(
    "<w:sectPr>", '<w:sectPr><w:footerReference w:type="default" r:id="rIdTdFooter"/>', 1)

rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
rels = rels.replace("</Relationships>", "".join(
    f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
    f'Target="media/{os.path.basename(n)}"/>' for n, _, rid in media)
    + '<Relationship Id="rIdTdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" '
      'Target="footer1.xml"/></Relationships>')
ct = zin.read("[Content_Types].xml").decode("utf-8")
if 'Extension="png"' not in ct:
    ct = ct.replace("<Types ", '<Types ', 1).replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>')
ct = ct.replace("</Types>", '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-'
                            'officedocument.wordprocessingml.footer+xml"/></Types>')
styles = zin.read("word/styles.xml").decode("utf-8")
CAP = ('<w:style w:type="paragraph" w:customStyle="1" w:styleId="{id}"><w:name w:val="{id}"/><w:basedOn w:val="Normal"/>'
       '<w:next w:val="Normal"/><w:qFormat/><w:pPr>{ppr}<w:spacing w:before="120" w:after="120"/>{jc}</w:pPr>'
       '<w:rPr><w:color w:val="666666"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>')
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
for n, data, _ in media:
    zout.writestr(n, data)
zout.close()
print("tables/figures written; scope rows", len(SCOPE), "->", OUTPUT)
