# Network Experience Dashboard

This project is a Network Experience Dashboard designed to monitor and visualize the health of 260+ sites managed via FortiManager and ZDX.

It implements a **granular "Network Experience Score"** (0-100) by aggregating data from:
1.  **FortiManager (FMG)**: Uses **Proxy Tunnels** to connect to individual FortiGates and extract detailed WAN/LAN status (Interfaces, Switches, APs).
2.  **ZDX**: Scrapes raw performance metrics (Latency, Loss) from the ZDX portal (Standard Plan).
3.  **FortiAnalyzer (FAZ)**: Monitors critical system events.

## Features

-   **Proxy Tunnel Collection**: Bypasses the need for FMG API by automating the "Connect to Device" proxy feature to scrape granular data directly from the FortiGate GUI.
-   **Custom Scoring Engine**: Calculates experience scores based on weighted metrics (Latency vs Loss vs Device Availability).
-   **Streamlit Dashboard**: Real-time visualization with drill-down capabilities for troubleshooting.
-   **Mock Data Mode**: Generate realistic test scenarios for demonstration.

## Project Structure

-   `dashboard/`: Streamlit application code.
-   `collectors/`:
    -   `fmg_proxy_collector.py`: Automates FMG Login -> Device List -> Proxy Tunnel -> FGT Scrape.
    -   `zdx_scraper.py`: Scrapes ZDX for latency/loss metrics.
    -   `faz_scraper.py`: Checks for critical events.
-   `analysis/`: Scoring logic implementation.
-   `database/`: SQLite database schema.
-   `utils/`: Mock data generation.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo_url>
    cd network-experience-dashboard
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers**:
    ```bash
    playwright install chromium
    ```

## Usage

### 1. Run with Mock Data (Testing)

To quickly see the dashboard in action with generated data:

```bash
# Initialize DB and Generate Mock Data
python3 main.py --mode mock --init-db

# Launch Dashboard
streamlit run dashboard/app.py
```

### 2. Run with Real Data (Production)

**Step 1: Configure Collectors**
-   Edit `collectors/fmg_proxy_collector.py`:
    -   Update `FMG_URL` (e.g., `https://10.1.1.1`).
    -   Update `_login_fmg` selectors if your login page differs.
    -   **Important**: Verify the `_collect_via_proxy` logic. The script assumes it can navigate to the "Network > Interfaces" or "Dashboard" page of the *FortiGate* once inside the proxy tunnel. You may need to inspect the HTML of your specific firmware version.
-   Edit `collectors/zdx_scraper.py`: Update credentials and table selectors.

**Step 2: Enable Real Mode**
Edit `main.py` to uncomment the collector execution lines and run:

```bash
python3 main.py --mode real
```

**Step 3: View Dashboard**
```bash
streamlit run dashboard/app.py
```

## How the FMG Proxy Collector Works

Since direct API access is unavailable or restricted:
1.  The script logs into the FortiManager Web UI.
2.  It scrapes the list of devices (or uses a provided list).
3.  It constructs a **Proxy URL** for each device (typically `https://<fmg_ip>/p/firewall/<device_name>/`).
4.  It opens this URL, which tunnels the browser session to the FortiGate's own GUI.
5.  It then scrapes the specific status widgets (e.g., Interface Status, SD-WAN Monitor) from the FortiGate's page to get granular data that isn't easily available on the high-level FMG dashboard.

## Customization

-   **Scoring Logic**: Modify `analysis/scoring.py` to adjust weights.
-   **Dashboard**: Edit `dashboard/app.py` to add new charts.
