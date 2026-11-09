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

from formfill import FULL_NAME, MEMBER_ORDER, TEAM_LINE

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT_DIR, 'bieu-mau', 'SWP490_R2_BM01_Design_Brief_1.docx')
OUT = os.path.join(OUT_DIR, 'SEP490_FA26SE002_R2_DesignBrief.docx')

TODO = object()  # marker: the next text part is a placeholder (yellow)
BODY = RGBColor(0x1F, 0x29, 0x37)

# ---------------------------------------------------------------- content
HEADER = [
    'FA26SE002 (group GFA26SE32)',
    'Drone Delivery and Smart Locker Management System (DDSLMS) – product name Lock.R',
    TEAM_LINE,
    'Đặng Ngọc Minh Đức (DucDNM) · Đỗ Hữu Tiến (TienDH)',
    'https://github.com/LockR-Tech (backend, frontend, mobile, iot, docs) – tag review-2',
    '1.0',
    '09/11/2026',
]

REG_CHANGES = [
    ['3.2 b–c, f–g; 3.3 Research', 'Battery-aware assignment, strategy comparison, research outputs',
     'Removed; idle drone above minimum battery; Software & Hardware Products',
     'Iteration 1: one real drone (BM03 No. 1–3)'],
    ['3.2 c) Module 5', 'AI summaries of operational reports', 'Removed', 'BM03 No. 4'],
    ['3.2 d) NFR', 'p95 < 300 ms, availability > 95 %, telemetry 3–5 s', 'N1–N6 (§7)', 'BM03 No. 5'],
    ['3.2 b), c) Module 2', 'Parcel collection by PIN/QR; generate PIN and QR codes',
     'PIN at kiosk; app opens via Bluetooth or locker QR', 'BM03 No. 6'],
    ['3.2 b–c, g; 3.3 b)', 'Modules 1–4 without a separate incident module',
     'Added Module 3: Incident Reporting before Maintenance (Modules 4–5)', 'BM03 No. 7'],
]

OUT_OF_SCOPE = [
    ['Beyond-visual-line-of-sight commercial drone flights',
     'Needs aviation permits; demo flights run in a controlled area with one drone.'],
    ['Payment gateways other than SePay VietQR (MoMo, VNPay, cards)',
     'One reconciled payment path; VietQR works with every Vietnamese bank app (BR-21).'],
    ['Publishing on Google Play / App Store', 'Pilot ships as an Android APK and mobile web.'],
    ['Battery-aware drone assignment research and strategy comparison',
     'Removed from the registration (BM03 No. 1–3): one real drone gives no meaningful comparison.'],
    ['Physical drone flight control', 'The drone Pi only reads autopilot telemetry and drives the '
     'release servo; it never arms or steers the drone.'],
    ['More than one physical cabinet',
     'One real cabinet (CAB-TU01, 7 boxes); other lockers run the same controller software simulated.'],
]

GLANCE = (
    'Lock.R lets people send and store parcels without meeting in person. A customer rents a locker box or '
    'books a drone delivery in the mobile app and pays by VietQR; for a drone delivery the nearest '
    "technician on shift collects the parcel at home and the drone drops it into the receiver locker's drone "
    'box. Boxes open with a 6-digit PIN at the kiosk, or from the phone over Bluetooth or by scanning the '
    'locker QR. Users are customers and receivers (mobile app, mobile web, kiosk), locker and drone '
    'technicians handling incidents and maintenance (mobile app), and administrators assigning work and '
    'following revenue (admin web). Each locker is a Raspberry Pi driving relays, door sensors and the '
    'drone-box lid over MQTT; Spring Boot microservices sit behind an API gateway, with an AI assistant. '
    'Core value: 24/7 contact-free hand-over with every box state and payment traceable. '
    'Architecture: SDD Figure 1.1.'
)

