import serial
import pynmea2
import time

GPS_PORT = "/dev/ttyAMA0"
GPS_BAUD = 57600  # Default HGLRC 100 Pro
TIMEOUT = 1

# UBX CFG-PRT para activar NMEA+UBX
CFG_PRT = bytes([
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 
    0x01, 0x00, 0x00, 0x00, 0xD0, 0x08, 0x00, 0x00,
    0x80, 0x25, 0x00, 0x00, 0x07, 0x00, 0x03, 0x00, 0x00, 0x00
])

# Calcular checksum UBX
def ubx_checksum(msg):
    ck_a = 0
    ck_b = 0
    for b in msg[2:len(msg)]:
        ck_a = (ck_a + b) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return bytes([ck_a, ck_b])

CFG_PRT += ubx_checksum(CFG_PRT)

# Abrir UART
ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=TIMEOUT, bytesize=8, parity='N', stopbits=1)
time.sleep(1)
ser.reset_input_buffer()

# Enviar comando UBX
ser.write(CFG_PRT)
print("UBX enviado para activar NMEA+UBX, espera 2s...")
time.sleep(2)

# Leer datos NMEA legibles
print("Leyendo GPS (CTRL+C para salir)...")
while True:
    try:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if not line:
            continue
        if line.startswith('$'):
            try:
                msg = pynmea2.parse(line)
                if isinstance(msg, pynmea2.GGA):
                    fix = "Fix" if msg.gps_qual > 0 else "Waiting for fix"
                    print(f"{fix} | Lat: {msg.latitude} {msg.lat_dir}, Lon: {msg.longitude} {msg.lon_dir}, Alt: {msg.altitude} {msg.altitude_units}, Sat: {msg.num_sats}")
                elif isinstance(msg, pynmea2.RMC):
                    speed_kmh = float(msg.spd_over_grnd) * 1.852 if msg.spd_over_grnd else 0
                    print(f"Speed: {speed_kmh:.1f} km/h | Date: {msg.datestamp}, Time: {msg.timestamp}")
            except pynmea2.ParseError:
                continue
    except KeyboardInterrupt:
        print("Saliendo...")
        break

ser.close()
