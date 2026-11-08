"""Fill form BM01 (Design Brief – Review 2) for Lock.R.

Run: uv run --no-project --with python-docx python build_brief.py
Placeholders the team must still fill are highlighted yellow.
"""
import copy
import os

import docx
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.shared import Cm, RGBColor

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT_DIR, 'bieu-mau', 'SWP490_R2_BM01_Design_Brief_1.docx')
OUT = os.path.join(OUT_DIR, 'SWP490_LockR_R2_DesignBrief.docx')

TODO = object()  # marker: the next text part is a placeholder (yellow)
BODY = RGBColor(0x1F, 0x29, 0x37)

# ---------------------------------------------------------------- content
HEADER = [
    [TODO, '[Project code from the registration form]'],
    'Lock.R – Smart Locker System with Drone Delivery',
    'Nguyễn Quốc Bảo Huy (SE180211, leader) · Trương Nguyễn Thái Bình (SE182370) · '
    'Lê Thị Yến Vi (SE182544) · Trần Kim Nhã (SE182290)',
    'Đặng Ngọc Minh Đức (DucDNM) · Đỗ Hữu Tiến (TienDH)',
    ['https://github.com/LockR-Tech (backend, frontend, mobile, iot, docs) – ',
     TODO, 'tag review-2 to be created on all five repos'],
    '1.0',
    '08/11/2026',
]

REG_CHANGES = [
    [[TODO, '[Section]'], [TODO, '[Current text]'], [TODO, '[Proposed text]'],
     [TODO, '[Reason – details in BM03, or "No changes"]']],
]

OUT_OF_SCOPE = [
    ['Beyond-visual-line-of-sight commercial drone flights',
     'Needs aviation permits; demo flights run in a controlled area with one drone.'],
    ['Payment gateways other than SePay VietQR (MoMo, VNPay, cards)',
     'One reconciled payment path; VietQR works with every Vietnamese bank app (BR-22).'],
    ['Publishing on Google Play / App Store', 'Pilot ships as an Android APK and mobile web.'],
    ['More than one physical cabinet',
     'One real cabinet (CAB-TU01, 7 boxes); other lockers run the same controller software simulated.'],
]

GLANCE = (
    'Lock.R lets people send and store parcels without meeting in person. A customer books a box in a '
    'smart locker in the mobile app, pays by VietQR bank transfer and drops the parcel; the receiver opens '
    'the box with a 6-digit PIN or QR at the kiosk or over Bluetooth from the phone. '
    'Boxes can be rented by the hour, and parcels can travel between lockers by drone. '
    'Users are customers and receivers (mobile app, mobile web, kiosk), locker and drone technicians '
    '(mobile app) and administrators (admin web). Each locker is a Raspberry Pi that drives relays, door '
    'sensors and a sliding landing lid and talks to the backend over MQTT; the backend is a set of Spring '
    'Boot microservices behind an API gateway, with an AI assistant. Core value: 24/7 contact-free '
    'hand-over in which every box state and payment is traceable. Architecture: SDD Figure 1.1.'
)

DECISIONS = [
    ['D1', 'Backend structure', 'Monolith; microservices',
     'Microservices: 10 Spring Boot services, one database each (Flyway), gateway with JWT and roles, '
     'RabbitMQ events; members work per domain and failures stay local.',
     'Huy', 'SDD Fig. 1.1'],
    ['D2', 'Locker control and box opening', 'Arduino/RS485; vendor controller; Pi on GPIO',
     "Pi 5 on GPIO with a versioned MQTT contract (ACL per device, resend outbox). Orders change only on "
     "the cabinet's report; Bluetooth tokens (Ed25519, 120 s, single use) are checked offline on the Pi.",
     'Huy', 'UC17, UC35; BR-09, BR-25'],
    ['D3', 'Payment method', 'MoMo / VNPay; wallet; SePay VietQR',
     'SePay VietQR only: PAID only when the webhook amount covers the total; duplicate webhooks ignored; '
     'no merchant contract, works with every bank app.',
     'Bình', 'UC08; BR-02, BR-22'],
    ['D4', 'Drone delivery orchestration', 'Auto nearest-drone dispatch; technician accepts offer',
     'Technician accepts, completes a loading checklist and launches; one delivery state machine fed by '
     'MQTT telemetry; a person is responsible for every flight.',
     'Vi', 'UC10, UC32; BR-10, BR-11'],
    ['D5', 'Box incident handling', 'Complaint to admin; box FAULT at once; ticket with SLA',
     'Report puts the box in PENDING_CHECK; a technician on shift claims a ticket (SLA 4 h, max 2 '
     'extensions); the scheduler escalates. No box is locked on a false report.',
     'Nhã', 'UC13, UC28; BR-19, BR-24'],
]