DECISIONS = [
    ['D1', 'Backend structure', 'Monolith; microservices',
     'Microservices: 10 Spring Boot services, one database each (Flyway), gateway with JWT and roles, '
     'RabbitMQ events; members work per domain and failures stay local.',
     'Huy', 'SDD Fig. 1.1'],
    ['D2', 'Locker control and box opening', 'Arduino/RS485; vendor controller; Pi on GPIO',
     "Pi 5 on GPIO with a versioned MQTT contract (ACL per device, resend outbox). Orders change only on "
     "the cabinet's report; Bluetooth tokens (Ed25519, 120 s, single use) are checked offline on the Pi.",
     'Huy', 'UC16, UC34; BR-09, BR-24'],
    ['D3', 'Payment method', 'MoMo / VNPay; wallet; SePay VietQR',
     'SePay VietQR only: PAID only when the webhook amount covers the total; duplicate webhooks ignored; '
     'no merchant contract, works with every bank app.',
     'Bình', 'UC08; BR-02, BR-21'],
    ['D4', 'Drone delivery orchestration', 'Auto nearest-drone dispatch; technician accepts offer',
     'The nearest free technician on shift collects the parcel at home, picks an idle drone, completes the '
     'loading checklist and launches; one delivery state machine fed by MQTT telemetry; a person answers '
     'for every flight.',
     'Vi', 'UC10, UC31; BR-10, BR-11'],
    ['D5', 'Incident and maintenance tickets', 'Complaint to admin; box FAULT at once; ticket with SLA',
     'Reports, failed inspections and drone faults become tickets; a customer report sets the box '
     'PENDING_CHECK, not FAULT; only a technician on shift claims (SLA 4 h, max 2 extensions); the '
     'scheduler escalates.',
     'Nhã', 'UC12, UC27; BR-18, BR-23'],
]

RISKS = [
    ['R1', 'Cabinet reports a wrong door state (sensor misread, door stays shut)',
     'Box shown empty while holding a parcel; false JAMMED',
     '20 opens per box on CAB-TU01 with sensor log; hourly box/order reconciliation; emergency open',
     'Huy'],
    ['R2', 'Real drone flight cannot be shown reliably (weather, battery, permits)',
     'Drone workflow not shown end to end',
     'Weather check blocks bookings; without flight the drone Pi reads the locker ArUco marker, the lid '
     'opens, the servo releases and the lid closes with the same events; recorded flight as backup',
     'Vi'],
    ['R3', 'External services throttle or delay (Firebase SMS, SePay webhook)',
     'Sign-in fails or orders stay UNPAID in the demo',
     'Firebase test numbers, email OTP fallback; payment polling; service check script before demos',
     'Bình'],
]

