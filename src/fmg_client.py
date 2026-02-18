import requests
import json
import logging
from requests.adapters import HTTPAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FMGClient:
    def __init__(self, base_url, username, password, verify_ssl=False):
        """
        Initialize the FMG Client.

        :param base_url: Base URL of the FortiManager (e.g., https://fmg.example.com)
        :param username: Username for authentication
        :param password: Password for authentication
        :param verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session_id = None

        # Increase connection pool size to handle parallel requests
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        if not verify_ssl:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    def login(self):
        """
        Login to FMG to retrieve a session cookie.
        This simulates a browser login or JSON-RPC login.
        """
        login_url = f"{self.base_url}/jsonrpc"
        payload = {
            "method": "exec",
            "params": [
                {
                    "url": "/sys/login/user",
                    "data": {
                        "user": self.username,
                        "passwd": self.password
                    }
                }
            ],
            "id": 1
        }

        try:
            response = self.session.post(login_url, json=payload, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            if 'session' in data:
                self.session_id = data['session']
                logger.info(f"Login successful. Session ID: {self.session_id}")
                return True
            elif 'result' in data and data['result'][0]['status']['code'] == 0:
                 # Sometimes the session is set in cookies automatically
                self.session_id = self.session.cookies.get('session_id') # Example cookie name
                logger.info("Login successful (via cookies).")
                return True
            else:
                logger.error(f"Login failed: {data}")
                return False
        except Exception as e:
            logger.error(f"Login exception: {e}")
            return False

    def get_managed_devices(self, adom="root"):
        """
        Retrieve a list of managed devices in the specified ADOM.
        """
        url = f"{self.base_url}/jsonrpc"
        payload = {
            "method": "get",
            "params": [
                {
                    "url": f"/dvmdb/adom/{adom}/device"
                }
            ],
            "id": 2
        }
        if self.session_id:
            payload['session'] = self.session_id

        try:
            response = self.session.post(url, json=payload, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            if 'result' in data and data['result'][0]['status']['code'] == 0:
                return data['result'][0]['data']
            else:
                logger.error(f"Failed to get devices: {data}")
                return []
        except Exception as e:
            logger.error(f"Exception getting devices: {e}")
            return []

    def execute_device_command(self, device_name, command_api_path):
        """
        Execute a command or fetch data from a specific device via FMG proxy.

        :param device_name: The name or serial number of the target device.
        :param command_api_path: The API path on the device (e.g., /api/v2/monitor/system/status).
        """
        url = f"{self.base_url}/jsonrpc"

        # This payload structure is typical for FMG proxying to FGT
        payload = {
            "method": "exec",
            "params": [
                {
                    "url": "/sys/proxy/json",
                    "data": {
                        "target": device_name,
                        "action": "get",
                        "resource": command_api_path
                    }
                }
            ],
            "id": 3
        }
        if self.session_id:
            payload['session'] = self.session_id

        try:
            response = self.session.post(url, json=payload, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            if 'result' in data and len(data['result']) > 0:
                # The inner result from the device
                device_response = data['result'][0]
                if 'status' in device_response and device_response['status']['code'] == 0:
                     return device_response.get('data', {})
                else:
                    logger.warning(f"Device command failed for {device_name}: {device_response}")
                    return None
            else:
                logger.error(f"Proxy command failed: {data}")
                return None
        except Exception as e:
            logger.error(f"Exception executing command on {device_name}: {e}")
            return None

    def logout(self):
        """
        Logout from FMG.
        """
        url = f"{self.base_url}/jsonrpc"
        payload = {
            "method": "exec",
            "params": [
                {
                    "url": "/sys/login/user",
                    "data": {} # Logout often doesn't need data or uses a specific logout action
                }
            ],
            "id": 4
        }
        try:
            self.session.post(url, json=payload, verify=self.verify_ssl)
            logger.info("Logged out.")
        except Exception:
            pass
