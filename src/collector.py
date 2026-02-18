import concurrent.futures
import pandas as pd
import logging
try:
    from .fmg_client import FMGClient
except ImportError:
    from fmg_client import FMGClient

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, fmg_url, username, password, verify_ssl=False, adom="root"):
        self.client = FMGClient(fmg_url, username, password, verify_ssl)
        self.adom = adom
        self.devices = []

    def fetch_all_data(self):
        """
        Connects to FMG, gets devices, and fetches detailed status for each.
        Returns a DataFrame.
        """
        if not self.client.login():
            logger.error("Failed to login to FMG")
            return pd.DataFrame()

        logger.info(f"Fetching managed devices for ADOM: {self.adom}...")
        self.devices = self.client.get_managed_devices(self.adom)
        logger.info(f"Found {len(self.devices)} devices.")

        results = []

        # Limit concurrency to avoid overwhelming FMG
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_device = {
                executor.submit(self.fetch_device_status, device): device
                for device in self.devices
            }

            for future in concurrent.futures.as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    data = future.result()
                    results.append(data)
                except Exception as exc:
                    logger.error(f"{device.get('name')} generated an exception: {exc}")
                    results.append({
                        "name": device.get("name"),
                        "serial": device.get("sn"),
                        "status": "Error",
                        "cpu": 0,
                        "mem": 0,
                        "switches_total": 0,
                        "switches_up": 0,
                        "aps_total": 0,
                        "aps_up": 0,
                        "details": f"Error: {exc}"
                    })

        self.client.logout()
        return pd.DataFrame(results)

    def fetch_device_status(self, device):
        """
        Fetches status for a single device.
        """
        name = device.get("name")
        serial = device.get("sn")

        # Default info from FMG list
        # 1=up usually
        fmg_status = "UP" if device.get("conn_status") == 1 else "DOWN"

        if fmg_status == "DOWN":
             return {
                "name": name,
                "serial": serial,
                "status": "DOWN",
                "cpu": 0,
                "mem": 0,
                "switches_total": 0,
                "switches_up": 0,
                "aps_total": 0,
                "aps_up": 0,
                "details": "Device disconnected from FMG"
            }

        # Fetch System, Switch, and AP Status in parallel
        # Optimization: Fetch these 3 independent resources concurrently to reduce wait time
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_sys = executor.submit(self.client.execute_device_command, name, "/api/v2/monitor/system/status")
            future_sw = executor.submit(self.client.execute_device_command, name, "/api/v2/monitor/switch-controller/managed-switch/status")
            future_ap = executor.submit(self.client.execute_device_command, name, "/api/v2/monitor/wifi/managed-ap")

            sys_status = future_sys.result()
            switch_status = future_sw.result()
            ap_status = future_ap.result()

        # Process System Status
        cpu = 0
        mem = 0
        if sys_status and isinstance(sys_status, dict):
            # Handle potential 'results' wrapper
            if 'results' in sys_status:
                stats = sys_status['results']
            else:
                stats = sys_status

            cpu = stats.get("cpu", 0)
            mem = stats.get("mem", 0)

        # Process Switch Status
        switches_total = 0
        switches_up = 0

        if switch_status:
            # Handle potential 'results' wrapper
            if isinstance(switch_status, dict) and 'results' in switch_status:
                switch_status = switch_status['results']

            if isinstance(switch_status, list):
                switches_total = len(switch_status)
                for sw in switch_status:
                    # Common keys for status: 'status', 'state'
                    # Values often: 'up', 'down', 'online', 'offline'
                    status = str(sw.get('status', '')).lower()
                    state = str(sw.get('state', '')).lower()
                    if status in ['up', 'online', 'connected'] or state in ['up', 'online', 'connected']:
                        switches_up += 1

        # Process AP Status
        aps_total = 0
        aps_up = 0
        if ap_status:
             # Handle potential 'results' wrapper
             if isinstance(ap_status, dict) and 'results' in ap_status:
                ap_status = ap_status['results']

             if isinstance(ap_status, list):
                aps_total = len(ap_status)
                for ap in ap_status:
                    # Common keys: 'status', 'connection_state'
                    status = str(ap.get('status', '')).lower()
                    conn_state = str(ap.get('connection_state', '')).lower()
                    # 'running' is also common for APs
                    if status in ['up', 'online', 'connected', 'running'] or conn_state in ['connected', 'online', 'running']:
                        aps_up += 1

        return {
            "name": name,
            "serial": serial,
            "status": "UP" if sys_status else "Unreachable",
            "cpu": cpu,
            "mem": mem,
            "switches_total": switches_total,
            "switches_up": switches_up,
            "aps_total": aps_total,
            "aps_up": aps_up,
            "details": f"Switches: {switches_up}/{switches_total} UP, APs: {aps_up}/{aps_total} UP"
        }