GAPS = [
    ['G1', 'Seven tables and ten columns added since 29/10 missing from Logical ERD (SR-10, SR-11)',
     'rp3/srs-assets/drawio/05*', 'Regenerate Logical ERD', 'Bình', '15/11/2026'],
    ['G2', 'Opening an order box via Bluetooth (fallback: locker QR or PIN) is built, not in SRS',
     'SRS UC15; SDD §3; backend #137', 'Add use case, rule, sequence diagram', 'Huy', '15/11/2026'],
    ['G3', 'State machines and activity diagrams not yet in Report 3/4; 06c lacks pickup',
     'docs/diagrams/src, srs-assets/drawio', 'Insert 5 + 5 diagrams; redraw 06c', 'Vi', '15/11/2026'],
    ['G4', 'Report 4 declares no environments; Azure VM (api.locker-drone.tech) is staging',
     'Report 4; backend scripts/seed-*.sql', 'Declare VM as staging with seed/rollback', 'Huy', '15/11/2026'],
    ['G5', 'Report 5 written; CI tests not mapped to §6 TC IDs and iot has no CI (BM02 SR-20)',
     'Report 5; test suites', 'Map CI tests to §6 TC IDs; add iot CI', 'Nhã', '22/11/2026'],
    ['G6', 'SRS FRs have no testable acceptance criteria (BM02 SR-08; SR-13, SR-17 = G3; SR-01 fixed)',
     'SRS §3.2–3.6', 'Add acceptance criteria per FR from §6', 'Nhã', '22/11/2026'],
    ['G7', 'Inspection activity 06g covers lockers only; drone schedules are built',
     'srs-assets/drawio/06g', 'Add the drone path to 06g', 'Bình', '15/11/2026'],
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
     'Right PIN opens and completes the order; 5 wrong PINs lock the box 15 min (MSG21).', 'Done'],
    ['F-06', 'Rent box by hours', 'Customer',
     '1–720 h; multi-use PIN until the end; extension <= 24 h; ending frees the box.', 'Done'],
    ['F-07', 'Open box by Bluetooth', 'Customer, Receiver',
     'Owner/receiver token only, 120 s, single use; state changes on Pi report; fallback: QR or PIN.', 'Done'],
    ['F-08', 'Overdue fee, expiry', 'Customer, Scheduler',
     '500 VND/h, max 50,000 VND and 50 % of price; opens only after paying; > 72 h: EXPIRED.', 'Done'],
    ['F-09', 'Cabinet commands', 'Locker Controller',
     'No ack in 20 s: TIMEOUT, never success; relay ran but door closed: JAMMED; events resent.', 'Done'],
    ['F-10', 'Book drone delivery', 'Customer',
     'Refused: no free DRONE box (MSG13), > 5,000 g, > 5,000 m, unsafe weather or > 3 open orders.',
     'Done'],
    ['F-11', 'Assign drone, load, launch', 'Drone Technician',
     'Only an idle drone > 20 % battery is assigned; launch needs the checklist; + 50 g re-prices.',
     'Done'],
    ['F-12', 'Track drone, drop into locker', 'Customer, Receiver',
     'Stage updates in 2 s; on arrival lid opens, servo releases, lid closes; STORING with PIN.', 'Done'],
    ['F-13', 'Report box incident', 'Customer',
     'Title and description required, <= 5 photos; box PENDING_CHECK, no new orders, fee stops.',
     'Done'],
    ['F-14', 'Ticket within SLA', 'Locker Tech., Admin',
     'Claim only on shift; SLA 4 h, max 2 extensions with reason; 3 overdue tickets block claims.', 'Done'],
    ['F-15', 'Parcel drop and recovery', 'Drone/Locker Tech., Admin',
     'Camera evidence required; recovery SLA 4 h; 60 % compensation needs admin and customer approval.',
     'In progress'],
    ['F-16', 'AI assistant', 'User',
     'Answers cite sources; order questions see only own orders; reply within 10 s.', 'Done'],
    ['F-17', 'Home pickup by technician', 'Drone Tech., Admin',
     'Nearest free technician on shift; 180 s timeout: next one; pickup needs sender code within 300 m.', 'Done'],
    ['F-18', 'Maintenance schedule', 'Admin',
     'One locker or drone; matching technician role; drone schedule sets MAINTENANCE until inspected.', 'Done'],
    ['F-19', 'Inspection checklist', 'Locker / Drone Tech.',
     'Assigned technician only; items Pass/Fail/NA; all pass: next due date; fail opens ticket, FAULT.', 'Done'],
    ['F-20', 'Dashboard, revenue report', 'Admin',
     'Revenue = payments collected minus refunds in the period; each total opens the entries behind it.',
     'Done'],
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

# Parts follow git authorship on origin/main and balance 5 features + 1 workflow per member across the team.
OWNERS = [
    ['Nguyễn Quốc Bảo Huy', 'Backend, IoT, DevOps',
     '1) Architecture, gateway/auth, CI/CD, VM; 2) Locker controller, kiosk, MQTT, Bluetooth open; '
     '3) AI assistant and knowledge base',
     'WF-02', 'D1, D2; auth, iot, assistant services; iot repo'],
    ['Trương Nguyễn Thái Bình', 'Mobile – customer, payment, incidents',
     '1) Incident report and technician ticket screens; 2) SePay VietQR payment; '
     '3) Send / rent / my-orders screens, rental rules',
     'WF-03', 'D3; payment-service, mobile'],
    ['Lê Thị Yến Vi', 'Leader; drone delivery',
     '1) Drone booking, dispatch, home pickup; 2) Drone telemetry, drone Pi (ArUco, servo); '
     '3) Dashboard, revenue, drone screens',
     'WF-01', 'D4; order-service (drone), drone-iot'],
    ['Trần Kim Nhã', 'Drone fleet, maintenance',
     '1) Drone units, devices, logs, tickets; 2) Maintenance schedules, inspections, '
     'shifts; 3) Parcel drop, overdue and expiry',
     'WF-04', 'D5; locker-service (drone), order-service'],
]