RISKS = [
    ['R1', 'Cabinet reports a wrong door state (sensor misread, door stays shut)',
     'Box shown empty while holding a parcel; false JAMMED',
     '20 opens per box on CAB-TU01 with sensor log; hourly box/order reconciliation; emergency open',
     'Huy'],
    ['R2', 'Real drone flight cannot be shown reliably (weather, battery, permits)',
     'Drone workflow not shown end to end',
     'Weather check blocks bookings; indoor mode lands on the lid by ArUco with the same events; '
     'recorded flight as backup',
     'Vi'],
    ['R3', 'External services throttle or delay (Firebase SMS, SePay webhook)',
     'Sign-in fails or orders stay UNPAID in the demo',
     'Firebase test numbers, email OTP fallback; payment polling; service check script before demos',
     'Bình'],
]

GAPS = [
    ['G1', 'SRS keeps the customer wallet; the app removed it (SePay only)',
     'SRS UC08, UC12, §3.2.24–26, BR-16', 'Remove wallet from SRS', 'Bình', '15/11/2026'],
    ['G2', "Opening an order's box over Bluetooth (QR/OTP fallback) is built but not specified",
     'SRS UC16; SDD §3; backend #137', 'Add use case, rule, sequence diagram', 'Huy', '15/11/2026'],
    ['G3', 'State machines and activity diagrams are not yet in Report 3/4',
     'docs/diagrams/src, srs-assets/drawio', 'Insert 4 + 4 diagrams', 'Nhã', '15/11/2026'],
    ['G4', 'No separate staging; demo seed script is outside the repo',
     'Report 4; seed script', 'Declare staging, move script to repo', 'Huy', '22/11/2026'],
    ['G5', 'Report 5 test cases not written; automated tests not mapped to TC IDs',
     'Report 5; test suites', 'Write Report 5 with §6 TC IDs', 'Nhã', '22/11/2026'],
    ['G6', [TODO, '[High findings Kept / Planned in BM02]'], 'BM02', '', '', ''],
]

