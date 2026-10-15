# Gree AC Local Controller (CLI)

A lightweight, high-performance, cloud-free local UDP controller for Gree Smart Air Conditioners (supporting both `CipherV1` and newer `CipherV2` / firmware V1.23+ modules)[cite: 1].

Controls your AC directly across your local Wi-Fi network with zero reliance on cloud servers or the official mobile app[cite: 1].

---

## Features

- **Instant Execution**: Sub-second local UDP dispatch without network scanning delays[cite: 1].
- **Hardware-Level Feature Support**:
  - Power ON / OFF[cite: 1]
  - Target temperature control (16°C – 30°C)[cite: 1]
  - Operating modes: `cool`, `auto`, `dry`, `fan`[cite: 1]
  - Multi-speed fan control: `auto`, `low`, `medlow`, `medium`, `medhigh`, `high`[cite: 1]
  - **Turbo Cooling** toggle[cite: 1]
  - **Energy Saving ("SE" Mode)** without remote key combos[cite: 1]
  - **X-Fan** (Auto-drying feature to prevent indoor coil mold/mildew)[cite: 1]
  - **Health Mode** (Cold Plasma Ionizer)[cite: 1]
  - **Quiet Mode** (Ultra-low night fan profile)[cite: 1]
  - **Display Panel LED Light** toggle[cite: 1]
  - **Sleep Mode** profile[cite: 1]
  - **Vertical Louver Positioning / Swing**: Continuous oscillation or fixed angles (`up`, `midup`, `mid`, `middown`, `down`)[cite: 1]
  - **Horizontal Louver Positioning / Swing**: Continuous oscillation or fixed angles (`left`, `midleft`, `mid`, `midright`, `right`)
  - **Hardware Clock Sync**: Syncs the AC's internal Wi-Fi chip real-time clock with your PC (`--sync-time`)
  - **Silent Commands**: Mute the remote confirmation chime (`--silent`)[cite: 1]
  - Live ambient room temperature reading, IR timer status detection, and air filter cleaning indicator[cite: 1]

---

## 1. Finding Your AC's IP & MAC Address

Your AC must already be paired to your Wi-Fi router[cite: 1]. You can locate its IP and MAC address using either method below[cite: 1]:

### Method A: Using the Built-in Discovery Script (Easiest)
Run `debug_ac.py` without any configuration[cite: 1]. It broadcasts on UDP port `7000` and automatically detects your unit[cite: 1]:

```bash
python debug_ac.py
```

Look for the output line[cite: 1]:
```text
[+] Connected to AC: 192.168.1.xx (MAC: xx3x3x9x3bxx)
```

### Method B: Using `arp-scan` on Linux
```bash
sudo arp-scan --localnet
```
Look for entries under the vendor **"GREE ELECTRIC APPLIANCES, INC."** or **"Espressif Inc."**[cite: 1].

---

## 2. Installation & Setup

### Step 1: Clone the Repository
```bash
git clone [https://github.com/ShowOff67/GreeAC_local_control.git](https://github.com/ShowOff67/GreeAC_local_control.git)
cd GreeAC_local_control
```

### Step 2: Set Up Virtual Environment & Dependencies

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows (Command Prompt / PowerShell):**
```dos
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Device Details
Copy the example environment file[cite: 1]:

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows (Command Prompt):**
```dos
copy .env.example .env
```

Open `.env` in a text editor and fill in your AC's IP and MAC address[cite: 1]:
```ini
GREE_AC_IP=192.168.1.xx
GREE_AC_MAC=xx3x3x9x3bxx
```

---

## 3. Usage & Command Reference

Ensure your virtual environment is active (`source venv/bin/activate` on Linux/macOS or `venv\Scripts\activate` on Windows) before running commands[cite: 1].

👉 **[View the Complete Control Command Reference (`command.md`)](./command.md)**

---

## 4. Parameter Cheat Sheet

| Parameter | Values / Options | Description |
|---|---|---|
| `--power` | `on`, `off` | Power state[cite: 1] |
| `--temp` | `16` – `30` | Target temperature in °C[cite: 1] |
| `--mode` | `cool`, `auto`, `dry`, `fan` | Operating mode[cite: 1] |
| `--fan` | `auto`, `low`, `medlow`, `medium`, `medhigh`, `high` | Fan blower speed[cite: 1] |
| `--turbo` | `on`, `off` | Maximum rapid cooling[cite: 1] |
| `--se` | `on`, `off` | Energy Saving (SE) limit mode[cite: 1] |
| `--xfan` | `on`, `off` | Blower runs after shutdown to dry coils[cite: 1] |
| `--health` | `on`, `off` | Cold plasma ionizer[cite: 1] |
| `--quiet` | `on`, `off` | Ultra-quiet night fan profile[cite: 1] |
| `--light` | `on`, `off` | Front panel LED display[cite: 1] |
| `--sleep` | `on`, `off` | Night sleep curve[cite: 1] |
| `--swing` | `off`, `full`, `up`, `midup`, `mid`, `middown`, `down` | Vertical louver angle / oscillation[cite: 1] |
| `--hswing` | `off`, `full`, `left`, `midleft`, `mid`, `midright`, `right` | Horizontal louver angle / oscillation |
| `--sync-time` | *(flag, no argument)* | Syncs AC internal clock with PC time |
| `--silent` | *(flag, no argument)* | Mutes the confirmation chime[cite: 1] |
| `--ip` | `<IP_ADDRESS>` | Overrides IP from `.env`[cite: 1] |
| `--mac` | `<MAC_ADDRESS>` | Overrides MAC from `.env`[cite: 1] |

---

## 5. Troubleshooting & Diagnostics

If you need detailed packet logs or automatic network discovery, use `debug_ac.py`[cite: 1]:

```bash
# Auto-scan subnet and inspect live handshake & status
python debug_ac.py

# Send a command with full packet logging
python debug_ac.py --power on --temp 24
```

### Common Issues

1. **Command Hangs / Device Not Found:**
   - Ensure your computer and the AC unit are connected to the exact same local Wi-Fi subnet[cite: 1].
   - Check your Wi-Fi router settings and verify that **"AP Isolation" / "Client Isolation"** is disabled, as this prevents Wi-Fi clients from communicating locally with each other[cite: 1].
2. **Firewall / Port Blocking:**
   - Ensure your operating system's firewall permits incoming and outgoing traffic on **UDP port `7000`**[cite: 1].
3. **Multiple ACs on the Same Network:**
   - Use the `--ip` and `--mac` flags to target specific units individually without modifying your `.env` file[cite: 1].