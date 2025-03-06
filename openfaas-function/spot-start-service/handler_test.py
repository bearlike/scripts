#!/usr/bin/env python3
import json
import unittest
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
from handler import handle, PortainerAPIClient, ServiceManager

load_dotenv()


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

        # Test event with body as string
        event = {"body": json.dumps({"service": "nextcloud"})}

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
        # Test event with no service
        event = {"body": json.dumps({"other_field": "value"})}

        # Call handler
        result = handle(event, {})

        # Verify results
        self.assertEqual(result["statusCode"], 400)
        response_body = json.loads(result["body"])
        self.assertIn("error", response_body)

        # Verify mocks
        mock_service_manager.return_value.start_service.assert_not_called()

    @patch("handler.requests")
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
        manager = ServiceManager(mock_client)

        # Test finding existing service
        location = manager.find_service_location("nextcloud")
        self.assertIsNotNone(location)
        self.assertEqual(location, ("12", "80"))

        # Test finding non-existent service
        location = manager.find_service_location("nonexistent")
        self.assertIsNone(location)


if __name__ == "__main__":
    unittest.main()
