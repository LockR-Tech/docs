"""1.1 System Architecture of Lock.R (Figure II.1.1)."""
from dl import Diagram

d = Diagram("arch_system")
GROUP = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;fontStyle=1;fontSize=15;spacingTop=6;"
         "fillColor=#ffffff;strokeColor=#000000;")
SUB = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;fontStyle=1;fontSize=13;spacingTop=4;"
       "fillColor=#f5f5f5;strokeColor=#666666;dashed=1;")


def box(label, sub, x, y, w=150, h=62, fill="#dae8fc", stroke="#6c8ebf", shape="rounded=1;arcSize=8;"):
    return d.v(f"<b>{label}</b><br><font style=\"font-size:10px\" color=\"#444444\">{sub}</font>", x, y, w, h,
               f"{shape}whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize=12;")


def cyl(label, sub, x, y, w=150, h=78, fill="#dae8fc", stroke="#6c8ebf"):
    return d.v(f"<b>{label}</b><br><font style=\"font-size:10px\" color=\"#444444\">{sub}</font>", x, y, w, h,
               f"shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=10;fillColor={fill};strokeColor={stroke};fontSize=12;")


CALL = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;fontSize=10;labelBackgroundColor=#ffffff;"
RET = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=open;dashed=1;fontSize=10;labelBackgroundColor=#ffffff;"
ASY = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=open;dashed=1;dashPattern=1 3;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#ffffff;"

# ---- clients
cli = d.v("Client Applications", 0, 150, 210, 450, GROUP)
mob = box("Mobile App", "Flutter 3 · Android / iOS<br>Riverpod · dio · STOMP", 25, 205, 160, 72, "#d5e8d4", "#82b366")
adm = box("Admin Web", "React 19 · Vite · RTK Query<br>Cloudflare Workers", 25, 315, 160, 72, "#d5e8d4", "#82b366")
land = box("Landing Page", "React · Cloudflare Workers", 25, 425, 160, 60, "#d5e8d4", "#82b366")
d.v("REST/JSON over HTTPS<br>STOMP over WSS (/ws)", 25, 520, 160, 50, "text;html=1;align=center;fontSize=10;fontColor=#555555;")

# ---- backend VM
vm = d.v("Backend · Azure VM (Docker Compose)", 270, 40, 960, 700, GROUP)
ngx = box("Nginx", "TLS (Let's Encrypt)<br>api.locker-drone.tech", 295, 340, 130, 70, "#ffe6cc", "#d79b00")
gw = box("API Gateway", "Spring Cloud Gateway :8080<br>JWT check · RBAC by path", 460, 340, 165, 70, "#ffe6cc", "#d79b00")
eur = box("Discovery Server", "Eureka :8761", 470, 170, 145, 56, "#ffe6cc", "#d79b00")
ms = d.v("Microservices (Spring Boot 3 · Java 21)", 665, 75, 350, 520, SUB)
svcs = [("auth-service", ":8081 · login, OTP, 2FA"), ("user-service", ":8082 · profiles, roles"),
        ("order-service", ":8083 · orders, drone, promo"), ("locker-service", ":8084 · lockers, tickets"),
        ("payment-service", ":8086 · SePay, wallet"), ("notification-service", ":8087 · in-app, STOMP"),
        ("iot-service", ":8088 · MQTT bridge, PIN"), ("store-service", ":8089 · stores"),
        ("loyalty-service", ":8092 · points, tiers"), ("assistant-service", ":8093 · RAG assistant")]
for i, (n, s) in enumerate(svcs):
    r, c = divmod(i, 2)
    box(n, s, 680 + c * 165, 110 + r * 92, 155, 70, "#dae8fc", "#6c8ebf")
cl = box("common-lib", "DTOs · events · settings · media", 745, 600 + 0, 190, 50, "#e1d5e7", "#9673a6")
data = d.v("Data &amp; Messaging", 1040, 75, 170, 640, SUB)
pg = cyl("PostgreSQL 16", "1 database per service<br>(Flyway migrations)", 1050, 110)
vec = cyl("pgvector", "assistant-db<br>kb_chunks vector(1024)", 1050, 215)
mq = box("RabbitMQ", "topic exchange<br>laundry.events", 1050, 325, 150, 62, "#fff2cc", "#d6b656")
mqtt = box("MQTT Broker", "Mosquitto (WSS /mqtt)<br>cabinet/* · iot/* topics", 1050, 410, 150, 70, "#fff2cc", "#d6b656")

