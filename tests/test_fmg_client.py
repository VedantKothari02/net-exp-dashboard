import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from fmg_client import FMGClient

class TestFMGClient(unittest.TestCase):
    def setUp(self):
        self.client = FMGClient("https://fmg.example.com", "admin", "password")

    @patch('requests.Session.post')
    def test_login_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'session': 'test_session_id'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.login()
        self.assertTrue(result)
        self.assertEqual(self.client.session_id, 'test_session_id')

    @patch('requests.Session.post')
    def test_login_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': [{'status': {'code': -1, 'message': 'Auth failed'}}]}
        mock_post.return_value = mock_response

        result = self.client.login()
        self.assertFalse(result)

    @patch('requests.Session.post')
    def test_get_managed_devices(self, mock_post):
        mock_response = MagicMock()
        mock_data = [{'name': 'FGT1', 'sn': 'FGT1SN'}]
        mock_response.json.return_value = {
            'result': [{'status': {'code': 0}, 'data': mock_data}]
        }
        mock_post.return_value = mock_response

        devices = self.client.get_managed_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['name'], 'FGT1')

    @patch('requests.Session.post')
    def test_execute_device_command(self, mock_post):
        mock_response = MagicMock()
        device_data = {'cpu': 10, 'mem': 20}
        # Outer result (FMG proxy) -> Inner result (Device)
        mock_response.json.return_value = {
            'result': [
                {'status': {'code': 0}, 'data': device_data}
            ]
        }
        mock_post.return_value = mock_response

        result = self.client.execute_device_command("FGT1", "/api/v2/monitor/system/status")
        self.assertEqual(result['cpu'], 10)

if __name__ == '__main__':
    unittest.main()
