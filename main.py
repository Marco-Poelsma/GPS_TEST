import serial
import time

GPS_PORT = "/dev/ttyAMA0"
GPS_BAUD = 57600

# UBX para activar NMEA+UBX
CFG_PRT = bytes([
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00,
    0x01, 0x00, 0x00, 0x00, 0xD0, 0x08, 0x00, 0x00,
    0x80, 0x25, 0x00, 0x00, 0x07, 0x00, 0x03, 0x00, 0x00, 0x00
])

# Checksum UBX
def ubx_checksum(msg):
    ck_a = 0
    ck_b = 0
    for b in msg[2:len(msg)]:
        ck_a = (ck_a + b) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return bytes([ck_a, ck_b])

CFG_PRT += ubx_checksum(CFG_PRT)

# Abrir UART
ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=1, bytesize=8, parity='N', stopbits=1)
time.sleep(1)
ser.reset_input_buffer()

# Enviar UBX
ser.write(CFG_PRT)
print("UBX enviado para activar NMEA+UBX. Espera 2s...")
time.sleep(2)

# Leer GPS
print("Leyendo GPS (CTRL+C para salir)...")
while True:
    try:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if not line:
            continue
        if line.startswith('$G'):
            parts = line.split(',')
            if line.startswith('$GNGGA'):
                fix = "Fix" if parts[6] != '0' else "Waiting for fix"
                lat = parts[2]
                lat_dir = parts[3]
                lon = parts[4]
                lon_dir = parts[5]
                alt = parts[9]
                sats = parts[7]
                print(f"{fix} | Lat: {lat} {lat_dir}, Lon: {lon} {lon_dir}, Alt: {alt} m, Sat: {sats}")
            elif line.startswith('$GNRMC'):
                speed = float(parts[7]) * 1.852 if parts[7] else 0
                date = parts[9]
                time_gps = parts[1]
                print(f"Speed: {speed:.1f} km/h | Date: {date}, Time: {time_gps}")
    except KeyboardInterrupt:
        print("Saliendo...")
        break

ser.close()
