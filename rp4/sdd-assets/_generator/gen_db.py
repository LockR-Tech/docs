"""2. Database design: one physical diagram per service database (tables, columns, PK/FK, crow's foot)."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "erd"))
import erd_data  # noqa: E402  (ENT incl. assistant tables, REL)
from dl import Diagram, table_box, tw, REL as RELST  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ENT = erd_data.ENT
ENT["CabinetHardwareConfig"] = {"service": "iot-service", "table": "cabinet_hardware_configs", "fields": [
    erd_data.f("locker_id", "bigint", True), erd_data.f("config", "text"), erd_data.f("wiring", "text"),
    erd_data.f("updated_by", "bigint"), erd_data.f("updated_at", "timestamp"), erd_data.f("applied_by", "bigint"),
    erd_data.f("applied_at", "timestamp"), erd_data.f("apply_status", "varchar(20)"),
    erd_data.f("apply_message", "varchar(1000)")]}
NOTNULL = json.load(open(os.path.join(HERE, "erd", "fk_notnull.json"), encoding="utf-8"))
REL = erd_data.REL
CAP = 18

DBS = [
    ("auth_db", "auth-service", [[("RefreshToken", None), ("SocialIdentity", None)], [("AuthAccount", None)], [("EmailOtp", None)]]),
    ("user_db", "user-service", [[("UserProfile", None)]]),
    ("store_db", "store-service", [[("StoreLocation", None)]]),
    ("locker_db", "locker-service", [
        [("MaintenanceInspectionLog", "MaintenanceSchedule"), ("RepairLog", "LockerReport"), ("ReportAttachment", None),
         ("LockerReportRating", None)],
        [("MaintenanceSchedule", None), ("LockerReport", None)],
        [("LockerUnit", None), ("LockerBox", None)],
        [("DroneUnit", "LockerUnit"), ("DroneDeliveryRequest", None)],
        [("DroneDevice", "DroneUnit"), ("DroneIotLog", None), ("DroneMaintenanceLog", None), ("TechnicianPresence", None)]]),
    ("order_db", "order-service", [
        [("OrderDetail", None), ("OrderStatusHistory", None), ("OrderRating", None), ("OrderComplaint", None)],
        [("LockerOrder", None)],
        [("PromotionUsage", None), ("DronePickup", None), ("DroneMission", None), ("DroneDeliverySession", None)],
        [("Promotion", "PromotionUsage"), ("DronePickupOffer", "DronePickup"), ("DroneParcelIncident", "DroneMission"),
         ("DroneLockerCommLog", None)],
        [("PromotionClaim", None), ("DroneIncidentEvidence", "DroneParcelIncident"), ("DroneIncidentTimeline", None),
         ("DroneIncidentResolutionProposal", None), ("DroneTechnicianPresence", None)]]),
    ("payment_db", "payment-service", [[("PaymentRecord", None), ("Wallet", None)],
                                      [("RefundRecord", "PaymentRecord"), ("WalletTransaction", "Wallet")],
                                      [("WithdrawalRecord", None), ("UserBankAccount", None)]]),
    ("notification_db", "notification-service", [[("NotificationMessage", None)], [("FcmToken", None)]]),
    ("iot_db", "iot-service", [[("GatewayDevice", None), ("DeviceStatus", None), ("CabinetHardwareConfig", None)],
                               [("CabinetControlLog", None), ("BleTestGrant", None), ("BleSigningKey", None)],
                               [("BoxHardwareStatus", None), ("AccessAttempt", None), ("BoxAccessLog", None)]]),
    ("loyalty_db", "loyalty-service", [[("LoyaltyAccount", None)], [("PointTransaction", None)]]),
    ("assistant_db", "assistant-service", [[("AssistantMessage", None)], [("AssistantConversation", None)],
                                           [("KbChunk", None)], [("KbDocument", None), ("EvalCase", None)]]),
]


def svc_of(e):
    return ENT[e]["service"]


def rows_of(e):
    """PK first, then FKs, then the rest; (key, column, type)."""
    fks = {}
    for child, col, parent, _ in REL:
        if child == e:
            fks[col] = "FK" if svc_of(parent) == svc_of(e) else "(FK)"
    out = []
    for fl in ENT[e]["fields"]:
        k = "PK" if fl["pk"] else ""
        if fl["name"] in fks:
            k = (k + "," if k else "") + fks[fl["name"]]
        out.append((k, fl["name"], fl["type"]))
    out.sort(key=lambda r: (0 if "PK" in r[0] else 1 if "FK" in r[0] else 2))
    more = max(0, len(out) - CAP)
    return out[:CAP], more


def build(db, svc, cols):
    d = Diagram("db_" + db)
    info = {}
    for col in cols:
        for e, _ in col:
            rows, more = rows_of(e)
            w = max(210, tw(ENT[e]["table"], 12, True) + 40,
                    *(tw(n, 10) + tw(t, 10) + 70 for _, n, t in rows))
            h = 28 + (len(rows) + (1 if more else 0)) * 17 + 12
            info[e] = [rows, more, w, h, 0, 0]
    x = 30
    where = {}
    for ci, col in enumerate(cols):
        for si, (e, _) in enumerate(col):
            where[e] = (ci, si)
    colx = []
    for col in cols:
        cw = max(info[e][2] for e, _ in col)
        y = 70
        for e, anchor in col:
            if anchor:
                y = max(y, info[anchor][5])
            info[e][4], info[e][5] = x, y
            info[e][2] = cw
            y += info[e][3] + 40
        colx.append((x, cw))
        x += cw + 110
    width = x - 60
    height = max(v[5] + v[3] for v in info.values()) + 30
    d.v(f"<b>{db}</b> &nbsp;·&nbsp; PostgreSQL 16 &nbsp;·&nbsp; owned by {svc}", 0, 0, width + 60, height + 60,
        "rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontSize=15;"
        "fillColor=#f9f9f9;strokeColor=#999999;dashed=1;")
    ids = {}
    for e, (rows, more, w, h, x0, y0) in info.items():
        ids[e], _ = table_box(d, ENT[e]["table"], rows, x0, y0, w, more)
    gapuse = {}
    sideuse = {}

    def rowy(e, colname):
        for i, r in enumerate(info[e][0]):
            if r[1] == colname:
                return info[e][5] + 28 + 6 + (i + 0.5) * 17
        return info[e][5] + 34

    for child, col, parent, card in REL:
        if not (child in ids and parent in ids):
            continue
        nn = NOTNULL.get(f"{child}.{col}", False)
        st = RELST + ("endArrow=ERmandOne;" if nn else "endArrow=ERzeroToOne;") +             ("startArrow=ERzeroToMany;" if card == "many" else "startArrow=ERzeroToOne;")
        (cc, cs), (pc, ps) = where[child], where[parent]
        cx, cy, cw_, ch_ = info[child][4], info[child][5], info[child][2], info[child][3]
        px, py, pw, ph = info[parent][4], info[parent][5], info[parent][2], info[parent][3]
        yc = rowy(child, col)
        k = sideuse.get((parent, cc > pc), 0)
        sideuse[(parent, cc > pc)] = k + 1
        yp = py + 34 + 8.5 + k * 17
        if cc == pc and abs(cs - ps) == 1:
            up = cs > ps
            st += f"exitX=0.5;exitY={0 if up else 1};entryX=0.5;entryY={1 if up else 0};"
            d.e(ids[child], ids[parent], st)
            continue
        if abs(cc - pc) <= 1 and cc != pc:
            right = cc > pc          # child is right of parent
            g = pc if right else cc  # gap index after column g
            j = gapuse.get(g, 0)
            gapuse[g] = j + 1
            gx = colx[g][0] + colx[g][1] + 22 + 16 * j
            st += f"exitX={0 if right else 1};exitY={(yc - cy) / ch_:.4f};exitDx=0;exitDy=0;"                   f"entryX={1 if right else 0};entryY={(yp - py) / ph:.4f};entryDx=0;entryDy=0;"
            d.e(ids[child], ids[parent], st, pts=[(gx, yc), (gx, yp)])
            continue
        # far apart: go over the top of all tables
        top = 52 - 8 * len([1 for v in gapuse if v == "top"])
        gapuse.setdefault("top", 0)
        st += "exitX=0.5;exitY=0;entryX=0.5;entryY=0;"
        d.e(ids[child], ids[parent], st, pts=[(cx + cw_ / 2, top), (px + pw / 2, top)])
    d.v("<b>PK</b> primary key &nbsp; <b>FK</b> foreign key in this database &nbsp; <b>(FK)</b> logical id of a row "
        "owned by another service (checked by the service, no DB constraint)", 20, height + 22, width, 24,
        "text;html=1;align=left;fontSize=11;fontColor=#555555;")
    d.save()


if __name__ == "__main__":
    for db, svc, cols in DBS:
        build(db, svc, cols)
    covered = {e for _, _, cols in DBS for col in cols for e, _ in col}
    assert covered == set(ENT), set(ENT) ^ covered
    print("tables:", len(covered))