# The four flows the team demos (06/11/2026): drone delivery, locker rental, incident report, maintenance.
# Statistics and reports are feature F-20, shown at the end of DS-01a and DS-02a.
WORKFLOWS = [
    ['WF-01', 'Drone delivery with home pickup', 'Customer, Drone Technician, Receiver, Locker Controller',
     'Customer books a drone delivery', 'Parcel dropped into the receiver locker and picked up',
     'F-03, F-05, F-10–F-12, F-15, F-17, F-20',
     'Order AWAITING_DISPATCH → STORING → COMPLETED; Stage AWAITING_DISPATCH → PICKUP_ASSIGNED → PICKED_UP '
     '→ … → READY_FOR_PICKUP; Drone IDLE → RESERVED → IN_FLIGHT → IDLE', 'Vi'],
    ['WF-02', 'Rent a box or send a parcel via locker', 'Customer, Receiver, Locker Controller, System Scheduler',
     'Customer rents a box or creates a send order', 'Items collected and box released, or EXPIRED after '
     'the overdue fee', 'F-01–F-09, F-16, F-20',
     'Order INITIALIZED → STORING → COMPLETED / EXPIRED; Box AVAILABLE → RESERVED → OCCUPIED → AVAILABLE',
     'Huy'],
    ['WF-03', 'Box incident to resolution', 'Customer, Locker Technician, Admin',
     'Customer reports a faulty box', 'Ticket RESOLVED with the box back in service or locked, or REJECTED '
     'with feedback', 'F-13, F-14',
     'Box AVAILABLE / OCCUPIED → PENDING_CHECK → previous (rejected) or FAULT → previous (resolved); Ticket '
     'OPEN → IN_PROGRESS → RESOLVED / REJECTED',
     'Bình'],
    ['WF-04', 'Maintenance of lockers and drones', 'Admin, Locker / Drone Technician',
     'Admin creates a maintenance schedule or a drone ticket and assigns a technician',
     'Inspection recorded; asset back in service, or a repair ticket opened', 'F-14, F-18, F-19',
     'Drone IDLE → MAINTENANCE → IDLE / FAULT → IDLE; Box AVAILABLE → FAULT → AVAILABLE; Ticket OPEN → '
     'IN_PROGRESS → RESOLVED', 'Nhã'],
]

DEMOS = [
    ['DS-01a', 'WF-01', 'Main',
     'Receiver locker CAB-TU01 has a free drone box; idle drone > 20 % battery; technician on shift; safe '
     'weather',
     'Book with home pickup → pay → nearest technician accepts, collects at home (code, photo), loads, '
     'launches → ArUco read, lid opens, servo releases, lid closes → receiver enters PIN → admin opens '
     'revenue',
     'Order STORING with PIN, then COMPLETED; log shows servo release; payment in revenue', 'Vi'],
    ['DS-01b', 'WF-01', 'Exception', 'Receiver locker with no free drone box; parcel of 6,000 g',
     'Book a drone delivery', 'Booking refused (MSG13 / weight limit)', 'Vi'],
    ['DS-02a', 'WF-02', 'Main', 'CAB-TU01 has a free Standard box; customer near it with Bluetooth on',
     'Choose a box, rent 2 h → pay by VietQR → PIN issued → open with PIN at kiosk, close → reopen with '
     '"Open box" (Bluetooth) → end rental → admin opens revenue',
     'Order COMPLETED, box AVAILABLE; payment in revenue', 'Huy'],
    ['DS-02b', 'WF-02', 'Exception', 'Rental DS-02a in STORING; a second rental past its end time',
     'Enter a wrong PIN 5 times at the kiosk; open the overdue rental',
     'Box locked 15 min (MSG21); overdue box opens only after the fee is paid', 'Huy'],
    ['DS-03a', 'WF-03', 'Main', 'Occupied box on CAB-TU01; locker technician on shift',
     'Customer reports with a photo → technician claims → inspects, fixes on site with a photo → resolves',
     'Box PENDING_CHECK → back in service; ticket RESOLVED; customer notified', 'Bình'],
    ['DS-03b', 'WF-03', 'Exception', 'Report on a box with no fault; technician X holds 3 overdue tickets',
     'X claims it; a technician on shift claims, rejects without, then with feedback',
     'Claim refused; reject needs feedback; ticket REJECTED, box back to its previous state', 'Bình'],
    ['DS-04a', 'WF-04', 'Main', 'Drone DRONE-S550-07 idle, no mission; drone technician account',
     'Admin creates a schedule with a checklist and assigns the technician → technician is notified, marks '
     'every item Pass with a photo',
     'Drone MAINTENANCE (no deliveries) until the inspection, then IDLE; next due date set', 'Nhã'],
    ['DS-04b', 'WF-04', 'Exception', 'Schedule for CAB-TU01 assigned to technician A',
     'Technician B completes it; A marks one item Fail on a box',
     'B refused (assigned technician only); ticket for A, box FAULT, due date kept', 'Nhã'],
]

