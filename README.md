# Gree AC Local Controller (CLI)

A lightweight, high-performance, cloud-free local UDP controller for Gree Smart Air Conditioners (supporting both `CipherV1` and newer `CipherV2` / firmware V1.23+ modules). 

Controls your AC directly across your local Wi-Fi network with zero reliance on cloud servers or the official mobile app.

---

## Features

- **Instant Execution**: Sub-second local UDP dispatch without network scanning delays.
- **Hardware-Level Feature Support**:
  - Power ON / OFF
  - Target temperature control (16°C – 30°C)
  - Operating modes: `cool`, `auto`, `dry`, `fan`
  - Multi-speed fan control: `auto`, `low`, `medlow`, `medium`, `medhigh`, `high`
  - **Turbo Cooling** toggle
  - **Energy Saving ("SE" Mode)** without remote key combos
  - **X-Fan** (Auto-drying feature to prevent indoor coil mold/mildew)
  - **Health Mode** (Cold Plasma Ionizer)
  - **Quiet Mode** (Ultra-low night fan profile)
  - **Display Panel LED Light** toggle
  - **Sleep Mode** profile
  - **Motorized Louver Positioning / Swing**: Continuous oscillation or fixed angles (`up`, `midup`, `mid`, `middown`, `down`)
  - **Silent Commands**: Mute the remote confirmation chime (`--silent`)
  - Live ambient room temperature reading from the indoor sensor
  - Air filter cleaning status indicator

---


## 1. Finding Your AC's IP & MAC Address

Your AC must already be paired to your Wi-Fi router. You can locate its IP and MAC using either method below:

### Method A: Using the built-in Discovery Script (Easiest)
Run `debug_ac.py` without any configuration. It broadcasts on UDP port 7000 and automatically detects your unit:
```bash
python debug_ac.py
```
Look for the output line:

[+] Connected to AC: 192.168.1.xx (MAC: xx3x3x9x3bxx)

### Method B: Using arp-scan on Linux
```bash
sudo arp-scan --localnet
```
Look for entries under the vendor "GREE ELECTRIC APPLIANCES, INC." or "Espressif Inc.":

## 2. Installation & Setup

### Step 1: Clone the Repository
```bash
git clone [https://github.com/ShowOff67/GreeAC_local_control.git](https://github.com/ShowOff67/GreeAC_local_control.git)
cd GreeAC_local_control
```

Step 2: Set Up Virtual Environment & Dependencies
Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Windows (Command Prompt / PowerShell):

```DOS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Step 3: Configure Device Details
Copy the example environment file:

```bash
cp .env.example .env
```
On Windows Command Prompt, use
```DOS
copy .env.example .env
```
Open .env and fill in your device's IP and MAC address:

## 3. Usage & Command Reference

Make sure your virtual environment is active (`source venv/bin/activate` on linux or `venv\Scripts\activate` on Windows).

### Status Query
Check current status and ambient room temperature without modifying anything:
```bash
python ac.py
```

----------------------------------------------------------------------------------------------------------------------


Power Control
```bash
# Turn ON (Cool mode, 24°C, Auto Fan)
python ac.py --power on --mode cool --temp 24 --fan auto

# Turn OFF
python ac.py --power off
```
Temperature & Fan Control
```bash
# Set specific temperature
python ac.py --temp 22

# Set specific fan speed
python ac.py --fan high

# Enable Turbo Cooling
python ac.py --turbo on
```
Advanced Modes
```bash
# Enable Energy Saving (SE) mode
python ac.py --se on
python ac.py --se off

# Enable X-Fan (coil drying to prevent mildew)
python ac.py --xfan on

# Enable Health Mode (Cold Plasma Ionizer)
python ac.py --health on

# Enable Ultra-Quiet night profile
python ac.py --quiet on

# Toggle front panel display LED
python ac.py --light off
python ac.py --light on
```
Louver Direction & Vertical Swing
```bash
# Continuous vertical oscillation
python ac.py --swing full

# Fixed angle: direct airflow toward the ceiling
python ac.py --swing up

# Fixed angle: straight ahead (mid-level)
python ac.py --swing mid

# Fixed angle: direct airflow toward the floor
python ac.py --swing down

# Stop oscillation / return to default position
python ac.py --swing off
```
Silent Execution (No Chime)
Add --silent to any command to prevent the indoor unit from beeping:

```bash
python ac.py --power on --temp 25 --silent
```

## 4. Parameter Cheat Sheet

| Parameter | Values / Options | Description |
|---|---|---|
| `--power` | `on`, `off` | Power state |
| `--temp` | `16` – `30` | Target temperature in °C |
| `--mode` | `cool`, `auto`, `dry`, `fan` | Operating mode |
| `--fan` | `auto`, `low`, `medlow`, `medium`, `medhigh`, `high` | Fan blower speed |
| `--turbo` | `on`, `off` | Maximum rapid cooling |
| `--se` | `on`, `off` | Energy Saving (SE) limit mode |
| `--xfan` | `on`, `off` | Blower runs after shutdown to dry coils |
| `--health`| `on`, `off` | Cold plasma ionizer |
| `--quiet` | `on`, `off` | Ultra-quiet night fan profile |
| `--light` | `on`, `off` | Front panel LED display |
| `--sleep` | `on`, `off` | Night sleep curve |
| `--swing` | `off`, `full`, `up`, `midup`, `mid`, `middown`, `down` | Louver angle / oscillation |
| `--silent`| *(flag, no argument)* | Mutes the confirmation chime |
| `--ip` | `<IP_ADDRESS>` | Overrides IP from `.env` |
| `--mac`| `<MAC_ADDRESS>` | Overrides MAC from `.env` |

---

## 5. Troubleshooting & Diagnostics

If you need detailed logs or automatic network discovery, use `debug_ac.py`:

```bash
# Auto-scan subnet and inspect live handshake & status
python debug_ac.py
```
```
# Send command with full packet logging
python debug_ac.py --power on --temp 24
```

Common Issues
Command hangs / Device not found:

1. Ensure your computer and the AC unit are connected to the exact same local Wi-Fi subnet.

2. Check your Wi-Fi router settings and ensure "AP Isolation" / "Client Isolation" is disabled, as this setting prevents Wi-Fi clients from communicating locally with each other.

3. Firewall / Port Blocking:
Ensure your operating system's firewall permits incoming and outgoing traffic on UDP port 7000.

Multiple ACs on the Same Network:

Use the --ip and --mac flags to target specific units individually without needing to modify your .env configuration file.
