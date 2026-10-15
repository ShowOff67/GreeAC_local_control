import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
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
    from greeclimate.enums import VerticalSwing, HorizontalSwing
except ImportError:
    try:
        from greeclimate.device import VerticalSwing, HorizontalSwing
    except ImportError:
        VerticalSwing = None
        HorizontalSwing = None

class PropWrapper:
    def __init__(self, v):
        self.value = v

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
HSWING_MAP = {
    "off": 0, "default": 0,
    "full": 1,
    "left": 2, "midleft": 3, "mid": 4, "midright": 5, "right": 6
}

MODE_NAMES = {0: "Auto", 1: "Cool", 2: "Dry", 3: "Fan"}
FAN_NAMES = {0: "Auto", 1: "Low", 2: "Med-Low", 3: "Medium", 4: "Med-High", 5: "High"}
SWING_NAMES = {
    0: "Off", 1: "Full Oscillation",
    2: "Ceiling (Top)", 3: "Mid-Up", 4: "Straight (Mid)",
    5: "Mid-Down", 6: "Floor (Down)"
}
HSWING_NAMES = {
    0: "Off", 1: "Full Oscillation",
    2: "Far Left", 3: "Mid-Left", 4: "Center",
    5: "Mid-Right", 6: "Far Right"
}

async def run(args):
    target_ip = args.ip or os.getenv("GREE_AC_IP")
    target_mac = args.mac or os.getenv("GREE_AC_MAC")

    if not target_ip or not target_mac:
        print("[-] Error: AC IP or MAC address missing.")
        print("[-] Set GREE_AC_IP and GREE_AC_MAC in your .env file or use --ip and --mac.")
        sys.exit(1)

    ac = Device(DeviceInfo(target_ip, 7000, target_mac, "Gree AC"))
    await ac.bind()

    # Read hardware clock & remote timer flags alongside standard status
    orig_encrypt = ac._cipher.encrypt
    orig_decrypt = ac._cipher.decrypt
    hw_meta = {"TmrOn": 0, "TmrOff": 0, "time": None}
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def custom_encrypt(data):
        if isinstance(data, dict):
            if data.get("t") == "status":
                cols = data.setdefault("cols", [])
                for k in ("TmrOn", "TmrOff", "time"):
                    if k not in cols:
                        cols.append(k)
            elif data.get("t") == "cmd":
                opt = data.setdefault("opt", [])
                p = data.setdefault("p", [])
                if args.sync_time and "time" not in opt:
                    opt.append("time")
                    p.append(now_str)
                if args.silent:
                    if "BuzzerCtrl" in opt:
                        p[opt.index("BuzzerCtrl")] = 0
                    else:
                        opt.append("BuzzerCtrl")
                        p.append(0)
        return orig_encrypt(data)

    def custom_decrypt(data):
        res = orig_decrypt(data)
        if isinstance(res, dict) and res.get("t") in ("dat", "res"):
            keys = res.get("cols") or res.get("opt") or []
            vals = res.get("dat") or res.get("p") or []
            cur = dict(zip(keys, vals))
            if "TmrOn" in cur: hw_meta["TmrOn"] = cur["TmrOn"]
            if "TmrOff" in cur: hw_meta["TmrOff"] = cur["TmrOff"]
            if "time" in cur: hw_meta["time"] = cur["time"]
        return res

    ac._cipher.encrypt = custom_encrypt
    ac._cipher.decrypt = custom_decrypt

    # Fast state sync (~45ms)
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
            ac.set_property(PropWrapper("SwUpDn"), target_swing_val)
        changed = True

    # 13. Horizontal Louver Angle / Swing (Left-Right)
    if args.hswing is not None and args.hswing.lower() in HSWING_MAP:
        target_hswing_val = HSWING_MAP[args.hswing.lower()]
        if hasattr(ac, "horizontal_swing") and HorizontalSwing:
            ac.horizontal_swing = HorizontalSwing(target_hswing_val)
        else:
            ac.set_property(PropWrapper("SwingLfRig"), target_hswing_val)
        changed = True

    # 14. Sync Internal Hardware Clock
    if args.sync_time:
        # Touch a known property so greeclimate dispatches the cmd packet
        ac.light = ac.light
        ac._dirty.append("Lig")
        changed = True

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

    current_hswing_val = getattr(getattr(ac, "horizontal_swing", None), "value", props.get("SwingLfRig", 0))
    hswing_str = HSWING_NAMES.get(current_hswing_val, str(current_hswing_val))

    filter_dirty = props.get("Dfltr", 0) == 1
    mode_str = MODE_NAMES.get(ac.mode, str(ac.mode))
    fan_str = "Turbo" if ac.turbo else ("Quiet" if ac.quiet else FAN_NAMES.get(ac.fan_speed, str(ac.fan_speed)))

    ir_timers = []
    if hw_meta.get("TmrOn"): ir_timers.append("ON-Timer")
    if hw_meta.get("TmrOff"): ir_timers.append("OFF-Timer")
    ir_timer_str = ", ".join(ir_timers) if ir_timers else "OFF"

    ac_clock_raw = hw_meta.get("time")
    if ac_clock_raw:
        try:
            dt = datetime.strptime(ac_clock_raw, "%Y-%m-%d %H:%M:%S")
            clock_str = f"{dt.strftime('%H:%M:%S')} ({dt.strftime('%I:%M %p')})"
        except ValueError:
            clock_str = str(ac_clock_raw)[:32]
    else:
        clock_str = "N/A"

    print("┌──────────────────────────────────────────────┐")
    print(f"│ AC Power   : {'[ ON ]' if ac.power else '[ OFF ]':<32}│")
    print(f"│ Target     : {str(ac.target_temperature) + '°C':<32}│")
    print(f"│ Room Temp  : {room_temp:<32}│")
    print(f"│ Mode / Fan : {(mode_str + ' / ' + fan_str):<32}│")
    print(f"│ V-Swing    : {swing_str:<32}│")
    print(f"│ H-Swing    : {hswing_str:<32}│")
    print(f"│ SE / Sleep : {('ON' if ac.power_save else 'OFF') + ' / ' + ('ON' if ac.sleep else 'OFF'):<32}│")
    print(f"│ X-Fan / Ion: {('ON' if ac.xfan else 'OFF') + ' / ' + ('ON' if ac.anion else 'OFF'):<32}│")
    print(f"│ Panel LED  : {('ON' if ac.light else 'OFF'):<32}│")
    print(f"│ IR Timer   : {ir_timer_str:<32}│")
    print(f"│ AC Clock   : {clock_str:<32}│")
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
    parser.add_argument("--swing", choices=["off", "full", "up", "midup", "mid", "middown", "down"], help="Vertical louver position")
    parser.add_argument("--hswing", choices=["off", "full", "left", "midleft", "mid", "midright", "right"], help="Horizontal louver position")
    parser.add_argument("--sync-time", action="store_true", help="Sync AC internal clock with Linux PC time")
    parser.add_argument("--silent", action="store_true", help="Send command without beeping")

    asyncio.run(run(parser.parse_args()))