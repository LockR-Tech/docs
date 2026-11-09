"""Conceptual ERD theo microservice: mỗi service (bounded context) một khối, chỉ các thực thể nghiệp vụ chính,
không thuộc tính. Nét liền = quan hệ trong cùng database; nét đứt = tham chiếu sang service khác bằng ID logic.
Đi dây bằng cùng bộ định tuyến với Logical ERD: không cắt, không trùng, không xuyên thực thể.

Chạy: python gen_conceptual.py   →  ../../conceptual-erd-microservices/conceptual-erd-microservices.drawio + .png"""
import os
import sys

import gen
from gen import D, SVC, FONT, NN, M, REL, ENT, crow, STRAIGHT_SOLID, STRAIGHT_DASH
from route import route_all, anchor

OUT = os.path.join(os.path.dirname(gen.OUT), "conceptual-erd-microservices")

# quan hệ suy ra được qua đường khác – bỏ ở mức khái niệm (vẫn đủ trong Logical ERD)
SKIP = {("LockerOrder", "LockerUnit"), ("LockerOrder", "StoreLocation"), ("LockerReport", "LockerUnit"),
        ("PaymentRecord", "UserProfile"), ("BoxAccessLog", "LockerOrder"), ("Promotion", "LockerUnit"),
        ("LockerReport", "MaintenanceSchedule")}

EW, EH = 220, 50                      # kích thước một thực thể
TALL = {"UserProfile": 130, "LockerOrder": 90}   # thực thể trung tâm nhiều dây nối: cao hơn để đủ chỗ cắm dây
# khối service: (x, y, w, h), [(thực thể, dx, dy, rộng)]
# Bố cục chọn để các đường không phải đan chéo: các service chỉ nối vào UserProfile nằm phía trên user-service;
# store trên locker, iot dưới locker (đặt iot phía trên thì dây BoxAccessLog→LockerBox chắn lối LockerUnit→UserProfile);
# locker nối order theo hướng xuống – phải; payment nằm sau loyalty,
# dây từ đơn hàng tới thanh toán đi phía dưới.
LAYOUT = {
    "store-service": ((80, 150, 340, 170), [("StoreLocation", 60, 80, EW)]),
    "iot-service": ((380, 1060, 600, 170), [("GatewayDevice", 40, 80, EW), ("BoxAccessLog", 340, 80, EW)]),
    "auth-service": ((1180, 150, 340, 170), [("AuthAccount", 60, 80, EW)]),
    "notification-service": ((1580, 150, 340, 170), [("NotificationMessage", 60, 80, EW)]),
    "assistant-service": ((1980, 150, 620, 170), [("AssistantConversation", 40, 80, 260), ("KbDocument", 360, 80, EW)]),
    "locker-service": ((80, 420, 960, 560), [("MaintenanceSchedule", 50, 90, EW), ("LockerUnit", 350, 90, EW),
                                             ("DroneUnit", 50, 290, EW), ("LockerBox", 350, 290, EW),
                                             ("LockerReport", 680, 290, EW), ("DroneDeliveryRequest", 200, 460, EW)]),
    "user-service": ((1140, 420, 420, 280), [("UserProfile", 40, 90, 340)]),
    "loyalty-service": ((1640, 600, 340, 380), [("LoyaltyAccount", 60, 70, EW), ("PointTransaction", 60, 260, EW)]),
    "payment-service": ((2380, 680, 300, 360), [("PaymentRecord", 40, 60, EW), ("RefundRecord", 40, 230, EW)]),
    "order-service": ((1100, 1080, 1000, 640), [("DroneMission", 40, 90, EW), ("LockerOrder", 330, 90, 300),
                                               ("DroneParcelIncident", 40, 300, EW), ("PromotionUsage", 370, 300, EW),
                                               ("Promotion", 370, 480, EW), ("OrderDetail", 720, 90, EW),
                                               ("OrderRating", 720, 240, EW), ("OrderComplaint", 720, 390, EW),
                                               ("DronePickup", 720, 540, EW)]),
}


def build():
    d = D("conceptual-erd-microservices")
    d.v("<b>Conceptual ERD – theo microservice</b>", 80, 40, 2600, 40,
        "text;html=1;align=left;verticalAlign=middle;fontSize=28;" + FONT)
    boxes, walls, tids = {}, [], {}
    for svc, ((x, y, w, h), items) in LAYOUT.items():
        _, db, fill, stroke, head, _ = SVC[svc]
        d.v("", x, y, w, h, f"rounded=1;arcSize=3;fillColor={fill};strokeColor={stroke};strokeWidth=3;html=1;")
        d.v(f"<b>{svc}</b>", x + 16, y + 12, w - 32, 30,
            f"text;html=1;align=left;verticalAlign=middle;fontSize=17;fontColor={stroke};" + FONT)
        boxes[("_title", svc)] = (x + 14, y + 10, 10 * len(svc) + 10, 34)
        walls.append((x, y, w, h))
        for c, dx, dy, ew in items:
            eh = TALL.get(c, EH)
            tids[c] = d.v(f"<b>{c}</b>", x + dx, y + dy, ew, eh,
                          f"rounded=0;whiteSpace=wrap;html=1;fontSize=15;fillColor={head};strokeColor={stroke};strokeWidth=1.5;" + FONT)
            boxes[c] = (x + dx, y + dy, ew, eh)
    ents = set(tids)
    assert all(c in ENT for c in ents)
    edges = []
    for c, col, p, mult in REL:
        if c in ents and p in ents and (c, p) not in SKIP:
            cross = ENT[c]["service"] != ENT[p]["service"]
            edges.append({"key": (c, col), "a": c, "b": p, "cross": cross, "col": col, "mult": mult,
                          "tries": [("LRTB", "LRTB", None, None)]})
    done = route_all(boxes, edges, walls=walls, tag="conceptual", spacing=2, pin_internal=True, polish=12, attempts=80)
    for e in edges:
        pts = done[e["key"]][0]
        s, t = crow(e["mult"] == M, NN.get(f"{e['a']}.{e['col']}", False))
        base = STRAIGHT_DASH if e["cross"] else STRAIGHT_SOLID
        d.e(tids[e["a"]], tids[e["b"]], base + f"startArrow={s};endArrow={t};" + anchor("exit", boxes[e["a"]], pts[0])
            + anchor("entry", boxes[e["b"]], pts[-1]), points=pts[1:-1])
    os.makedirs(OUT, exist_ok=True)
    gen.OUT = OUT
    return d.save()


if __name__ == "__main__":
    try:
        print(build())
    except RuntimeError as ex:
        print("LỖI:", ex)
        sys.exit(1)
