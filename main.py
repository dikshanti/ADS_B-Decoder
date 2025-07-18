import socket
import pyModeS as pms
import requests
from requests.auth import HTTPBasicAuth

USERNAME = "cosmonot"
PASSWORD = "th9r9g99d"

def decode_adsb(hex_msg):
    result = {"hex": hex_msg}
    try:
        df = pms.df(hex_msg)
        result["df"] = df

        if df in [17, 18, 19]:  # Extended Squitter messages
            icao = pms.adsb.icao(hex_msg)
            tc = pms.adsb.typecode(hex_msg)
            result.update({"icao": icao, "typecode": tc})
            if 1 <= tc <= 4:
                callsign = pms.adsb.callsign(hex_msg)
                result["callsign"] = callsign
                result["ascii_callsign"] = [ord(c) for c in callsign]
            elif 9 <= tc <= 18:
                lat, lon = pms.adsb.airborne_position_with_ref(hex_msg, 0, 0)
                result["airborne_position"] = (lat, lon)
            elif 5 <= tc <= 8:
                alt = pms.adsb.altitude(hex_msg)
                result["altitude"] = alt
            elif 19 == tc:
                result["velocity"] = pms.adsb.velocity(hex_msg)
            else:
                result["info"] = f"Valid extended squitter but typecode not handled."
        elif df in [4, 20]:  # Surveillance, Altitude
            result["icao"] = pms.common.icao(hex_msg)
            result["altitude"] = pms.common.altcode(hex_msg)
        elif df in [5, 21]:  # Surveillance, Identity
            result["icao"] = pms.common.icao(hex_msg)
            result["identity"] = pms.common.idcode(hex_msg)
        elif df == 0:
            result["info"] = "Short Air-Air Surveillance (DF0)"
        elif df == 11:
            result.update({"icao": pms.common.icao(hex_msg), "info": "All-call reply (DF11)"})
        elif df == 24:
            result["info"] = "DF24: Comm-B Extended Squitter"
        else:
            result["info"] = f"Unknown or unhandled DF type: {df}"
    except Exception as e:
        result["error"] = f"Decoding failed: {e}"
    return result


def read_from_dump1090(host="localhost", port=30002, max_msgs=10):
    print("Trying to read ADS-B messages from dump1090...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Connected to dump1090 at {host}:{port}\n")
        count = 0
        while count < max_msgs:
            raw = s.recv(1024).decode("utf-8", errors="ignore").strip()
            lines = raw.split("\n")
            for msg in lines:
                if msg.startswith("*") and msg.endswith(";"):
                    hex_msg = msg[1:-1]
                    decoded = decode_adsb(hex_msg)
                    print(f"\nRaw Hex: {hex_msg}")
                    for k, v in decoded.items():
                        print(f"  {k}: {v}")
                    print("-" * 40)
                    count += 1
                    if count >= max_msgs:
                        break
        s.close()
        return True
    except Exception as e:
        print(f"Could not connect to dump1090: {e}")
        return False


def fetch_from_opensky():
    print("\nUsing OpenSky Network fallback...\n")
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        response.raise_for_status()
        data = response.json()
        states = data.get("states", [])

        print(f"Total aircraft received: {len(states)}\n")
        for state in states:
            icao24 = state[0]
            callsign = state[1].strip() if state[1] else "N/A"
            country = state[2] or "N/A"
            altitude = round(state[7], 2) if state[7] else "N/A"
            velocity = round(state[9], 2) if state[9] else "N/A"
            ascii_callsign = [ord(c) for c in callsign] if callsign != "N/A" else []

            print(f"ICAO: {icao24} | Callsign: {callsign} | ASCII: {ascii_callsign} | Country: {country} | Altitude: {altitude} | Speed: {velocity}")

            # Simulate a DF17 packet from ICAO for additional decoding (optional)
            dummy_hex = f"8D{icao24.upper():<6}00000000000000000000"[:28]
            decoded = decode_adsb(dummy_hex)
            for k, v in decoded.items():
                print(f"  {k}: {v}")
            print("-" * 40)
    except requests.RequestException as e:
        print(f"OpenSky request failed: {e}")


if __name__ == "__main__":
    if not read_from_dump1090():
        fetch_from_opensky()