FEATURES = [
    ['F-01', 'Sign in, admin 2FA', 'User, Admin',
     'Wrong password: MSG06, no token; admin needs a 6-digit email OTP valid 300 s.', 'Done'],
    ['F-02', 'Create send order', 'Customer',
     'Only AVAILABLE boxes of an online locker; box RESERVED; unpaid after 15 min: cancelled, box freed.',
     'Done'],
    ['F-03', 'VietQR payment', 'Customer',
     'PAID only when received >= total; a duplicate webhook counts once; partial shows the remainder.',
     'Done'],
    ['F-04', 'Drop parcel, share code', 'Customer',
     'Box opens only if PAID; drop gives STORING / OCCUPIED and a 6-digit PIN to the receiver.', 'Done'],
    ['F-05', 'Pick up at kiosk', 'Receiver',
     'Right PIN/QR opens and completes the order; 5 wrong PINs lock the box 15 min (MSG22).', 'Done'],
    ['F-06', 'Rent box by hours', 'Customer',
     '1–720 h; multi-use PIN until the end; extension <= 24 h; ending frees the box.', 'Done'],
    ['F-07', 'Open box by Bluetooth', 'Customer, Receiver',
     "Token for the order's owner/receiver only, 120 s, single use; state changes once on the Pi report; "
     'failure offers QR/OTP.', 'In progress'],
    ['F-08', 'Overdue fee, expiry', 'Customer, Scheduler',
     '500 VND/h, max 50,000 VND and 50 % of price; opens only after paying; > 72 h: EXPIRED.', 'Done'],
    ['F-09', 'Cabinet commands', 'Locker Controller',
     'No ack in 20 s: TIMEOUT, never success; relay ran but door closed: JAMMED; events resent.', 'Done'],
    ['F-10', 'Book drone delivery', 'Customer',
     'Refused: no free DRONE box (MSG13), > 5,000 g, > 5,000 m, unsafe weather or > 3 open orders.',
     'Done'],
    ['F-11', 'Dispatch, load, launch', 'Drone Technician',
     'Accept only with an idle drone >= 20 % battery; launch needs the checklist; + 50 g re-prices.',
     'In progress'],
    ['F-12', 'Track drone, pickup ready', 'Customer, Receiver',
     'Stage updates reach the app in 2 s; on arrival the lid opens and the order is STORING with a PIN.',
     'In progress'],
    ['F-13', 'Report box incident', 'Customer',
     'Title and 1–5 photos required; box PENDING_CHECK, no new orders, overdue fee stops.', 'Done'],
    ['F-14', 'Ticket within SLA', 'Locker Tech., Admin',
     'Claim only on shift; SLA 4 h, max 2 extensions with reason; 3 overdue tickets block claims.', 'Done'],
    ['F-15', 'Parcel drop and recovery', 'Drone/Locker Tech., Admin',
     'Camera evidence required; recovery SLA 4 h; 60 % compensation needs admin and customer approval.',
     'In progress'],
    ['F-16', 'AI assistant', 'User',
     'Answers cite sources; order questions see only own orders; reply within 10 s.', 'Done'],
]

NFRS = [
    ['N1', 'Performance', 'p95 API response time', 'Read <= 1 s, write <= 2 s at 100 sessions',
     'k6 on staging, 10 min'],
    ['N2', 'Responsiveness', 'PIN / "Open box" to door-open result',
     '<= 5 s in 95 % of 50 opens', 'Timed run on CAB-TU01 + logs'],
    ['N3', 'Realtime', 'Order status / drone stage delay to app', 'p95 <= 2 s',
     'Event vs receive time, 30 events'],
    ['N4', 'Payment accuracy', 'Double-counted replayed webhooks', '0 of 100', 'Replay test in CI'],
    ['N5', 'Security', 'PIN lockout; Bluetooth token reuse',
     'Lock after 5 wrong PINs; 100 % reused tokens rejected', 'Automated tests in CI'],
    ['N6', 'Availability', 'Monthly API uptime', '>= 99 %', 'Health check every 5 min'],
]

OWNERS = [
    ['Nguyễn Quốc Bảo Huy', 'Leader; backend, IoT, DevOps',
     '1) Architecture, gateway/auth, CI/CD, VM; 2) Locker controller, MQTT, Bluetooth open; '
     '3) AI assistant',
     'WF-02', 'D1, D2; iot-service, iot repo'],
    ['Trương Nguyễn Thái Bình', 'Mobile – customer, payment',
     '1) Send / rent / order screens; 2) SePay VietQR payment; 3) Profile, notifications',
     'WF-01', 'D3; payment-service, mobile'],
    ['Lê Thị Yến Vi', 'Drone delivery, admin reports',
     '1) Drone booking and tracking; 2) Admin dashboard, revenue; 3) Loyalty',
     'WF-03', 'D4; order-service (drone)'],
    ['Trần Kim Nhã', 'Maintenance, incidents, QA',
     '1) Locker tickets, SLA, inspections; 2) Parcel drop recovery; 3) Test cases, CI tests',
     'WF-04', 'D5; locker-service'],
]

