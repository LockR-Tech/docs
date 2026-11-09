"""Registration form version 2.0 for FA26SE002 – the signed form (17/08/2026) with only the changes in BM03:
(a) research part removed, (b) AI report summaries removed, (c) non-functional requirements updated,
(d) parcel pickup methods stated as built (PIN at the kiosk; Bluetooth or locker QR scan in the app).

Run: uv run --no-project --with python-docx python build_registration.py
Source: ../FA26SE002_DRONE_DELIVERY_AND_SMART_LOCKER_MANAGEME_ducdnm2.docx (never modified).
"""
import copy
import os

import docx

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT_DIR, '..', 'FA26SE002_DRONE_DELIVERY_AND_SMART_LOCKER_MANAGEME_ducdnm2.docx')
OUT = os.path.join(OUT_DIR, 'FA26SE002_Registration_v2.0.docx')

B = '-\t'  # list items in the form are typed as "-<tab>text"

DELETE = [
    B + 'Battery-aware drone assignment strategy.',
    B + 'Generate summaries of operational reports.',
    'Research Outputs',
    B + 'Experimental evaluation report on drone assignment strategies.',
    B + 'Conference paper manuscript prepared for submission.',
    B + 'Experimental evaluation of drone assignment strategies.',
    B + 'Conference paper preparation',
    'a. Research Problem / Research Question:',
    'To what extent can a Battery-aware Drone Assignment strategy',
    B + 'Design and implement a Battery-aware Drone Assignment strategy.',
    B + 'Evaluate delivery performance under different assignment strategies.',
    B + 'Experimental Evaluation.',
    B + 'Comparative Performance Analysis.',
    'd. Expected Scientific Contribution:',
    B + 'Development of a Battery-aware Drone Assignment strategy',
    B + 'Creation of a Drone Simulator framework for delivery research.',
    B + 'Experimental comparison of drone assignment strategies.',
    B + 'Contribution to research in drone logistics',
]

REPLACE = {
    B + 'Implement Battery-aware Drone Assignment.':
        B + 'Assign to each delivery an idle drone whose battery is above the admin-set minimum and that is '
            'not under maintenance.',
    B + 'API response time below 300 ms for 95% of requests.':
        B + '95% of read API requests under 1 s and write requests under 2 s at 100 concurrent sessions.',
    B + 'Real-time update latency below 2 seconds.':
        B + 'Order status and drone stage updates reach the app within 2 s (95th percentile).',
    B + 'Stable telemetry updates every 3–5 seconds.':
        B + 'Box open result shown within 5 s in 95% of opens.',
    B + 'System availability greater than 95% during testing.':
        B + 'Monthly API uptime of at least 99%.',
    'Phase 3: Advanced Features and Evaluation': 'Phase 3: Advanced Features',
    '3.3. Research Information': '3.3. Objectives, Scope & Methodology',
    'b. Research Objectives:': 'a. Objectives:',
    B + 'Build a Drone Simulator Service for experimentation.':
        B + 'Build a Drone Simulator Service for demonstration and testing.',
    'c. Research Scope & Methodology:': 'b. Scope & Methodology:',
    'Research Methodology': 'Methodology',
    B + 'Smart Locker management and parcel collection using PIN/QR authentication.':
        B + 'Smart Locker management and parcel collection using a PIN at the kiosk, or from the mobile app '
            'over Bluetooth or after scanning the locker QR code.',
    B + 'Generate PIN and QR codes for parcel pickup.':
        B + 'Generate a PIN for parcel pickup; open the box from the mobile app over Bluetooth or after '
            'scanning the locker QR code.',
    'The rapid growth of e-commerce has significantly increased':
        'The rapid growth of e-commerce has significantly increased the demand for fast, efficient, and '
        'contactless last-mile delivery services. Smart Locker systems have been widely deployed in '
        'residential areas, universities, and commercial centers, providing a practical infrastructure for '
        'parcel pickup and delivery. However, most existing drone delivery solutions focus primarily on '
        'flight control, routing algorithms, or simulation environments without offering an integrated '
        'platform that combines delivery management, drone fleet management, incident reporting, maintenance '
        'management, real-time monitoring, and Smart Locker operations.',
    'This project aims to develop an integrated Drone Delivery and Smart Locker Management System':
        'This project aims to develop an integrated Drone Delivery and Smart Locker Management System '
        '(DDSLMS) based on the Hub-to-Smart Locker delivery model. The system supports autonomous delivery '
        'operations, real-time monitoring, incident reporting, maintenance management, and AI-assisted '
        'operational support, providing a complete software solution for smart logistics applications.',
    'Module 3: Maintenance Management': 'Module 4: Maintenance Management',
    'Module 4: AI Knowledge Support': 'Module 5: AI Knowledge Support',
}

