"""1.1 System Architecture of Lock.R (Figure II.1.1) — simplified, logo-style overview."""
import base64, os
from dl import Diagram

ICONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
d = Diagram("arch_system")
_n = iter(range(2, 10**6))
d.nid = lambda: f"arch{next(_n)}"  # own id prefix so draw.io never merges these with the old diagram's c2, c3 ...
G = {}  # id -> (x, y, w, h)

GROUP = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;fontStyle=1;fontSize=14;spacingTop=4;"
         "fillColor=#ffffff;strokeColor=#000000;")
TILE = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=bottom;spacingBottom=4;fontSize=11;"
        "fillColor=#ffffff;strokeColor=#000000;")
TW, TH, IC = 100, 100, 46


def node(label, x, y, w, h, style):
    cid = d.v(label, x, y, w, h, style)
    G[cid] = (x, y, w, h)
    return cid


def group(title, x, y, w, h):
    return node(title, x, y, w, h, GROUP)


def icon_style(name, color):
    svg = open(os.path.join(ICONS, name + ".svg"), encoding="utf-8").read()
    svg = svg.replace("<svg ", f'<svg fill="{color}" ', 1)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"shape=image;html=1;imageAspect=1;aspect=fixed;image=data:image/svg+xml,{b64};"


def tile(name, sub, x, y, icon=None, color="#000000", badge=None, w=TW):
    label = f"{name}<br><font style=\"font-size:9px\" color=\"#555555\">{sub}</font>" if sub else name
    cid = node(label, x, y, w, TH, TILE)
    ix, iy = x + (w - IC) / 2, y + 10
    if icon:
        d.v("", ix, iy, IC, IC, icon_style(icon, color))
    elif badge:  # brand without a public icon: coloured text badge
        d.v(badge, ix - 6, iy + 4, IC + 12, IC - 8,
            f"rounded=1;arcSize=20;html=1;fontStyle=1;fontSize=12;fontColor=#ffffff;fillColor={color};strokeColor=none;")
    return cid


CALL = "html=1;endArrow=block;endFill=1;rounded=0;"
RET = "html=1;endArrow=open;dashed=1;rounded=0;"
ASY = "html=1;endArrow=open;dashed=1;dashPattern=1 3;strokeWidth=1.5;rounded=0;"
BI = ASY + "startArrow=open;"


def link(a, b, style, pa, pb, label="", pts=()):
    """Straight edge glued to a and b at absolute points pa / pb."""
    ax, ay, aw, ah = G[a]
    bx, by, bw, bh = G[b]
    style += (f"exitX={(pa[0]-ax)/aw:.4f};exitY={(pa[1]-ay)/ah:.4f};exitDx=0;exitDy=0;"
              f"entryX={(pb[0]-bx)/bw:.4f};entryY={(pb[1]-by)/bh:.4f};entryDx=0;entryDy=0;"
              "fontSize=10;labelBackgroundColor=#ffffff;")
    return d.e(a, b, style, label, pts=pts)


def pair(a, b, pa, pb, off=(0, 10)):
    """Call a->b and dashed return b->a, offset by `off`."""
    link(a, b, CALL, pa, pb)
    link(b, a, RET, (pb[0] + off[0], pb[1] + off[1]), (pa[0] + off[0], pa[1] + off[1]))


# ---------------------------------------------------------------- annotations
ann = d.v("<b>Annotations</b>", 0, 20, 190, 105,
          "rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;fontSize=11;")
for k, (t, st) in enumerate([("Call:", CALL), ("Return:", RET), ("Async / MQTT:", ASY)]):
    d.v(t, 8, 46 + k * 24, 80, 18, "text;html=1;align=left;fontSize=10;")
    d.e(None, None, st, sp=(95, 55 + k * 24), tp=(178, 55 + k * 24))

# ---------------------------------------------------------------- maps (left)
maps = group("Maps &amp; Routing", 0, 345, 140, 160)
tile("OpenStreetMap", "OSRM routing", 20, 385, "openstreetmap", "#7EBC6F")

# ---------------------------------------------------------------- clients
fe = group("Client Applications", 190, 190, 160, 450)
tile("Mobile App", "Flutter · Android / iOS", 220, 230, "flutter", "#02569B")
tile("Admin Web", "React", 220, 360, "react", "#149ECA")
tile("Kiosk Screen", "React", 220, 490, "react", "#149ECA")

# ---------------------------------------------------------------- backend
be = group("Backend · Azure VM (Docker Compose)", 420, 150, 560, 520)
ngx = tile("Nginx", "TLS · reverse proxy", 445, 330, "nginx", "#009639")
gw = tile("API Gateway", "Spring Cloud · JWT", 600, 330, "spring", "#6DB33F")
eur = tile("Discovery", "Eureka", 600, 195, "spring", "#6DB33F")
ms = tile("Microservices", "10 Spring Boot services", 790, 330, "springboot", "#6DB33F", w=130)
mqtt = tile("MQTT Broker", "Mosquitto", 445, 535, "eclipsemosquitto", "#3C5280")
pg = tile("PostgreSQL", "1 DB per service", 600, 535, "postgresql", "#4169E1")
vec = tile("pgvector", "assistant-db", 720, 535, "postgresql", "#4169E1")
mq = tile("RabbitMQ", "laundry.events", 845, 535, "rabbitmq", "#FF6600")