WORKFLOWS = [
    ['WF-01', 'Send parcel via locker, receiver picks up', 'Customer, Receiver, Locker Controller',
     'Customer creates a SEND order', 'Parcel handed over; order COMPLETED',
     'F-01–F-05, F-09, F-16',
     'Order INITIALIZED → STORING → COMPLETED; Box AVAILABLE → RESERVED → OCCUPIED → AVAILABLE', 'Bình'],
    ['WF-02', 'Rent a box by hours', 'Customer, Locker Controller, System Scheduler',
     'Customer rents a box', 'Rental ended, or EXPIRED after the overdue fee',
     'F-03, F-06–F-09',
     'Order INITIALIZED → STORING → COMPLETED / EXPIRED; Box RESERVED → OCCUPIED → AVAILABLE', 'Huy'],
    ['WF-03', 'Drone delivery between lockers', 'Customer, Drone Technician, Receiver, Locker Controller',
     'Customer books a drone delivery', 'Parcel in the receiver locker and picked up',
     'F-03, F-05, F-10–F-12, F-15',
     'Order AWAITING_DISPATCH → STORING → COMPLETED; Stage ACCEPTED → … → READY_FOR_PICKUP; '
     'Drone IDLE → RESERVED → IN_FLIGHT → IDLE', 'Vi'],
    ['WF-04', 'Box incident to repair', 'Customer, Locker Technician, Admin',
     'Customer reports a faulty box', 'Box back in service or locked',
     'F-13, F-14',
     'Box → PENDING_CHECK → FAULT → AVAILABLE; Ticket OPEN → IN_PROGRESS → RESOLVED / REJECTED', 'Nhã'],
]

DEMOS = [
    ['DS-01', 'WF-01', 'Main', 'CAB-TU01 has a free Standard box; customer account; receiver phone',
     'Create order → pay by VietQR → open box and drop → receiver enters PIN at kiosk',
     'Order COMPLETED, box AVAILABLE', 'Bình'],
    ['DS-02', 'WF-01', 'Exception', 'Order DS-01 in STORING',
     'Enter a wrong PIN 5 times at the kiosk', 'Box locked 15 min (MSG22); order stays STORING', 'Bình'],
    ['DS-03', 'WF-02', 'Main', 'Customer near CAB-TU01 with Bluetooth on',
     'Rent 2 h → pay → "Open box" (Bluetooth) → reopen → end rental',
     'Box opens over Bluetooth; order COMPLETED, box AVAILABLE', 'Huy'],
    ['DS-04', 'WF-02', 'Exception', 'Bluetooth off; a second rental past its end time',
     'Tap "Open box" → choose OTP at kiosk; open the overdue rental',
     'App offers QR/OTP; overdue box opens only after the fee is paid', 'Huy'],
    ['DS-05', 'WF-03', 'Main', 'Two lockers with landing pads; idle drone >= 20 % battery; safe weather',
     'Book → pay → technician accepts, loads, launches → arrival → receiver picks up',
     'Lid opens; order STORING with PIN, then COMPLETED', 'Vi'],
    ['DS-06', 'WF-03', 'Exception', 'Receiver locker with no free drone box; parcel of 6,000 g',
     'Book a drone delivery', 'Booking refused (MSG13 / weight limit)', 'Vi'],
    ['DS-07', 'WF-04', 'Main', 'Occupied box; locker technician on shift',
     'Customer reports with a photo → technician claims → resolves',
     'Box PENDING_CHECK → back in service; ticket RESOLVED', 'Nhã'],
    ['DS-08', 'WF-04', 'Exception', 'Ticket already extended twice; technician with 3 overdue tickets',
     'Extend the SLA a third time; claim a new ticket', 'Both refused with a message', 'Nhã'],
]

# state transitions committed: Order 10, Box 18, Drone delivery stage 12, Ticket 4
TEST_TARGET = [
    ['16', '3', '48'],
    ['4', '1', '4'],
    ['44', '1', '44'],
    ['6', '1', '6'],
    ['', '', '102'],
]

# column widths (cm), page text width = 17 cm
WIDTHS = {
    3: [0.9, 2.4, 3.0, 7.0, 1.2, 2.5],      # decisions
    4: [0.9, 4.0, 3.4, 7.3, 1.4],            # risks
    5: [0.9, 5.0, 3.6, 3.7, 1.2, 2.6],      # gaps
    6: [1.1, 2.9, 2.4, 6.6, 2.3, 1.7],      # features
    9: [1.2, 2.4, 2.4, 2.0, 2.4, 1.9, 3.6, 1.1],  # workflows
    10: [1.2, 1.4, 1.6, 3.2, 3.4, 3.2, 3.0],  # demos
    7: [0.9, 2.5, 4.0, 4.9, 4.7],            # NFRs
    8: [3.6, 3.1, 6.2, 1.5, 2.6],            # ownership
}


