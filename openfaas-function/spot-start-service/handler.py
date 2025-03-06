#!/usr/bin/env python3
import json
from loguru import logger
from portainer import PortainerAPIClient, ServiceManager

# Configure logger
logger.add(
    "function_logs.log",
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
    from constants import PORTAINER_ENDPOINTS_CONFIG

    ENDPOINTS_CONFIG = PORTAINER_ENDPOINTS_CONFIG.copy()
except ImportError as err_msg:
    logger.exception(err_msg)
    logger.exception("Failed to import constants.py. You may need to create it.")
    raise err_msg


def handle(event, context):
    """OpenFaaS handler function"""

    def format_event(event_handler):
        return (
            f"Event("
            f"method={event_handler.method}, "
            f"path={event_handler.path}, "
            f"query={event_handler.query}, "
            f"body={event_handler.body}, "
            f"headers={event_handler.headers})"
        )

    if event.method != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": f"Method {event.method} not allowed"}),
            "headers": {"Content-Type": "application/json"},
        }

    logger.info(f"Function invoked with event: {event}")

    try:
        # Parse request body if it exists
        request_body = {}
        if isinstance(event.body, bytes):
            json_str = event.body.decode("utf-8")
            request_body = json.loads(json_str)
        else:
            request_body = event.body

        # Check if service name is provided
        service_name = request_body.get("service")
        if not service_name:
            logger.error("No service name provided")
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Service name is required", "event": format_event(event)}
                ),
                "headers": {"Content-Type": "application/json"},
            }

        # Initialize API client
        api_client = PortainerAPIClient()
        service_manager = ServiceManager(api_client, ENDPOINTS_CONFIG)

        # Start the service
        result = service_manager.start_service(service_name)

        status_code = 200 if result.get("success", False) else 500

        logger.success(f"Request processed with status {status_code}: {result}")
        return {
            "statusCode": status_code,
            "body": json.dumps(result),
            "headers": {"Content-Type": "application/json"},
        }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "Invalid JSON in request", "event": format_event(event)}
            ),
            "headers": {"Content-Type": "application/json"},
        }
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": f"Internal server error: {str(e)}",
                    "event": format_event(event),
                }
            ),
            "headers": {"Content-Type": "application/json"},
        }


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

    byte_data = b'{"service": "n8n"}'
    test_event = TestEvent(
        method="POST",
        body=byte_data,
    )
    logger.debug(f"Local test event: {test_event}")
    response = handle(test_event, None)
    logger.info(f"Local test response: {response}")