# state transitions of the main entities, counted on the state machine diagrams (docs/rp3/srs-assets/drawio):
# Order 9 (06-1), Box 15 (06g), Drone delivery stage 18 (06c), Drone 11 (06i), Ticket 4 (06j) = 57
TEST_TARGET = [
    ['20', '3', '60'],
    ['4', '1', '4'],
    ['57', '1', '57'],
    ['6', '1', '6'],
    ['', '', '127'],
]

# column widths (cm), page text width = 17 cm
WIDTHS = {  # owner / presenter columns hold a member full name on two lines
    3: [0.9, 2.2, 2.6, 7.6, 2.0, 1.7],      # decisions
    4: [0.9, 4.0, 3.3, 6.8, 2.0],            # risks
    5: [0.9, 5.5, 3.3, 3.3, 2.2, 1.8],      # gaps
    6: [1.0, 2.6, 2.2, 7.4, 2.3, 1.5],      # features
    9: [1.2, 2.1, 2.2, 1.8, 2.1, 1.7, 3.2, 2.7],  # workflows
    10: [1.5, 1.4, 1.6, 3.1, 3.5, 3.2, 2.7],  # demos
    7: [0.9, 2.5, 4.0, 4.9, 4.7],            # NFRs
    8: [2.7, 3.0, 6.9, 1.6, 2.8],            # ownership
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
for p in d.paragraphs:
    for r in p.runs:
        if 'SWP490' in r.text:
            r.text = r.text.replace('SWP490', 'SEP490')
for sec in d.sections:
    for part in (sec.header, sec.footer):
        for p in part.paragraphs:
            for r in p.runs:
                if 'SWP490' in r.text:
                    r.text = r.text.replace('SWP490', 'SEP490')
t = d.tables

tmpl = run_template(t[0].rows[0].cells[1])
for row, value in zip(t[0].rows, HEADER):
    set_cell(row.cells[1], value, tmpl)

fill_table(t[1], REG_CHANGES)
fill_table(t[2], OUT_OF_SCOPE)
def by_name(rows, col):
    """Copy of rows with the member name in column col written as the member's full name."""
    return [r[:col] + [FULL_NAME[r[col]]] + r[col + 1:] for r in rows]


fill_table(t[3], by_name(DECISIONS, 4))
fill_table(t[4], by_name(RISKS, 4))
fill_table(t[5], by_name(GAPS, 4))
fill_table(t[6], [[f[0], f[1], f[2], f[3], f'TC-F{f[0][2:]}-01..03', f[4]] for f in FEATURES])
fill_table(t[7], NFRS)
fill_table(t[8], sorted(by_name(OWNERS, 0), key=lambda r: MEMBER_ORDER.index(r[0])))
fill_table(t[9], by_name(WORKFLOWS, 7))
fill_table(t[10], by_name(DEMOS, 6))
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
# Empty template lines left after the System at a Glance text (keeps sections 0–8 within 4 pages).
glance_p = next(p for p in d.paragraphs if p.text.startswith('Lock.R'))._p
while glance_p.getnext() is not None and glance_p.getnext().tag.endswith('}p') \
        and not ''.join(glance_p.getnext().itertext()).strip():
    glance_p.getparent().remove(glance_p.getnext())

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

# Headings stay on the same page as the table that follows them.
for para in d.paragraphs:
    if para.style.name.startswith('Heading'):
        para.paragraph_format.keep_with_next = True

os.makedirs(OUT_DIR, exist_ok=True)
d.save(OUT)
print('saved', OUT, '| glance words', len(GLANCE.split()))
