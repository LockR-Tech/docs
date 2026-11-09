"""Fill form BM02 (SRS/SDD Self-Review Report – Review 2) for FA26SE002.

Run: uv run --no-project --with python-docx python build_bm02.py

FINDINGS and TOP5 are the raw output of the standard prompt (do not edit them). The Team response column is
the team's confirmed decision at tag review-2.
"""
import os

import docx

from formfill import fill_column, fill_table, keep_rows_together, rebrand_sep490, remove_grey_guidance, set_widths

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT_DIR, 'bieu-mau', 'SWP490_R2_BM02_Self_Review_Report_1.docx')
OUT = os.path.join(OUT_DIR, 'SEP490_FA26SE002_R2_SelfReview.docx')

RUN_INFO = [
    'FA26SE002 (group GFA26SE32)',
    'Drone Delivery and Smart Locker Management System (DDSLMS) – product name Lock.R',
    'Lê Thị Yến Vi (SE182544, leader) · Trương Nguyễn Thái Bình (SE182370) · '
    'Nguyễn Quốc Bảo Huy (SE180211) · Trần Kim Nhã (SE182290)',
    'Đặng Ngọc Minh Đức · Đỗ Hữu Tiến',
    'Claude Code (Anthropic) – model Claude Opus 5.5 (claude-opus-5-5)',
    '09/11/2026',
    'Tag review-2 on github.com/LockR-Tech: backend fdf7480 · frontend 77cda59 · mobile b184a71 · '
    'iot f7bc145 · docs 8d2ac0b',
    '2.0 (proposed final: form signed 17/08/2026 with BM03 Record of Changes dated 09/11/2026)',
    '1.0',
    '09/11/2026',
]

