#!/usr/bin/env python3
import json
import unittest
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
from .handler import handle, PortainerAPIClient, ServiceManager

load_dotenv()

ENDPOINTS_CONFIG = {
    "endpoints": {
        "1": {
            "name": "Example-Server-1",
            "docker_version": "v1.xx",
            "stacks": {
                "101": "service-a",
                "102": "service-b",
                "103": "service-c",
                "104": "service-d",
                "105": "service-e",
                "106": "service-f",
                "107": "service-g",
                "108": "service-h",
            },
        },
        "2": {
            "name": "Example-Server-2",
            "docker_version": "v1.xx",
            "stacks": {
                "201": "service-z",
            },
        },
    }
}


class TestEvent:
    def __init__(self, method="POST", body=None, headers=None, query=None, path=None):
        self.method = method
        self.body = body
        self.headers = headers or {}
        self.query = query or {}
        self.path = path or ""


class TestSpotStartService(unittest.TestCase):
    """Tests for the spot start service handler"""

    @patch("handler.PortainerAPIClient")
    @patch("handler.ServiceManager")
    def test_handle_valid_request(self, mock_service_manager, mock_api_client):
        """Test that handle processes valid requests correctly"""
        # Setup mocks
        instance = mock_service_manager.return_value
        instance.start_service.return_value = {
            "success": True,
            "message": "Service 'nextcloud' restarted successfully",
            "action": "restart",
            "endpoint_id": "12",
            "stack_id": "80",
        }

        # Use dict for body instead of JSON string
        event = TestEvent(method="POST", body={"service": "nextcloud"})

        # Call handler
        result = handle(event, {})

        # Verify results
        self.assertEqual(result["statusCode"], 200)
        response_body = json.loads(result["body"])
        self.assertTrue(response_body["success"])
        self.assertEqual(response_body["action"], "restart")

        # Verify mocks
        instance.start_service.assert_called_once_with("nextcloud")

    @patch("handler.PortainerAPIClient")
    @patch("handler.ServiceManager")
    def test_handle_missing_service(self, mock_service_manager, mock_api_client):
        """Test that handle returns error when service is missing"""
        # Use TestEvent object instead of dict
        event = TestEvent(method="POST", body={"other_field": "value"})

        # Call handler
        result = handle(event, {})

        # Verify results
        self.assertEqual(result["statusCode"], 400)
        response_body = json.loads(result["body"])
        self.assertIn("error", response_body)

        # Verify mocks
        mock_service_manager.return_value.start_service.assert_not_called()

    @patch("portainer.requests")
    def test_portainer_api_client_authenticate(self, mock_requests):
        """Test API client authentication"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"jwt": "test_token"}
        mock_requests.post.return_value = mock_response

        # Create client
        client = PortainerAPIClient(
            base_url="https://test.com/api", username="user", password="pass"
        )

        # Call authenticate
        token = client.authenticate()

        # Verify
        self.assertEqual(token, "test_token")
        self.assertEqual(client.jwt_token, "test_token")
        mock_requests.post.assert_called_once()

    def test_service_manager_find_service(self):
        """Test finding service location"""
        # Create manager with mock client
        mock_client = MagicMock()
        manager = ServiceManager(mock_client, endpoints_config=ENDPOINTS_CONFIG)

        # Test finding existing service
        location = manager.find_service_location("service-a")
        self.assertIsNotNone(location)
        self.assertEqual(location, ("1", "101"))

        # Test finding non-existent service
        location = manager.find_service_location("nonexistent")
        self.assertIsNone(location)


if __name__ == "__main__":
    unittest.main()