# ---------------------------------------------------------------- helpers
def write_runs(paragraph, value, template_run):
    """Write value (str or list with TODO markers) into paragraph, cloning template_run formatting."""
    parts = value if isinstance(value, list) else [value]
    for r in list(paragraph.runs):
        r._r.getparent().remove(r._r)
    yellow = False
    for part in parts:
        if part is TODO:
            yellow = True
            continue
        paragraph._p.append(copy.deepcopy(template_run))
        run = paragraph.runs[-1]
        run.text = part
        run.font.italic = False
        run.font.color.rgb = BODY
        if yellow:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
        yellow = False


def run_template(cell):
    p = cell.paragraphs[0]
    r = p.runs[0] if p.runs else p.add_run('')
    return copy.deepcopy(r._r)


def set_cell(cell, value, tmpl):
    for extra in cell.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    write_runs(cell.paragraphs[0], value, tmpl)


def fill_table(table, rows, first_col=0, start_row=1):
    """Write rows starting at start_row, adding rows (copies of the last) as needed."""
    tmpl = run_template(table.rows[start_row].cells[-1])
    needed = start_row + len(rows)
    while len(table.rows) < needed:
        table._tbl.append(copy.deepcopy(table.rows[-1]._tr))
    while len(table.rows) > needed:
        table._tbl.remove(table.rows[-1]._tr)
    for i, values in enumerate(rows):
        cells = table.rows[start_row + i].cells
        for j, v in enumerate(values):
            set_cell(cells[first_col + j], v, tmpl)


def set_widths(table, widths_cm):
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn('w:gridCol')), widths_cm):
        gc.set(qn('w:w'), str(int(Cm(w).twips)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths_cm):
            cell.width = Cm(w)


# ---------------------------------------------------------------- build
d = docx.Document(SRC)
t = d.tables

tmpl = run_template(t[0].rows[0].cells[1])
for row, value in zip(t[0].rows, HEADER):
    set_cell(row.cells[1], value, tmpl)

fill_table(t[1], REG_CHANGES)
fill_table(t[2], OUT_OF_SCOPE)
fill_table(t[3], DECISIONS)
fill_table(t[4], RISKS)
fill_table(t[5], GAPS)
fill_table(t[6], [[f[0], f[1], f[2], f[3], f'TC-F{f[0][2:]}-01..03', f[4]] for f in FEATURES])
fill_table(t[7], NFRS)
fill_table(t[8], OWNERS)
fill_table(t[9], WORKFLOWS)
fill_table(t[10], DEMOS)
fill_table(t[11], TEST_TARGET, first_col=1)
for idx, w in WIDTHS.items():
    set_widths(t[idx], w)

# Grey guidance: section 2 guidance becomes the body text, the rest is removed.
glance_done = False
for p in list(d.paragraphs):
    colors = {r.font.color.rgb for r in p.runs if r.font.color is not None and r.font.color.type is not None}
    if RGBColor(0x66, 0x66, 0x66) not in colors:
        continue
    if p.text.startswith('Maximum 150 words') and not glance_done:
        write_runs(p, GLANCE, copy.deepcopy(p.runs[0]._r))
        glance_done = True
    else:
        p._p.getparent().remove(p._p)

# Rows never split across pages; heading + header row + first row stay together.
for table in t:
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        if trPr.find(qn('w:cantSplit')) is None:
            trPr.append(trPr.makeelement(qn('w:cantSplit'), {}))
        if i == 0:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.keep_with_next = True

# Headings that would otherwise be stranded at a page bottom start a new page.
for para in d.paragraphs:
    if para.text.strip() in ('3. Key Design Decisions', '7. Non-Functional Requirements'):
        para.paragraph_format.page_break_before = True

os.makedirs(OUT_DIR, exist_ok=True)
d.save(OUT)
print('saved', OUT, '| glance words', len(GLANCE.split()))
