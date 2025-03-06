#!/usr/bin/env python3
import os
import time
import requests
from loguru import logger
from typing import List, Dict, Any, Optional, Tuple


class PortainerAPIClient:
    """Functional API Wrapper for Portainer service"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.base_url = base_url or os.getenv("PORTAINER_API_URL")
        self.username = username or os.getenv("PORTAINER_USERNAME")
        self.password = password or os.getenv("PORTAINER_PASSWORD")
        self.jwt_token = None
        self.verify_ssl = False

        if not self.base_url or not self.username or not self.password:
            logger.error("Portainer URL, username and password must be provided")
            raise ValueError("Portainer URL, username and password must be provided")

        logger.debug(f"PortainerAPIClient initialized with base URL: {self.base_url}")

    def authenticate(self) -> str:
        """
        Authenticate with Portainer API

        Returns:
            str: The JWT token for authenticated requests

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        auth_endpoint = f"{self.base_url}/api/auth"
        payload = {"Username": self.username, "Password": self.password}

        logger.info("Authenticating with Portainer API")

        try:
            response = requests.post(
                auth_endpoint, json=payload, verify=self.verify_ssl
            )
            response.raise_for_status()
            token = response.json().get("jwt")

            if not token:
                logger.error("Authentication failed: No JWT token in response")
                raise ValueError("Authentication failed: No JWT token in response")

            self.jwt_token = token
            logger.success("Successfully authenticated with Portainer API")
            return token

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    def get_request_headers(self) -> Dict[str, str]:
        """
        Get headers for authenticated API requests

        Returns:
            Dict[str, str]: Headers including Authorization
        """
        if not self.jwt_token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Accept": "application/json",
        }

    def get_containers(self, endpoint_id: str, docker_version: str) -> List[Dict]:
        """
        Get all containers from a specific endpoint

        Args:
            endpoint_id: The endpoint ID
            docker_version: Docker API version

        Returns:
            List[Dict]: List of containers

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        containers_url = f"{self.base_url}/api/endpoints/{endpoint_id}/docker/{docker_version}/containers/json?all=true"
        logger.info(f"Fetching containers from endpoint {endpoint_id}")

        try:
            response = requests.get(
                containers_url,
                headers=self.get_request_headers(),
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            containers = response.json()
            logger.success(f"Successfully fetched {len(containers)} containers")
            return containers

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch containers: {str(e)}")
            raise

    def start_stack(self, stack_id: str, endpoint_id: str) -> bool:
        """
        Start a specific stack

        Args:
            stack_id: The stack ID
            endpoint_id: The endpoint ID

        Returns:
            bool: True if successful

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        stack_url = (
            f"{self.base_url}/api/stacks/{stack_id}/start?endpointId={endpoint_id}"
        )
        params = {"endpointId": endpoint_id, "id": stack_id}

        logger.info(f"Starting stack {stack_id} on endpoint {endpoint_id}")

        try:
            response = requests.post(
                stack_url,
                headers=self.get_request_headers(),
                data=params,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            logger.success(f"Stack {stack_id} started successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start stack {stack_id}: {str(e)}")
            raise

    def stop_stack(self, stack_id: str, endpoint_id: str) -> bool:
        """
        Stop a specific stack

        Args:
            stack_id: The stack ID
            endpoint_id: The endpoint ID

        Returns:
            bool: True if successful

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        stack_url = (
            f"{self.base_url}/api/stacks/{stack_id}/stop?endpointId={endpoint_id}"
        )
        params = {"endpointId": endpoint_id, "id": stack_id}

        logger.info(f"Stopping stack {stack_id} on endpoint {endpoint_id}")

        try:
            response = requests.post(
                stack_url,
                headers=self.get_request_headers(),
                data=params,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            logger.success(f"Stack {stack_id} stopped successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to stop stack {stack_id}: {str(e)}")
            raise


class ServiceManager:
    """Manages service stack operations"""

    def __init__(self, api_client: PortainerAPIClient):
        """
        Initialize with API client

        Args:
            api_client: Portainer API client instance
        """
        self.api_client = api_client
        self.endpoints_config = ENDPOINTS_CONFIG
        logger.debug(f"ServiceManager initialized")

    def find_service_location(self, service_name: str) -> Optional[Tuple[str, str]]:
        """
        Find endpoint ID and stack ID for a given service name

        Args:
            service_name: Name of the service to find

        Returns:
            Optional[Tuple[str, str]]: (endpoint_id, stack_id) if found, None otherwise
        """
        logger.debug(f"Looking for service: {service_name}")

        for endpoint_id, endpoint_info in self.endpoints_config["endpoints"].items():
            stacks = endpoint_info.get("stacks", {})

            for stack_id, stack_name in stacks.items():
                if stack_name == service_name:
                    logger.info(
                        f"Found service '{service_name}' at endpoint {endpoint_id}, stack {stack_id}"
                    )
                    return (endpoint_id, stack_id)

        logger.warning(f"Service '{service_name}' not found in endpoints configuration")
        return None

    def check_service_health(
        self, service_name: str
    ) -> Tuple[bool, Optional[Tuple[str, str]]]:
        """
        Check if all containers in a service are running and healthy

        Args:
            service_name: Name of the service to check

        Returns:
            Tuple[bool, Optional[Tuple[str, str]]]: (is_healthy, (endpoint_id, stack_id))
            where is_healthy is True if all containers are running and healthy
        """
        service_location = self.find_service_location(service_name)
        if not service_location:
            return (False, None)

        endpoint_id, stack_id = service_location
        endpoint_info = self.endpoints_config["endpoints"][endpoint_id]
        docker_version = endpoint_info.get("docker_version", "v1.24")

        try:
            containers = self.api_client.get_containers(endpoint_id, docker_version)

            # Filter containers belonging to this service/stack
            service_containers = []
            for container in containers:
                labels = container.get("Labels", {})
                project_name = labels.get("com.docker.compose.project")

                if project_name == service_name:
                    service_containers.append(container)

            if not service_containers:
                logger.warning(f"No containers found for service '{service_name}'")
                return (False, service_location)

            # Check if all containers are healthy
            all_healthy = True
            for container in service_containers:
                state = container.get("State", "").lower()
                if state != "running" and not state.startswith("healthy"):
                    logger.warning(
                        f"Container {container.get('Names', ['unknown'])[0]} in state: {state}"
                    )
                    all_healthy = False

            logger.info(
                f"Service '{service_name}' health check: {'healthy' if all_healthy else 'unhealthy'}"
            )
            return (all_healthy, service_location)

        except Exception as e:
            logger.error(f"Error checking service health: {str(e)}")
            return (False, service_location)

    def start_service(self, service_name: str) -> Dict[str, Any]:
        """
        Start a service if it's not running

        Args:
            service_name: Name of the service to start

        Returns:
            Dict[str, Any]: Response with status information
        """
        logger.info(f"Starting service '{service_name}'")

        try:
            # Check if service exists and its health
            is_healthy, location = self.check_service_health(service_name)

            if not location:
                return {
                    "success": False,
                    "message": f"Service '{service_name}' not found in configuration",
                }

            endpoint_id, stack_id = location

            if is_healthy:
                logger.info(f"Service '{service_name}' is already running and healthy")
                return {
                    "success": True,
                    "message": f"Service '{service_name}' is already running",
                    "action": "none",
                    "endpoint_id": endpoint_id,
                    "stack_id": stack_id,
                }

            # Service exists but is not healthy, restart it
            logger.info(
                f"Service '{service_name}' exists but is not healthy, restarting..."
            )

            # Try to stop first, ignoring errors
            try:
                self.api_client.stop_stack(stack_id, endpoint_id)
                time.sleep(5)  # Give it some time to stop
            except Exception as e:
                logger.warning(f"Error stopping service (continuing anyway): {str(e)}")

            # Start the service
            self.api_client.start_stack(stack_id, endpoint_id)

            return {
                "success": True,
                "message": f"Service '{service_name}' restarted successfully",
                "action": "restart",
                "endpoint_id": endpoint_id,
                "stack_id": stack_id,
            }

        except Exception as e:
            logger.exception(f"Error starting service '{service_name}': {str(e)}")
            return {"success": False, "message": f"Error starting service: {str(e)}"}