# ---------------------------------------------------------------- raw AI output (do not edit)
# ID | Category | Location | Finding | Severity | Evidence
FINDINGS = [
    ['SR-01', 'Scope', 'SRS UC08, UC12, UC22; §3.2.24–3.2.26, §3.6.8',
     'Wallet (top-up, payment by wallet, withdrawal to bank) is specified but is not in registration v2.0 '
     'and the mobile app no longer offers it.',
     'High',
     'mobile lib/ calls only GET /api/wallet/transactions, /spending-stats, /total-by-method; no top-up, '
     'wallet checkout or /api/wallet/withdraw call. payment-service WalletController still exposes them.'],
    ['SR-02', 'Scope', 'SRS UC05',
     'Face ID registration / sign-in is specified but is neither in the registration nor implemented.',
     'Medium',
     'mobile core/config/feature_flags.dart: faceRecognitionEnabled = false; backend has no '
     '/api/auth/ai/* endpoint.'],
    ['SR-03', 'Scope', 'Registration §3.2 c) Module 1 (ETA)',
     'Registration item "Estimate delivery time (ETA)" has no FR in the SRS.',
     'Medium',
     'SRS contains no ETA requirement; order-service drone read model returns etaMinutes.'],
    ['SR-04', 'Scope', 'Registration §3.2 c) Module 3',
     'Registration item "Generate maintenance notifications and alerts" has no FR in the SRS.',
     'Medium',
     'SRS §3.3.8, §3.4.5, §3.6.6 describe schedules and inspections only.'],
    ['SR-05', 'Scope', 'Registration §3.2 c) Modules 1–2',
     '"Track delivery history and performance statistics" and "Monitor locker utilization" are only '
     'partly covered: UC25 lists revenue, orders by status, peak hours, user growth, top locations.',
     'Low',
     'SRS UC25, §3.6.2.'],
    ['SR-06', 'Scope', 'SRS UC16; registration §3.2 c) Module 2',
     'Opening an order\'s own box over Bluetooth is implemented, but it is neither in the registration nor '
     'specified in the SRS, which only has the admin-granted Bluetooth test (UC16).',
     'Medium',
     'iot-service BleOrderController POST /api/iot/ble/orders/{orderId}/token, BleOrderService, table '
     'ble_order_tokens; order-service BleOrderAccessService.'],
    ['SR-07', 'Scope', 'SRS UC08, UC09, UC13–UC16, UC24, UC28, UC31, UC34; §3.2.6, §3.2.16, §3.2.17, '
     '§3.4.6, §3.4.7',
     'FRs not covered by registration v2.0: VietQR payment, hourly box rental, box incident tickets with '
     'SLA, vouchers and loyalty, Bluetooth open test, kiosk login by QR, parcel-drop recovery, favorite '
     'stores, delegate pickup / change PIN, ratings and complaints, mission planner, flight data.',
     'Medium',
     'SRS use cases and headings; registration v2.0 §3.2 c) Modules 1–4 do not mention them.'],
    ['SR-08', 'Requirements', 'SRS §3.2–§3.6',
     'FRs have no testable acceptance criteria: each function is described by screen, trigger and business '
     'rules. Testable criteria exist only for 16 features in Design Brief §6.',
     'High',
     'SRS has no acceptance-criteria field or section (no occurrence of "acceptance").'],
    ['SR-09', 'Requirements', 'SRS §4.2.1–§4.2.4',
     'NFRs give thresholds without a measurement method: availability 99 %, read < 1 s / write < 2 s, '
     'box open 5 s, assistant 10 s, usability 3 min / 30 s, capacity 100 sessions.',
     'Medium',
     'SRS §4.2 text.'],
    ['SR-10', 'Data', 'Logical ERD (rp3/srs-assets/drawio/05*-logical-erd*; _generator/entities.json)',
     'Seven tables in code and DB script are missing from the ERD: storage_handovers, drone_flight_blocks, '
     'drone_flight_track_points, drone_station_suspensions, drone_station_suspension_logs, '
     'ble_order_tokens, cabinet_hardware_configs.',
     'Medium',
     '@Entity StorageHandover, DroneFlightBlock, DroneFlightTrackPoint, DroneStationSuspension, '
     'DroneStationSuspensionLog, BleOrderToken, CabinetHardwareConfig; CREATE TABLE in Flyway '
     'migrations; absent from entities.json.'],
    ['SR-11', 'Data', 'Logical ERD',
     'Ten columns added by migrations after the ERD was generated (29/10) are missing: '
     'orders.pending_extension_fee, orders.pending_extension_hours, lockers.deleted_at, '
     'locker_boxes.deleted_at, drone_units.deleted_at, user_profiles.deleted_at, user_profiles.language, '
     'user_profiles.terms_accepted, fcm_tokens.language, drone_parcel_incidents.recovery_station_dispatched_at.',
     'Medium',
     'ALTER TABLE … ADD COLUMN in Flyway migrations committed since 29/10/2026; absent from entities.json.'],
    ['SR-12', 'Data', 'Logical ERD; SDD §2',
     'system_settings and system_setting_audits exist in the database of every service but are not in the '
     'ERD.',
     'Low',
     'Flyway migrations of auth, order, locker, payment, iot, store, loyalty and assistant services; '
     'common-lib business settings framework.'],
    ['SR-13', 'States', 'Report 3, Report 4',
     'Sixteen state machine diagrams exist only as draw.io sources; none is included in Report 3 or '
     'Report 4.',
     'High',
     'docs/rp3/srs-assets/drawio/06*-state-machine-*.drawio; SRS and SDD text has no state machine '
     'section.'],
    ['SR-14', 'States', '06f-state-machine-drone-delivery-session.drawio',
     'State PARCEL_RELEASE_FAILED used in code is missing from the drone delivery session state machine.',
     'Medium',
     'DroneDeliverySession.PARCEL_RELEASE_FAILED; DroneLockerCommunicationService.processParcelReleaseFailed '
     'and handleCloseResult.'],
    ['SR-15', 'States', 'SRS Table 5.4',
     'Delivery stage values omit ACCEPTED, PICKUP_ASSIGNED, PICKED_UP, DROP_REPORTED, FAILED and CANCELED, '
     'which code sets (they are in diagram 06c).',
     'Medium',
     'order-service setDeliveryStage / advanceToStage values.'],
    ['SR-16', 'States', 'SRS Table 5.4; 06-1-state-machine-order.drawio',
     'REFUND_PENDING and REFUNDED are listed as order statuses in the SRS but are not in the order state '
     'machine; DELIVERY_INCOMPLETE is checked in code but never set and not modelled.',
     'Low',
     'DroneLockerCommunicationService CLOSED_ORDER_STATUSES (only occurrence of DELIVERY_INCOMPLETE).'],
    ['SR-17', 'Flows', 'Report 4',
     'Activity diagrams (06a send parcel, 06b rent locker, 06c drone delivery, 06d AI assistant, 06e '
     'knowledge base) exist only as draw.io sources and are not in Report 4.',
     'High',
     'docs/rp3/srs-assets/drawio/06a–06e-activity-*.drawio; SDD text has no activity diagram.'],
    ['SR-18', 'Flows', 'Design Brief A1 WF-04',
     'Main flow "box incident to repair" has no activity diagram.',
     'Medium',
     'No activity diagram for incidents in docs/rp3/srs-assets/drawio or docs/diagrams.'],
    ['SR-19', 'Flows', '06c-activity-drone-delivery.drawio',
     'The diagram shows the sender placing the parcel in the sending locker; code implements home pickup '
     'by a drone technician (offer, accept, pickup code and photo).',
     'Medium',
     'order-service DronePickupService; endpoints /api/drone-technician/drone-orders/{id}/pickup/*.'],
    ['SR-20', 'Flows', 'Test suites; CI',
     'No test runs a whole flow across services and clients; flows are tested per service. The admin web '
     'has no automated tests and the iot repository has no CI workflow. CI run results cannot be verified '
     'from the repository.',
     'Medium',
     'backend OrderServiceSendFlowTest, DroneHomePickupFlowPostgresTest; frontend has no test files and '
     'deploy.yml only builds; iot .github has no workflow.'],
    ['SR-21', 'Architecture', 'SDD Figure 1.1, Table 1.1',
     'The drone companion computer (drone-iot: ArUco camera, MJPEG stream, servo release, signed delivery '
     'events) is not an architecture component.',
     'Medium',
     'iot/drone-iot/lockr_drone/camera.py, delivery.py, release.py, mqtt_publisher.py.'],
    ['SR-22', 'Architecture', 'SDD Table 1.1 No. 22',
     'eSMS.vn is an SMS provider in code but the architecture lists only Twilio. Whether SMS is enabled in '
     'production cannot be verified from the repository.',
     'Low',
     'notification-service EsmsSmsSender, SmsChannelConfig (provider chosen from environment).'],
    ['SR-23', 'Architecture', 'SDD Table 1.1',
     'Nominatim geocoding and Esri ArcGIS tiles used by the mobile app, and the landing page app, are not '
     'in the architecture.',
     'Low',
     'mobile pickup_geocoder.dart, location_picker.dart, drone_base_tile_layer.dart; frontend/landingPage.'],
    ['SR-24', 'Design vs code', 'SDD §3.2; SRS UC15, §3.2.5',
     'Kiosk login by QR: the kiosk UI never creates a QR session, so the designed flow cannot start.',
     'Medium',
     'iot/ui/src/api.js has no /api/auth/kiosk/qr-sessions call; auth-service KioskQrLoginController and '
     'mobile qr_login exist.'],
    ['SR-25', 'Design vs code', 'SDD Table 1.1 No. 03; SRS UC17; registration §3.1 Module 2',
     'Pickup at the kiosk accepts a typed code only; the kiosk cannot scan a QR code.',
     'Medium',
     'iot/ui/src/api.js (unlockWithCode, unlockBox); no camera or QR library in the kiosk UI.'],
    ['SR-26', 'Design vs code', 'SDD §1.2.15; SDD drone sections',
     'The SDD describes drone-iot as telemetry only; parcel release by servo (parcelRelease, '
     'DROP_PHASE_COMPLETED, PARCEL_RELEASE_FAILED) is implemented but not designed.',
     'Medium',
     'drone-iot lockr_drone/release.py, delivery.py; order-service DroneLockerCommunicationService; SDD has '
     'no mention of servo or parcel release.'],
    ['SR-27', 'Scope', 'Registration §3.2 g) Phase 2; §3.3 b) In Scope',
     'Registration item "Drone Simulator Service" has no FR; the SRS mentions only a payment simulator.',
     'Medium',
     'order-service DroneDeliverySimulator; SRS §3.2.10 (payment simulator only).'],
    ['SR-28', 'Scope', 'Registration §3.2 b) Proposed Solutions',
     'The registration states that drones operate between a central hub and Smart Locker stations; no FR '
     'covers a hub. The SRS specifies flights between two lockers with home pickup by a drone technician.',
     'Medium',
     'SRS UC10, §3.2.19, §3.4.1; order-service DroneSourceLockerSelector, DronePickupService.'],
]

