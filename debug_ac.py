import os
import asyncio
import argparse
from pathlib import Path

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

from greeclimate.discovery import Discovery
from greeclimate.device import Device, Mode, FanSpeed

# Friendly lookup dictionaries
MODE_NAMES = {0: "Auto", 1: "Cool", 2: "Dry", 3: "Fan", 4: "Heat"}
FAN_NAMES = {0: "Auto", 1: "Low", 2: "Med-Low", 3: "Medium", 4: "Med-High", 5: "High"}

def format_mode(val):
    if val is None:
        return "Unknown"
    if hasattr(val, "name"):
        return val.name
    return MODE_NAMES.get(val, str(val))

def format_fan(val):
    if val is None:
        return "Unknown"
    if hasattr(val, "name"):
        return val.name
    return FAN_NAMES.get(val, str(val))

async def control_ac(args):
    target_ip = args.ip or os.getenv("GREE_AC_IP")

    discovery = Discovery()
    print("[*] Scanning local network on UDP 7000...")
    devices = await discovery.scan(wait_for=2)

    if not devices:
        print("[-] No Gree AC devices found on this subnet.")
        return

    target = None
    if target_ip:
        for dev in devices:
            if getattr(dev, "ip", None) == target_ip:
                target = dev
                break

    # If no IP was specified or matched, default to the first discovered unit
    if not target:
        target = devices[0]
        print(f"[i] Using auto-detected AC at {target.ip}")

    print(f"[+] Connected to AC: {target.ip} (MAC: {target.mac})")
    ac = Device(target)

    print("[*] Performing CipherV2 binding and fetching state...")
    await ac.bind()
    await asyncio.sleep(0.3)
    await ac.update_state()
    await asyncio.sleep(0.3)

    print(f"[i] Live State -> Power: {'ON' if ac.power else 'OFF'} | Temp: {ac.target_temperature}°C | Mode: {format_mode(ac.mode)} | Fan: {format_fan(ac.fan_speed)} | Light: {'ON' if ac.light else 'OFF'}")

    changed = False

    # Power
    if args.power is not None:
        ac.power = (args.power.lower() == "on")
        changed = True

    # Target Temperature
    if args.temp is not None:
        ac.target_temperature = int(args.temp)
        changed = True

    # Mode
    if args.mode is not None:
        mode_map = {
            "auto": Mode.Auto,
            "cool": Mode.Cool,
            "dry": Mode.Dry,
            "fan": Mode.Fan,
            "heat": Mode.Heat
        }
        if args.mode.lower() in mode_map:
            ac.mode = mode_map[args.mode.lower()]
            changed = True

    # Fan Speed & Turbo
    if args.fan is not None:
        fan_choice = args.fan.lower()
        if fan_choice == "turbo":
            ac.turbo = True
            changed = True
        else:
            fan_map = {
                "auto": FanSpeed.Auto,
                "low": FanSpeed.Low,
                "medlow": FanSpeed.MediumLow,
                "medium": FanSpeed.Medium,
                "medhigh": FanSpeed.MediumHigh,
                "high": FanSpeed.High
            }
            if fan_choice in fan_map:
                ac.fan_speed = fan_map[fan_choice]
                ac.turbo = False
                changed = True

    # Keep display light illuminated when running
    if ac.power:
        ac.light = True

    if changed:
        print(f"[*] Sending update -> Power={'ON' if ac.power else 'OFF'}, Temp={ac.target_temperature}°C, Mode={format_mode(ac.mode)}, Fan={format_fan(ac.fan_speed)}...")
        await ac.push_state_update()
        await asyncio.sleep(1.5)
        print("[+] Done! Command delivered.")
    else:
        print("[i] No modifications requested.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gree AC Discovery & Debug Controller")
    parser.add_argument("--ip", help="Target AC IP address (overrides .env)")
    parser.add_argument("--power", choices=["on", "off"], help="Turn AC on or off")
    parser.add_argument("--temp", type=int, help="Target temperature in Celsius (16-30)")
    parser.add_argument("--mode", choices=["cool", "heat", "dry", "fan", "auto"], help="Operation mode")
    parser.add_argument("--fan", choices=["auto", "low", "medlow", "medium", "medhigh", "high", "turbo"], help="Fan speed")

    args = parser.parse_args()
    asyncio.run(control_ac(args))
