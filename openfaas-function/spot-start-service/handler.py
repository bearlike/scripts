#!/usr/bin/env python3
import json
from loguru import logger
from typing import Optional, Tuple
from .portainer import PortainerAPIClient, ServiceManager

# Configure logger
logger.add(
    "spot-start-service-logs.log",
    rotation="10 MB",
    retention="1 week",
    level="DEBUG",
    enqueue=True,
)
logger.info("Starting Spot Start Service function")

# Example -> Service to stack mapping
# TODO: Automatically populate this from Portainer API
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

try:
    from .constants import PORTAINER_ENDPOINTS_CONFIG

    ENDPOINTS_CONFIG = PORTAINER_ENDPOINTS_CONFIG.copy()
except ImportError as err_msg:
    logger.exception(err_msg)
    logger.exception(
        "Failed to import constants.py. You may need to create it.")
    raise err_msg


def parse_event_body(event) -> Tuple[Optional[str], Optional[str]]:
    """Get the body of the event"""
    # Parse request body if it exists
    request_body = {}
    if isinstance(event.body, bytes):
        json_str = event.body.decode("utf-8")
        request_body: dict = json.loads(json_str)
    else:
        request_body: dict = event.body

    # Check if service name is provided
    service_name = request_body.get("service")
    referral_url = request_body.get("referral_url")
    return service_name, referral_url


def build_response(
    body: dict, content_type: str = "application/json", status_code: int = 200
) -> dict:
    """Get the response"""
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type": content_type},
    }


def format_event(event_handler) -> str:
    """Format the event for logging"""
    return (
        f"Event("
        f"method={event_handler.method}, "
        f"path={event_handler.path}, "
        f"query={event_handler.query}, "
        f"body={event_handler.body}, "
        f"headers={event_handler.headers})"
    )


def handle(event, context):
    """OpenFaaS handler function"""
    if event.method != "POST":
        return build_response(
            status_code=405,
            body={"error": f"Method {event.method} not allowed"},
        )

    logger.info(f"Function invoked with event: {format_event(event)}")

    try:
        service_name, referral_url = parse_event_body(event)
        if not service_name and not referral_url:
            logger.error("No service name or referral URL provided")
            return build_response(
                status_code=400,
                body={
                    "error": "Service name or referral URL is required",
                    "event": format_event(event),
                },
            )

        # Initialize API client
        api_client = PortainerAPIClient()
        service_manager = ServiceManager(api_client, ENDPOINTS_CONFIG)

        if referral_url:
            # Find the service name from the referral URL
            service_name = service_manager.find_service_from_url(referral_url)
            if not service_name:
                logger.error(
                    f"No service found for referral URL: {referral_url}")
                return build_response(
                    status_code=404,
                    body={
                        "error": f"No service found for referral URL: {referral_url}",
                    },
                )

        if service_name:
            # Start the service
            result = service_manager.start_service(service_name)
            status_code = 200 if result.get("success", False) else 500
            logger.success(
                f"Request processed with status {status_code}: {result}")
            return build_response(status_code=status_code, body=result)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        return build_response(
            status_code=400,
            body={"error": "Invalid JSON in request",
                  "event": format_event(event)},
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return build_response(
            status_code=500,
            body={
                "error": f"Internal server error: {str(e)}",
                "event": format_event(event),
            },
        )


if __name__ == "__main__":
    # Example event for local testing
    # Ensure env vars are set for local testing
    from dotenv import load_dotenv

    load_dotenv()

    class TestEvent:
        def __init__(self, method, body):
            self.method = method
            self.body = body
            self.headers = None
            self.query = None
            self.path = None

        def __repr__(self):
            return format_event(self)

    byte_data = b'{"referral_url": "https://jupyter.hurricane.home"}'
    test_event = TestEvent(
        method="POST",
        body=byte_data,
    )
    logger.debug(f"Local test event: {test_event}")
    response = handle(test_event, None)
    logger.info(f"Local test response: {response}")
