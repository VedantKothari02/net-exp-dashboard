import time
from playwright.sync_api import sync_playwright
from database.db import get_session, SiteStatus
from datetime import datetime

class FMGProxyCollector:
    def __init__(self, fmg_url, fmg_user, fmg_pass, headless=True):
        self.fmg_url = fmg_url
        self.fmg_user = fmg_user
        self.fmg_pass = fmg_pass
        self.headless = headless

    def run(self):
        """
        Main execution method: Login to FMG -> Scrape Device List -> Iterate Devices via Proxy -> Update DB.
        """
        print(f"Starting FMG Proxy Collector for {self.fmg_url}...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            try:
                # 1. Login to FMG
                self._login_fmg(page)

                # 2. Get List of Devices (scrape device manager table)
                devices = self._get_device_list(page)

                # 3. Iterate Devices & Proxy Tunnel
                for device in devices:
                    try:
                        self._collect_via_proxy(context, device)
                    except Exception as e:
                        print(f"Error collecting data for device {device['name']}: {e}")

                print("FMG Proxy Collection completed successfully.")

            except Exception as e:
                print(f"Error during FMG Proxy Collection: {e}")
                page.screenshot(path="fmg_proxy_error.png")
            finally:
                browser.close()

    def _login_fmg(self, page):
        print("Logging in to FMG...")
        page.goto(self.fmg_url)
        page.wait_for_load_state("networkidle")

        # Standard Fortinet Login
        page.fill("input[id='username']", self.fmg_user)
        page.fill("input[id='password']", self.fmg_pass)
        page.click("button#login_button")

        page.wait_for_selector("div.main-content", timeout=30000)
        print("Login successful.")

    def _get_device_list(self, page):
        """
        Navigates to Device Manager and scrapes the list of managed devices.
        Returns a list of dicts: [{'name': 'Branch-01', 'id': 'OID123'}]
        """
        print("Retrieving Device List...")
        # Navigate to Device Manager
        # page.goto(f"{self.fmg_url}/p/device/manager/") # Adjust if URL differs
        # For now, let's assume we are on the dashboard or navigate via click

        # Scrape Table
        devices = []
        # rows = page.query_selector_all("table#device_list tbody tr")
        # for row in rows:
        #     name = row.query_selector(".name").inner_text()
        #     # ID might be hidden or part of a link attribute
        #     devices.append({'name': name})

        # MOCK DEVICE LIST if scraping fails or for template
        if not devices:
            print("No devices found via scraping (using mock logic).")
            # In production, this would be populated.
            # devices = [{'name': 'Branch-01'}, {'name': 'Branch-02'}]

        return devices

    def _collect_via_proxy(self, context, device):
        """
        Opens a new page (tab) to proxy into the specific device.
        """
        print(f"Connecting to {device['name']} via Proxy Tunnel...")

        # Construct Proxy URL
        # Pattern: https://<fmg>/p/firewall/<device_name>/
        proxy_url = f"{self.fmg_url}/p/firewall/{device['name']}/"

        page = context.new_page()
        try:
            page.goto(proxy_url)
            page.wait_for_load_state("networkidle")

            # Now we are "inside" the FortiGate GUI via FMG proxy.
            # We can check specific dashboards/widgets.

            # 1. Check Interfaces (WAN Status)
            # page.click("text=Network")
            # page.click("text=Interfaces")
            wan_status = True # Mock logic
            latency = 0
            loss = 0
            jitter = 0

            # Scrape WAN metrics if visible (e.g. SD-WAN Monitor)
            # page.click("text=SD-WAN Status")
            # ... scrape latency/jitter table ...

            # 2. Check Managed Switch/AP (LAN Status)
            # page.click("text=WiFi & Switch Controller")
            sw_status = True
            ap_status = True

            # Save to DB
            self._update_db(device['name'], wan_status, sw_status, ap_status, latency, loss, jitter)

        finally:
            page.close()

    def _update_db(self, site_name, wan_status, sw_status, ap_status, latency, loss, jitter):
        session = get_session()
        site = session.query(SiteStatus).filter_by(site_name=site_name).first()

        if not site:
            # Create new if doesn't exist (or log warning)
            site = SiteStatus(site_id=site_name, site_name=site_name)
            session.add(site)

        site.wan_status = wan_status
        site.lan_switch_status = sw_status
        site.lan_ap_status = ap_status
        site.latency_ms = latency
        site.packet_loss_pct = loss
        site.jitter_ms = jitter
        site.timestamp = datetime.utcnow()

        session.commit()
        session.close()
        print(f"Updated DB for {site_name}")

if __name__ == "__main__":
    pass