# ---- physical lockers
cab = d.v("Smart Locker Cabinet &amp; Drone", 270, 790, 960, 150, GROUP)
pi = box("Raspberry Pi Controller", "Python 3.13 · paho-mqtt · gpiod<br>heartbeat, open, lid, BLE", 560, 840, 200, 76, "#d5e8d4", "#82b366")
ard = box("Arduino / GPIO", "relay locks · reed sensors<br>sliding lid (RS485)", 840, 840, 170, 76, "#d5e8d4", "#82b366")
kio = box("Kiosk UI", "React web on the touch screen<br>PIN / QR pickup, send, rent", 300, 840, 190, 76, "#d5e8d4", "#82b366")
drn = box("Drone Companion Pi", "MAVLink → MQTT telemetry<br>(HMAC-signed)", 1040, 840, 170, 76, "#d5e8d4", "#82b366")

# ---- external services
ext = d.v("External Services", 1290, 26, 250, 914, GROUP)
exts = [("Firebase", "Auth (phone, Google) · FCM push", "auth / notification"),
        ("SePay", "VietQR bank transfer · webhook", "payment-service"),
        ("Cloudinary", "image storage · signed upload", "user / order / locker / store"),
        ("SMTP · Twilio", "email OTP · pickup-code SMS", "auth / notification"),
        ("Anthropic Claude", "answer generation with citations", "assistant-service"),
        ("Voyage AI", "text embeddings (1024-d)", "assistant-service"),
        ("OpenStreetMap · OSRM", "maps · routing · directions", "mobile app"),
        ("Open-Meteo", "weather check before flights", "order-service")]
eids = []
for i, (n, s, u) in enumerate(exts):
    eids.append(box(n, f"{s}<br><i>used by {u}</i>", 1310, 80 + i * 110, 210, 84, "#f5f5f5", "#666666"))

# ---- annotations
ann = d.v("<b>Annotations</b>", 20, 640, 200, 110, "rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;fontSize=12;")
for k, (t, st) in enumerate([("Call", CALL), ("Return", RET), ("Async event", ASY)]):
    d.v(t + ":", 30, 668 + k * 26, 80, 20, "text;html=1;align=left;fontSize=11;")
    d.e(None, None, st.replace("edgeStyle=orthogonalEdgeStyle;", ""), sp=(120, 678 + k * 26), tp=(205, 678 + k * 26))

# ---- edges
def link(a, b, st, label="", ex=None, en=None, pts=()):
    if ex:
        st += f"exitX={ex[0]};exitY={ex[1]};exitDx=0;exitDy=0;"
    if en:
        st += f"entryX={en[0]};entryY={en[1]};entryDx=0;entryDy=0;"
    return d.e(a, b, st, label, pts=pts)


BI = ASY + "startArrow=open;startFill=0;"
link(cli, ngx, CALL, "", (1, 0.477), (0, 0.35))
link(ngx, cli, RET, "", (0, 0.65), (1, 0.523))
d.v("HTTPS / WSS", 205, 330, 95, 20, "text;html=1;align=center;fontSize=10;")
link(ngx, gw, CALL, "", (1, 0.35), (0, 0.35))
link(gw, ngx, RET, "", (0, 0.65), (1, 0.65))
link(gw, eur, CALL, "service lookup", (0.5, 0), (0.5, 1))
link(gw, ms, CALL, "", (1, 0.35), (0, 0.557))
link(ms, gw, RET, "", (0, 0.597), (1, 0.65))
d.v("lb:// routing to services<br>adds X-User-Id, X-User-Roles", 455, 418, 175, 34, "text;html=1;align=center;fontSize=10;fontColor=#333333;")
link(ms, pg, CALL, "", (1, 0.142), (0, 0.5))
link(ms, vec, CALL, "", (1, 0.344), (0, 0.5))
link(ms, mq, BI, "", (1, 0.54), (0, 0.5))
link(ms, mqtt, BI, "", (1, 0.7115), (0, 0.5))
link(ms, cl, ASY.replace("dashPattern=1 3;strokeWidth=1.5;", ""), "depends on", (0.5, 1), (0.5, 0))
link(pi, mqtt, BI, "MQTT: commands, heartbeat, results", (0.5, 0), (0.3, 1), pts=[(660, 765), (1095, 765)])
link(drn, mqtt, ASY, "telemetry", (0.7, 0), (0.7, 1))
link(pi, ard, CALL, "GPIO<br>RS485", (1, 0.5), (0, 0.5))
link(kio, pi, CALL, "local API", (1, 0.5), (0, 0.5))
link(kio, ngx, CALL, "/api/iot/* (PIN, QR)", (0.5, 0), (0.5, 1), pts=[(395, 775), (360, 775)])
link(ms, ext, CALL, "HTTPS (SDK / REST API)", (0.5, 0), (0.1, 0), pts=[(840, 12), (1315, 12)])
link(ext, ms, RET, "response / SePay webhook", (0.25, 0), (0.6, 0), pts=[(1352, 0), (875, 0)])
d.save()