TOP5 = [
    ['1', 'SR-08', 'SRS FRs have no testable acceptance criteria.'],
    ['2', 'SR-13', 'State machine diagrams are not in Report 3/4.'],
    ['3', 'SR-17', 'Activity diagrams are not in Report 4.'],
    ['4', 'SR-01', 'Wallet is specified but out of registration and removed from the app.'],
    ['5', 'SR-10', 'Seven tables in code are missing from the Logical ERD.'],
]

# ---------------------------------------------------------------- team response (team decision)
# Balanced across the 4 members: 24 Planned items = 6 per member (Vi: 6, Bình: 6, Huy: 6, Nhã: 6).
P = 'Planned – '
RESPONSE = {
    'SR-01': 'Fixed – customer wallet removed from SRS, SDD and Project Tracking, '
             'https://github.com/LockR-Tech/docs/commit/8771a1cb6212aff11997bc6914848827f805cd25',
    'SR-02': P + 'remove Face ID from SRS – Huy, 15/11/2026',
    'SR-03': P + 'add ETA FR to SRS – Vi, 15/11/2026',
    'SR-04': P + 'add maintenance alert FR to SRS – Nhã, 15/11/2026',
    'SR-05': P + 'specify delivery statistics and utilization in UC24 – Bình, 15/11/2026',
    'SR-06': P + 'add Bluetooth order-open use case (G2) – Huy, 15/11/2026',
    'SR-07': 'Kept – the registration keeps the signed scope; features added in Iteration 1 are specified in '
             'the SRS and listed in Design Brief §6',
    'SR-08': P + 'add acceptance criteria per FR (from Design Brief §6, G6) – Nhã, 22/11/2026',
    'SR-09': P + 'add measurement method to each NFR (Design Brief §7) – Huy, 15/11/2026',
    'SR-10': P + 'regenerate Logical ERD from current entities (G1) – Bình, 15/11/2026',
    'SR-11': P + 'regenerate Logical ERD with new columns (G1) – Bình, 15/11/2026',
    'SR-12': P + 'add settings tables to ERD – Bình, 15/11/2026',
    'SR-13': P + 'insert state machines into Report 4 (G3) – Vi, 15/11/2026',
    'SR-14': P + 'add PARCEL_RELEASE_FAILED to session state machine – Nhã, 15/11/2026',
    'SR-15': P + 'complete delivery stage values in SRS 5.4 – Vi, 15/11/2026',
    'SR-16': P + 'align order statuses in SRS and diagram – Bình, 15/11/2026',
    'SR-17': P + 'insert activity diagrams into Report 4 (G3) – Vi, 15/11/2026',
    'SR-18': 'Fixed – incident activity diagram 06f-activity-handle-incident-ticket.drawio added, '
             'https://github.com/LockR-Tech/docs/commit/e28e6c339a349f93b2a7a042a379615aa4a7dddc',
    'SR-19': P + 'redraw drone activity diagram with home pickup (G3) – Vi, 15/11/2026',
    'SR-20': P + 'map CI tests to §6 TC IDs, add cross-service e2e and iot CI (G5) – Nhã, 22/11/2026',
    'SR-21': P + 'add drone companion computer to architecture – Nhã, 15/11/2026',
    'SR-22': P + 'add eSMS to architecture – Bình, 15/11/2026',
    'SR-23': P + 'add map services and landing page to architecture – Huy, 15/11/2026',
    'SR-24': P + 'wire kiosk QR session or drop UC14 – Huy, 22/11/2026',
    'SR-25': P + 'align SRS UC16 with registration change No. 6 (PIN at kiosk; Bluetooth or locker QR in '
             'the app) – Huy, 15/11/2026',
    'SR-26': P + 'design parcel release in SDD – Vi, 15/11/2026',
    'SR-27': P + 'add demo simulator FR to SRS – Nhã, 15/11/2026',
    'SR-28': 'Kept – the registration keeps the signed text; SRS and Design Brief describe the '
             'locker-to-locker model with home pickup',
}