# ---------------------------------------------------------------- cabinet & drone
# Real cabinet CAB-TU01: Pi 5 drives relays / TB6600 straight from GPIO (ADR-0007, HARDWARE_BACKEND=gpio);
# the Arduino + RS485 path is only an optional code path, not deployed hardware.
SUBG = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=10;fontStyle=1;fontSize=12;spacingTop=2;"
        "fillColor=#f7f7f7;strokeColor=#666666;dashed=1;")
iot = group("IoT Devices", 190, 715, 790, 335)
node("Smart Locker Cabinet (CAB-TU01)", 205, 745, 360, 295, SUBG)
lck = tile("Relay &amp; 7 Locks", "12 V · door sensors", 240, 775, badge="Relay", color="#555555")
lid = tile("Lid Motors", "2× TB6600 · lead screw", 240, 885, badge="TB6600", color="#8A6D3B")
pi = tile("Raspberry Pi 5", "cabinet controller", 455, 830, "raspberrypi", "#A22846")
node("Drone", 585, 745, 380, 295, SUBG)
drn = tile("Raspberry Pi 5", "drone controller", 625, 790, "raspberrypi", "#A22846")
srv = tile("Drop Servo", "MG996R · latch", 625, 925, badge="Servo", color="#2E7D32")
fc = tile("Pixhawk 6C", "ArduPilot autopilot", 830, 775, badge="Pixhawk", color="#2B2B2B")
cam = tile("Camera", "OpenCV ArUco", 830, 900, "opencv", "#5C3EE8")

# ---------------------------------------------------------------- external services (right)
X = 1060
ai = group("AI Services", X, 0, 260, 155)
tile("Claude", "Anthropic · answers", X + 20, 38, "anthropic", "#191919")
tile("Voyage AI", "embeddings", X + 140, 38, badge="Voyage", color="#5B4BDB")

ntf = group("Authentication &amp; Notification", X, 180, 380, 155)
tile("Firebase", "Auth · FCM push", X + 20, 218, "firebase", "#DD2C00")
tile("SMTP", "email OTP", X + 140, 218, "gmail", "#EA4335")
tile("Twilio", "SMS pickup code", X + 260, 218, "twilio", "#F22F46")

fs = group("File Storage", X, 360, 140, 155)
tile("Cloudinary", "images", X + 20, 398, "cloudinary", "#3448C5")

pay = group("Payment Gateway", X, 540, 140, 155)
tile("SePay", "VietQR · webhook", X + 20, 578, badge="SePay", color="#1D5BD8")

wx = group("Weather API", X, 720, 140, 155)
tile("Open-Meteo", "flight check", X + 20, 758, badge="☁ Meteo", color="#FF8C00")

# ---------------------------------------------------------------- edges
pair(fe, maps, (190, 420), (140, 420))                  # mobile map
pair(fe, ngx, (350, 375), (445, 375))                   # HTTPS / WSS
d.v("HTTPS / WSS", 352, 345, 92, 16, "text;html=1;align=center;fontSize=10;")
pair(ngx, gw, (545, 370), (600, 370))
pair(gw, ms, (700, 370), (790, 370))
link(gw, eur, CALL, (650, 330), (650, 295), "lookup")
link(ms, pg, CALL, (820, 430), (660, 535))
link(pg, ms, RET, (680, 535), (835, 430))
link(ms, vec, CALL, (850, 430), (760, 535))
link(vec, ms, RET, (780, 535), (862, 430))
link(ms, mq, BI, (895, 430), (895, 535))
link(ms, mqtt, BI, (790, 415), (545, 560))
link(pi, mqtt, BI, (495, 830), (495, 635))
d.v("open / sync · result · heartbeat", 310, 697, 180, 16, "text;html=1;align=right;fontSize=10;")
link(drn, mqtt, BI, (705, 790), (535, 635), "telemetry · delivery events / commands",
     pts=[(705, 685), (535, 685)])
# cabinet: GPIO out to relays and stepper drivers, lock feedback back in
link(pi, lck, CALL, (455, 845), (340, 815), "GPIO")
link(lck, pi, RET, (340, 840), (455, 862), "feedback")
link(pi, lid, CALL, (455, 895), (340, 930), "PUL / DIR")
# drone: Pixhawk streams MAVLink to the Pi (Pi only asks for message rates), Pi reads camera frames,
# Pi drives the payload-drop servo with PWM on GPIO18 (iot/drone-iot/servo.py)
link(fc, drn, BI, (830, 825), (725, 825), "MAVLink")
link(cam, drn, ASY, (830, 950), (725, 865), "frames")
link(drn, srv, CALL, (675, 890), (675, 925))
d.v("PWM", 680, 899, 40, 16, "text;html=1;align=left;fontSize=10;")

# backend -> external, each a call + dashed return
targets = [(ai, 70), (ntf, 250), (fs, 430), (pay, 610), (wx, 790)]
for k, (g, gy) in enumerate(targets):
    sy = 345 + k * 14
    link(ms, g, CALL, (920, sy), (X, gy))
    link(g, ms, RET, (X, gy + 22), (920, sy + 6))
d.save()
