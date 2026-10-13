import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Silence background library logging
logging.disable(logging.CRITICAL)

# Load .env file
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
from greeclimate.discovery import DeviceInfo
from greeclimate.device import Device, Mode, FanSpeed
from greeclimate.cipher import CipherV2

# Bypass 5-second CipherV1 fallback delay
greeclimate.device.CipherV1 = CipherV2

try:
    from greeclimate.enums import VerticalSwing
except ImportError:
    try:
        from greeclimate.device import VerticalSwing
    except ImportError:
        VerticalSwing = None

MODE_MAP = {"auto": Mode.Auto, "cool": Mode.Cool, "dry": Mode.Dry, "fan": Mode.Fan}
FAN_MAP = {
    "auto": FanSpeed.Auto,
    "low": FanSpeed.Low,
    "medlow": FanSpeed.MediumLow,
    "medium": FanSpeed.Medium,
    "medhigh": FanSpeed.MediumHigh,
    "high": FanSpeed.High
}
SWING_MAP = {
    "off": 0, "default": 0,
    "full": 1,
    "up": 2, "midup": 3, "mid": 4, "middown": 5, "down": 6
}

MODE_NAMES = {0: "Auto", 1: "Cool", 2: "Dry", 3: "Fan"}
FAN_NAMES = {0: "Auto", 1: "Low", 2: "Med-Low", 3: "Medium", 4: "Med-High", 5: "High"}
SWING_NAMES = {
    0: "Off", 1: "Full Oscillation",
    2: "Ceiling (Top)", 3: "Mid-Up", 4: "Straight (Mid)",
    5: "Mid-Down", 6: "Floor (Down)"
}

