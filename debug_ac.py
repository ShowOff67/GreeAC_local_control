import os
import asyncio
import argparse
import logging
from pathlib import Path

# Silence noisy background library logs in favor of clean packet output
logging.disable(logging.CRITICAL)

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import greeclimate.device
from greeclimate.discovery import Discovery, DeviceInfo
from greeclimate.device import Device, Mode, FanSpeed
from greeclimate.cipher import CipherV2

# Bypass 5-second CipherV1 fallback delay
greeclimate.device.CipherV1 = CipherV2

MODE_MAP = {"auto": Mode.Auto, "cool": Mode.Cool, "dry": Mode.Dry, "fan": Mode.Fan}
FAN_MAP = {
    "auto": FanSpeed.Auto,
    "low": FanSpeed.Low,
    "medlow": FanSpeed.MediumLow,
    "medium": FanSpeed.Medium,
    "medhigh": FanSpeed.MediumHigh,
    "high": FanSpeed.High
}

MODE_NAMES = {0: "Auto", 1: "Cool", 2: "Dry", 3: "Fan"}
FAN_NAMES = {0: "Auto", 1: "Low", 2: "Med-Low", 3: "Medium", 4: "Med-High", 5: "High"}

def format_mode(val):
    if val is None:
        return "Unknown"
    return MODE_NAMES.get(val, getattr(val, "name", str(val)))

def format_fan(val, turbo=False):
    if turbo:
        return "Turbo"
    if val is None:
        return "Unknown"
    return FAN_NAMES.get(val, getattr(val, "name", str(val)))

async def control_ac(args):
    target_ip = args.ip or os.getenv("GREE_AC_IP")
    target_mac = args.mac or os.getenv("GREE_AC_MAC")

    print("[*] Scanning local network on UDP port 7000...")
    discovery = Discovery()
    devices = await discovery.scan(wait_for=2)

    target = None
    if devices:
        for dev in devices:
            print(f"[+] Discovered AC -> IP: {dev.ip} | MAC: {dev.mac} | Name: {getattr(dev, 'name', 'Gree AC')}")
            if target_ip and getattr(dev, "ip", None) == target_ip:
                target = dev
        if not target:
            target = devices[0]
    elif target_ip and target_mac:
        print("[!] Broadcast scan returned no reply; falling back to direct IP/MAC from .env...")
        target = DeviceInfo(target_ip, 7000, target_mac, "Gree AC")
    else:
        print("[-] No Gree AC devices found on this subnet.")
        return

    print(f"[+] Connected to AC: {target.ip} (MAC: {target.mac})")
    print(f"    (.env config -> GREE_AC_IP={target.ip} | GREE_AC_MAC={target.mac})\n")

    ac = Device(target)

    print("[*] Performing CipherV2 handshake...")
    await ac.bind()

    # Attach packet logger to inspect live JSON payloads
    orig_encrypt = ac._cipher.encrypt
    orig_decrypt = ac._cipher.decrypt

    def debug_encrypt(data):
        print(f"  [TX -> AC] {data}")
        return orig_encrypt(data)

    def debug_decrypt(data):
        res = orig_decrypt(data)
        print(f"  [RX <- AC] {res}")
        return res

    ac._cipher.encrypt = debug_encrypt
    ac._cipher.decrypt = debug_decrypt

    print("[*] Fetching live status packet...")
    await ac.update_state()
    for _ in range(50):
        if ac.target_temperature is not None:
            break
        await asyncio.sleep(0.01)

    props = getattr(ac, "_properties", {}) or {}
    room_temp = getattr(ac, "current_temperature", None)
    if room_temp is None and "TemSen" in props:
        room_temp = props["TemSen"] - 40

    print(
        f"\n[i] Live State -> Power: {'ON' if ac.power else 'OFF'} | "
        f"Target: {ac.target_temperature}°C | Room: {room_temp}°C | "
        f"Mode: {format_mode(ac.mode)} | Fan: {format_fan(ac.fan_speed, ac.turbo)} | "
        f"Light: {'ON' if ac.light else 'OFF'} | Firmware: {props.get('hid', 'Unknown')}"
    )

    changed = False

    if args.power is not None:
        ac.power = (args.power.lower() == "on")
        changed = True

    if args.temp is not None:
        ac.target_temperature = int(args.temp)
        changed = True

    if args.mode is not None and args.mode.lower() in MODE_MAP:
        ac.mode = MODE_MAP[args.mode.lower()]
        changed = True

    if args.fan is not None:
        fan_choice = args.fan.lower()
        if fan_choice == "turbo":
            ac.turbo = True
            changed = True
        elif fan_choice in FAN_MAP:
            ac.fan_speed = FAN_MAP[fan_choice]
            ac.turbo = False
            changed = True

    if args.light is not None:
        ac.light = (args.light.lower() == "on")
        changed = True

    if changed:
        print(
            f"\n[*] Dispatching update -> Power={'ON' if ac.power else 'OFF'}, "
            f"Temp={ac.target_temperature}°C, Mode={format_mode(ac.mode)}, "
            f"Fan={format_fan(ac.fan_speed, ac.turbo)}, Light={'ON' if ac.light else 'OFF'}..."
        )
        await ac.push_state_update()
        await asyncio.sleep(0.5)
        print("[+] Done! Command delivered and acknowledged.")
    else:
        print("[i] No modifications requested (Discovery & Status check complete).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gree AC Discovery & Debug Controller")
    parser.add_argument("--ip", help="Target AC IP address (overrides .env)")
    parser.add_argument("--mac", help="Target AC MAC address (overrides .env)")
    parser.add_argument("--power", choices=["on", "off"], help="Turn AC on or off")
    parser.add_argument("--temp", type=int, help="Target temperature in Celsius (16-30)")
    parser.add_argument("--mode", choices=["cool", "dry", "fan", "auto"], help="Operation mode")
    parser.add_argument("--fan", choices=["auto", "low", "medlow", "medium", "medhigh", "high", "turbo"], help="Fan speed")
    parser.add_argument("--light", choices=["on", "off"], help="Front panel LED light")

    asyncio.run(control_ac(parser.parse_args()))