def summary_rows():
    rows = []
    for sev in ('High', 'Medium', 'Low'):
        ids = [f[0] for f in FINDINGS if f[4] == sev]
        counts = {k: sum(RESPONSE[i].startswith(k) for i in ids) for k in ('Fixed', 'Kept', 'Planned')}
        rows.append([str(len(ids))] + [str(counts[k]) for k in ('Fixed', 'Kept', 'Planned')])
    return rows


d = docx.Document(SRC)
rebrand_sep490(d)
t = d.tables
fill_column(t[0], RUN_INFO)
fill_table(t[2], [f + [RESPONSE[f[0]]] for f in FINDINGS])
set_widths(t[2], [1.3, 1.7, 2.0, 4.3, 1.6, 3.2, 2.9])
fill_table(t[3], TOP5)
fill_table(t[4], summary_rows(), first_col=1)
remove_grey_guidance(d)
keep_rows_together(d)
for row in t[4].rows[:-1]:  # the summary table stays on one page
    for cell in row.cells:
        for para in cell.paragraphs:
            para.paragraph_format.keep_with_next = True
d.save(OUT)
print('saved', OUT, '| findings', len(FINDINGS),
      {s: sum(f[4] == s for f in FINDINGS) for s in ('High', 'Medium', 'Low')})