async def run(args):
    target_ip = args.ip or os.getenv("GREE_AC_IP")
    target_mac = args.mac or os.getenv("GREE_AC_MAC")

    if not target_ip or not target_mac:
        print("[-] Error: AC IP or MAC address missing.")
        print("[-] Set GREE_AC_IP and GREE_AC_MAC in your .env file or use --ip and --mac.")
        sys.exit(1)

    ac = Device(DeviceInfo(target_ip, 7000, target_mac, "Gree AC"))

    # Direct bind & fast state sync (~45ms)
    await ac.bind()
    await ac.update_state()
    for _ in range(50):
        if ac.target_temperature is not None:
            break
        await asyncio.sleep(0.01)

    changed = False

    # 1. Power
    if args.power is not None:
        ac.power = (args.power.lower() == "on")
        changed = True

    # 2. Temperature (16 - 30 C)
    if args.temp is not None:
        ac.target_temperature = int(args.temp)
        changed = True

    # 3. Mode (Cool, Auto, Dry, Fan)
    if args.mode is not None and args.mode.lower() in MODE_MAP:
        ac.mode = MODE_MAP[args.mode.lower()]
        changed = True

    # 4. Fan Speed
    if args.fan is not None and args.fan.lower() in FAN_MAP:
        ac.fan_speed = FAN_MAP[args.fan.lower()]
        ac.turbo = False
        changed = True

    # 5. Turbo Cooling
    if args.turbo is not None:
        ac.turbo = (args.turbo.lower() == "on")
        changed = True

    # 6. SE (Energy Saving) Mode
    if args.se is not None:
        ac.power_save = (args.se.lower() == "on")
        changed = True

    # 7. X-Fan (Auto coil-drying mold prevention)
    if args.xfan is not None:
        ac.xfan = (args.xfan.lower() == "on")
        changed = True

    # 8. Health (Cold Plasma Ionizer)
    if args.health is not None:
        ac.anion = (args.health.lower() == "on")
        changed = True

    # 9. Quiet Night Mode
    if args.quiet is not None:
        ac.quiet = (args.quiet.lower() == "on")
        changed = True

    # 10. Display Panel LED Light
    if args.light is not None:
        ac.light = (args.light.lower() == "on")
        changed = True

    # 11. Sleep Curve Mode
    if args.sleep is not None:
        ac.sleep = (args.sleep.lower() == "on")
        changed = True

    # 12. Vertical Louver Angle / Swing
    if args.swing is not None and args.swing.lower() in SWING_MAP:
        target_swing_val = SWING_MAP[args.swing.lower()]
        if hasattr(ac, "vertical_swing") and VerticalSwing:
            ac.vertical_swing = VerticalSwing(target_swing_val)
        else:
            class PropWrapper:
                def __init__(self, v): self.value = v
            ac.set_property(PropWrapper("SwUpDn"), target_swing_val)
        changed = True

    # 13. Silent Execution (Mute remote confirmation chime)
    if args.silent:
        orig_encrypt = ac._cipher.encrypt
        def mute_encrypt(data):
            if isinstance(data, dict) and data.get("t") == "cmd":
                opt = data.setdefault("opt", [])
                p = data.setdefault("p", [])
                if "BuzzerCtrl" in opt:
                    p[opt.index("BuzzerCtrl")] = 0
                else:
                    opt.append("BuzzerCtrl")
                    p.append(0)
            return orig_encrypt(data)
        ac._cipher.encrypt = mute_encrypt

    # Dispatch updates to AC
    if changed:
        await ac.push_state_update()
        await asyncio.sleep(0.35)

    # Read live status values
    props = getattr(ac, "_properties", {}) or {}
    room_temp = getattr(ac, "current_temperature", None)
    if room_temp is None:
        room_temp = str(props.get("TemSen", 71) - 40) + "°C" if "TemSen" in props else "N/A"
    else:
        room_temp = f"{room_temp}°C"

    current_swing_val = getattr(getattr(ac, "vertical_swing", None), "value", props.get("SwUpDn", 0))
    swing_str = SWING_NAMES.get(current_swing_val, str(current_swing_val))
    filter_dirty = props.get("Dfltr", 0) == 1
    mode_str = MODE_NAMES.get(ac.mode, str(ac.mode))
    fan_str = "Turbo" if ac.turbo else FAN_NAMES.get(ac.fan_speed, str(ac.fan_speed))

    print("┌──────────────────────────────────────────────┐")
    print(f"│ AC Power   : {'[ ON ]' if ac.power else '[ OFF ]':<32}│")
    print(f"│ Target     : {str(ac.target_temperature) + '°C':<32}│")
    print(f"│ Room Temp  : {room_temp:<32}│")
    print(f"│ Mode / Fan : {(mode_str + ' / ' + fan_str):<32}│")
    print(f"│ Swing Vane : {swing_str:<32}│")
    print(f"│ SE Energy  : {('ON' if ac.power_save else 'OFF'):<32}│")
    print(f"│ X-Fan / Ion: {('ON' if ac.xfan else 'OFF') + ' / ' + ('ON' if ac.anion else 'OFF'):<32}│")
    print(f"│ Panel LED  : {('ON' if ac.light else 'OFF'):<32}│")
    if filter_dirty:
        print("│ Warning    : [!] AIR FILTER NEEDS CLEANING   │")
    print("└──────────────────────────────────────────────┘")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gree AC Local Control CLI")
    parser.add_argument("--ip", help="AC IP address (overrides .env)")
    parser.add_argument("--mac", help="AC MAC address (overrides .env)")
    parser.add_argument("--power", choices=["on", "off"], help="AC Power state")
    parser.add_argument("--temp", type=int, help="Target temperature (16-30°C)")
    parser.add_argument("--mode", choices=["cool", "auto", "dry", "fan"], help="AC Mode")
    parser.add_argument("--fan", choices=["auto", "low", "medlow", "medium", "medhigh", "high"], help="Fan speed")
    parser.add_argument("--turbo", choices=["on", "off"], help="Turbo maximum cooling")
    parser.add_argument("--se", choices=["on", "off"], help="Energy Saving (SE) mode")
    parser.add_argument("--xfan", choices=["on", "off"], help="X-Fan coil drying")
    parser.add_argument("--health", choices=["on", "off"], help="Cold plasma ionizer")
    parser.add_argument("--quiet", choices=["on", "off"], help="Ultra-quiet mode")
    parser.add_argument("--light", choices=["on", "off"], help="Front panel display LED")
    parser.add_argument("--sleep", choices=["on", "off"], help="Night sleep mode")
    parser.add_argument("--swing", choices=["off", "full", "up", "midup", "mid", "middown", "down"], help="Louver position")
    parser.add_argument("--silent", action="store_true", help="Send command without beeping")
    
    asyncio.run(run(parser.parse_args()))
