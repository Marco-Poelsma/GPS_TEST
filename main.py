import serial
import pynmea2
import time
import math
from datetime import datetime

# ===== CONFIG =====
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 9600
LOG_INTERVAL = 1  # seconds
CSV_FILE = None

# ===== STATE =====
start_logging = False
start_lat = None
start_lon = None
prev_lat = None
prev_lon = None
total_distance = 0.0
max_speed = 0.0
last_log_time = 0
status = "w8-4-fix"

# ===== HELPERS =====
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def start_new_log():
    global CSV_FILE, start_logging
    ts = datetime.utcnow().strftime("%d%m_H%H%M")
    CSV_FILE = f"{ts}.csv"
    with open(CSV_FILE, "w") as f:
        f.write("lat,lon,alt,speed_kmh,time,total_dist,start_dist\n")
    start_logging = True
    print(f"[LOG] Started: {CSV_FILE}")

# ===== MAIN =====
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

print("GPS logger running… waiting for fix")

while True:
    try:
        line = ser.readline().decode("ascii", errors="ignore").strip()
        if not line.startswith("$"):
            continue

        msg = pynmea2.parse(line)

        if isinstance(msg, pynmea2.types.talker.GGA):
            if msg.latitude and msg.longitude:
                lat = msg.latitude
                lon = msg.longitude
                alt = float(msg.altitude) if msg.altitude else 0.0
                status = "rdy"

                if not start_logging:
                    start_lat = lat
                    start_lon = lon
                    prev_lat = lat
                    prev_lon = lon
                    start_new_log()

        if isinstance(msg, pynmea2.types.talker.RMC):
            if msg.spd_over_grnd is None:
                continue

            speed_kmh = float(msg.spd_over_grnd) * 1.852
            max_speed = max(max_speed, speed_kmh)

            now = time.time()
            if now - last_log_time >= LOG_INTERVAL and start_logging:
                dist_start = haversine(start_lat, start_lon, lat, lon)
                step_dist = haversine(prev_lat, prev_lon, lat, lon)

                if 5 <= step_dist < 100:
                    total_distance += step_dist
                    prev_lat = lat
                    prev_lon = lon

                with open(CSV_FILE, "a") as f:
                    f.write(
                        f"{lat},{lon},{alt},{speed_kmh:.2f},"
                        f"{datetime.utcnow().isoformat()},"
                        f"{int(total_distance)},"
                        f"{int(dist_start)}\n"
                    )

                last_log_time = now

                print(
                    f"[GPS] {speed_kmh:.1f} km/h | "
                    f"TD: {int(total_distance)} m | "
                    f"SD: {int(dist_start)} m"
                )

    except pynmea2.ParseError:
        continue
    except KeyboardInterrupt:
        print("\nStopping logger")
        break