INSERT_AFTER = {
    B + 'Monthly API uptime of at least 99%.': B + 'Replayed payment webhooks are never counted twice.',
    B + 'Secure access to operational and maintenance data.':
        B + 'A box is locked after 5 wrong PIN entries; Bluetooth open tokens are single-use.',
    B + 'Smart Locker management and parcel collection using a PIN at the kiosk, or from the mobile app over Bluetooth or after scanning the locker QR code.':
        B + 'Incident reporting and resolution management.',
    B + 'Real-time tracking and monitoring.': B + 'Incident Reporting and Management Module.',
}

INSERT_BEFORE = {
    B + 'Maintenance Management.': B + 'Incident Reporting and Management.',
}

INCIDENT_MODULE_TITLE = 'Module 3: Incident Reporting and Management'
INCIDENT_MODULE_ITEMS = [
    B + 'Submit locker compartment and delivery incident reports with photo evidence.',
    B + 'Assign and track incident tickets with SLA deadlines for technicians.',
    B + 'Hold affected locker compartments from new orders until inspection and resolution.',
    B + 'Notify customers and technicians of incident status and resolution updates.',
]

VERSION_NOTE = ('Version 2.0 (08/11/2026): research part removed (Battery-aware drone assignment, comparison of '
                'assignment strategies, experimental evaluation report, conference paper); AI summaries of '
                'operational reports removed; Incident Reporting and Management module added; non-functional '
                'requirements updated; parcel pickup methods stated as built (PIN at the kiosk; Bluetooth or '
                'locker QR scan in the app). Details: Record of Changes (BM03).')


def set_text(p, text):
    """Replace the paragraph text, keeping the formatting of its first run."""
    first = p.runs[0]
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    first.text = text


def matches(p, key):
    return p.text.strip().startswith(key.strip())


d = docx.Document(SRC)
done = set()
for p in list(d.paragraphs):
    for key in DELETE:
        if matches(p, key):
            p._p.getparent().remove(p._p)
            done.add(key)
            break
    else:
        for key, new in REPLACE.items():
            if matches(p, key):
                set_text(p, new)
                done.add(key)
                break

for p in list(d.paragraphs):
    for key, new in INSERT_AFTER.items():
        if matches(p, key):
            clone = copy.deepcopy(p._p)
            p._p.addnext(clone)
            set_text(docx.text.paragraph.Paragraph(clone, p._parent), new)
            done.add(key)
    for key, new in INSERT_BEFORE.items():
        if matches(p, key):
            clone = copy.deepcopy(p._p)
            p._p.addprevious(clone)
            set_text(docx.text.paragraph.Paragraph(clone, p._parent), new)
            done.add(key)

# Insert Module 3: Incident Reporting and Management before Module 4: Maintenance Management
for idx, p in enumerate(list(d.paragraphs)):
    if matches(p, 'Module 4: Maintenance Management'):
        bullet_tmpl = d.paragraphs[idx - 1]._p
        heading_clone = copy.deepcopy(p._p)
        p._p.addprevious(heading_clone)
        set_text(docx.text.paragraph.Paragraph(heading_clone, p._parent), INCIDENT_MODULE_TITLE)
        for item in INCIDENT_MODULE_ITEMS:
            item_clone = copy.deepcopy(bullet_tmpl)
            p._p.addprevious(item_clone)
            set_text(docx.text.paragraph.Paragraph(item_clone, p._parent), item)
        break

dots = [p for p in d.paragraphs if p.text.strip().startswith('.....')]
set_text(dots[0], VERSION_NOTE)
for p in dots[1:]:
    p._p.getparent().remove(p._p)

missing = [k for k in list(DELETE) + list(REPLACE) + list(INSERT_AFTER) + list(INSERT_BEFORE) if k not in done]
assert not missing, f'not found in the form: {missing}'
d.save(OUT)
print('saved', OUT, '| deleted', len(DELETE), '| replaced', len(REPLACE), '| inserted', len(INSERT_AFTER) + len(INSERT_BEFORE))
