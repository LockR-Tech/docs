"""Fill form BM03 (Registration Form – Record of Changes) for FA26SE002.

Run: uv run --no-project --with python-docx python build_bm03.py
"""
import os

import docx

from formfill import fill_column, fill_table, keep_rows_together, rebrand_sep490, remove_grey_guidance, set_widths

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT_DIR, 'bieu-mau', 'SWP490_R2_BM03_Record_of_Changes_1.docx')
OUT = os.path.join(OUT_DIR, 'SEP490_FA26SE002_R2_RecordOfChanges.docx')

PROJECT = [
    'FA26SE002 (group GFA26SE32)',
    'Drone Delivery and Smart Locker Management System (DDSLMS) – '
    'Hệ thống quản lý giao nhận hàng bằng Drone và Smart Locker (product name: Lock.R)',
    'Lê Thị Yến Vi (SE182544, leader) · Trương Nguyễn Thái Bình (SE182370) · '
    'Nguyễn Quốc Bảo Huy (SE180211) · Trần Kim Nhã (SE182290)',
    'Đặng Ngọc Minh Đức · Đỗ Hữu Tiến',
    '1.0 – registration form signed 17/08/2026',
    '2.0',
    '1.0',
    '09/11/2026',
]

ITER1 = 'Findings from Iteration 1: '

# No. | Section | Current content | Proposed content | Reason | Proposed by
# Only these changes are made in the registration form (build_registration.py). Other differences between
# the form and the system are recorded in BM02 and the Design Brief, not here.
RESEARCH_REASON = (ITER1 + 'the pilot has one real drone (DRONE-S550-07), so comparing drone assignment '
                   'strategies gives no meaningful result. Effort moved to real hardware integration (cabinet '
                   'CAB-TU01, drone camera, servo parcel release) and to a named technician being responsible '
                   'for every flight (Design Brief D4). Only the research scope is reduced; the delivery '
                   'workflow and its business rules are unchanged.')

CHANGES = [
    ['1', '3.2 b) Proposed Solutions; 3.2 c) Module 1',
     'Capability "Battery-aware drone assignment strategy"; FR "Implement Battery-aware Drone Assignment".',
     'Capability removed. FR: "Assign to each delivery an idle drone whose battery is above the admin-set '
     'minimum and that is not under maintenance."',
     RESEARCH_REASON, 'Team'],
    ['2', '3.2 f) Products; 3.2 g) Proposed Tasks',
     'Software Products (5 separate module items); Research Outputs (experimental evaluation report, '
     'conference paper); Phase 3 "Experimental evaluation of drone assignment strategies"; Phase 4 '
     '"Conference paper preparation".',
     'Software Products updated to 3 applications ("Drone Delivery and Smart Locker Management Web '
     'Application", "Mobile Application For Customer & Technicians", "Kiosk Screen Web Application"); '
     'Hardware Products added ("Drone and Smart Locker System"); Research Outputs removed; Phase 3 renamed '
     '"Advanced Features".',
     'Same as No. 1; deliverables restated to match the actual web, mobile, kiosk software and physical '
     'drone/locker hardware built in Iteration 1.', 'Team'],
    ['3', '3.3 Research Information',
     'Research question; research objectives on assignment strategies; methodology "Experimental '
     'Evaluation", "Comparative Performance Analysis"; expected scientific contribution.',
     'Section renamed "Objectives, Scope & Methodology". Removed the research question, the assignment-'
     'strategy objectives, the two experimental methods and the scientific contribution. Kept the general '
     'objective, In/Out of Scope and the remaining methods; the simulator objective now reads "for '
     'demonstration and testing".',
     'Same as No. 1.', 'Team'],
    ['4', '3.2 c) Module 5 AI Knowledge Support',
     'Generate summaries of operational reports.',
     'Removed. Document-based question answering with cited sources (RAG) is kept.',
     'Not aligned with the project scope: the assistant answers operational questions from the knowledge base '
     'with cited sources, and operational figures are already shown on the admin dashboard and revenue '
     'reports (UC24).', 'Team'],
    ['5', '3.2 d) Non-Functional Requirements',
     'p95 API response < 300 ms; real-time update < 2 s; telemetry every 3–5 s; availability > 95 % during '
     'testing; JWT; RBAC; secure access.',
     'p95 read <= 1 s / write <= 2 s at 100 sessions; status and drone stage updates <= 2 s (p95); box open '
     'result <= 5 s in 95 % of opens; monthly uptime >= 99 %; replayed payment webhooks never counted twice; '
     'box locked after 5 wrong PINs and single-use Bluetooth tokens. JWT, RBAC, secure access and '
     'scalability kept. Same as Design Brief §7 N1–N6.',
     'Constraint from technology: thresholds set to what can be measured on the deployed VM (2 vCPU, '
     '8 GB RAM, SRS §4.2.3) and kept identical to Design Brief §7.', 'Team'],
    ['6', '3.2 b) Proposed Solutions; 3.2 c) Module 2',
     '"Smart Locker management and parcel collection using PIN/QR authentication"; "Generate PIN and QR '
     'codes for parcel pickup".',
     '"… parcel collection using a PIN at the kiosk, or from the mobile app over Bluetooth or after scanning '
     'the locker QR code"; "Generate a PIN for parcel pickup; open the box from the mobile app over Bluetooth '
     'or after scanning the locker QR code".',
     ITER1 + 'the kiosk accepts a typed PIN only. QR is used the other way round: the app scans the QR '
     'sticker on the locker and opens the box over the Internet, or opens it over Bluetooth with a single-use '
     'token checked on the Pi (Design Brief D2). No device scans the order QR shown in the app.', 'Team'],
    ['7', '3.2 b) Proposed Solutions; 3.2 c) Module 3 & Module 4; 3.2 g) Phase 3; 3.3 b) In Scope',
     'Modules 1–4 only (Delivery Management, Smart Locker Management, Maintenance Management, AI Knowledge '
     'Support); incident reporting not listed as a separate module; smart locker installation not listed '
     'under Maintenance Management.',
     'Added "Module 3: Incident Reporting and Management" before Maintenance Management (renumbered to '
     'Module 4, with "Installation of a smart locker system" added; AI Knowledge Support renumbered to '
     'Module 5), and added "Incident Reporting and Management" and "Real-Time Monitoring Dashboard" in '
     'Proposed Solutions, Phase 3 and In Scope.',
     ITER1 + 'incident reporting and resolution (box incidents with SLA tickets and dropped-parcel recovery) '
     'is one of the four core workflows owned and demonstrated by the team (WF-03, Design Brief §8 and '
     'Appendix A1), and smart locker installation & commissioning is supported for technicians and admins.', 'Team'],
]

d = docx.Document(SRC)
rebrand_sep490(d)
t = d.tables
fill_column(t[0], PROJECT)
fill_table(t[1], CHANGES)
fill_table(t[2], [[c[0], '', ''] for c in CHANGES])
set_widths(t[1], [0.9, 2.4, 3.4, 4.4, 4.2, 1.7])
remove_grey_guidance(d)
keep_rows_together(d)
for row in t[2].rows[:-1]:  # the reviewers' decision table stays on one page
    for cell in row.cells:
        for para in cell.paragraphs:
            para.paragraph_format.keep_with_next = True
d.save(OUT)
print('saved', OUT, '| changes', len(CHANGES))

