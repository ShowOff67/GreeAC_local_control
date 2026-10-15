# Gree AC CLI Control Commands

Complete list of working CLI control commands for `ac.py`.

---

## 1. Live Status Check & Clock Sync
```bash
# View live AC status (Power, Target/Room Temp, Louvers, Modes, IR Timer status, and AC Clock)
python ac.py

# Sync the AC's internal hardware clock with your Linux PC clock
python ac.py --sync-time
```

## 2. Power & Mode Control
```bash
# Turn ON with Cool mode, 24°C, and Auto Fan
python ac.py --power on --mode cool --temp 24 --fan auto

# Turn OFF
python ac.py --power off

# Switch operating modes (cool, auto, dry, fan)
python ac.py --mode cool
python ac.py --mode dry
python ac.py --mode fan
python ac.py --mode auto
```

## 3. Temperature & Fan Speed Control
```bash
# Set target temperature (16°C to 30°C)
python ac.py --temp 25

# Set fan speeds (auto, low, medlow, medium, medhigh, high)
python ac.py --fan auto
python ac.py --fan low
python ac.py --fan medlow
python ac.py --fan medium
python ac.py --fan medhigh
python ac.py --fan high

# Enable or disable Turbo cooling
python ac.py --turbo on
python ac.py --turbo off
```

## 4. Advanced Features & Night Profiles
```bash
# Energy Saving (SE) mode
python ac.py --se on
python ac.py --se off

# X-Fan (auto coil drying after power-off to prevent mold)
python ac.py --xfan on
python ac.py --xfan off

# Health mode (Cold Plasma Ionizer)
python ac.py --health on
python ac.py --health off

# Ultra-Quiet mode
python ac.py --quiet on
python ac.py --quiet off

# Night Sleep Curve mode
python ac.py --sleep on
python ac.py --sleep off

# Toggle the indoor unit's front LED display light
python ac.py --light on
python ac.py --light off
```

## 5. Vertical & Horizontal Louver Swing
```bash
# Vertical Swing (Up / Down)
python ac.py --swing full      # Full vertical oscillation
python ac.py --swing up        # Fixed toward ceiling
python ac.py --swing midup     # Fixed upper-middle
python ac.py --swing mid       # Fixed straight ahead
python ac.py --swing middown   # Fixed lower-middle
python ac.py --swing down      # Fixed toward floor
python ac.py --swing off       # Stop oscillation

# Horizontal Swing (Left / Right)
python ac.py --hswing full     # Full left-to-right oscillation
python ac.py --hswing left     # Fixed far left
python ac.py --hswing midleft  # Fixed mid-left
python ac.py --hswing mid      # Fixed center
python ac.py --hswing midright # Fixed mid-right
python ac.py --hswing right    # Fixed far right
python ac.py --hswing off      # Stop horizontal oscillation
```

## 6. Silent Execution (Mute AC Beep)
```bash
# Append --silent to any command to prevent the AC from beeping
python ac.py --power on --temp 24 --se on --silent
python ac.py --light off --silent
```