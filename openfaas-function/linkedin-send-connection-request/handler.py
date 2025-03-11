#!/usr/bin/env python3
import os
import json
import jinja2
from loguru import logger
from gradio_client import Client
from typing import Optional, Tuple
import datetime


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


def render_template(template_path, *args, **kwargs):
    """
    Render a Jinja2 template file with the provided arguments.

    Args:
        template_path (str): Path to the Jinja2 template file
        *args: Additional positional arguments
        **kwargs: Variables to pass to the template

    Returns:
        str: Rendered template string
    """
    try:
        # Set up the Jinja2 environment
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)

        # Create the environment with the file system loader
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

        # Load and render the template
        template = env.get_template(template_file)
        return template.render(**kwargs)
    except Exception as e:
        logger.error(f"Error rendering template {template_path}: {e}")
        return None


def parse_event_body(event) -> Optional[str]:
    """Get the body of the event"""
    # Parse request body if it exists
    request_body = {}
    if isinstance(event.body, bytes):
        json_str = event.body.decode("utf-8")
        request_body: dict = json.loads(json_str)
    else:
        request_body: dict = event.body

    # Check if service name is provided
    return request_body.get("linkedin_profile").strip()


def handle(event, context):
    metadata = {
        "timestamp": datetime.datetime.now().isoformat(),
        "linkedin_profile": None
    }
    try:
        if event.method != "POST":
            return build_response(
                status_code=405,
                body={"error": f"Method {event.method} not allowed"},
            )

        logger.info(f"Function invoked with event: {format_event(event)}")
        profile_url = parse_event_body(event)
        if not profile_url:
            raise Exception("linkedin_profile not provided or empty")

        metadata["linkedin_profile"] = profile_url
        prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
        task_prompt = render_template(
            os.path.join(prompt_dir, "task.md.j2"), PROFILE_URL=profile_url
        )
        # * Guidelines are ignored during commits.
        # * Please create this with your message template.
        guidelines_prompt = render_template(
            os.path.join(prompt_dir, "guidelines.md.j2")
        )
        BROWSER_USE_URL = os.getenv("BROWSER_USE_URL")
        if BROWSER_USE_URL is None:
            raise Exception("BROWSER_USE_URL not provided or empty")

        client = Client(
            BROWSER_USE_URL, ssl_verify=False, httpx_kwargs={"timeout": 300}
        )
        result = client.predict(
            window_w=1280,
            window_h=1100,
            max_steps=100,
            chrome_cdp="",
            llm_api_key="",
            headless=False,
            llm_base_url="",
            use_vision=True,
            task=task_prompt,
            llm_num_ctx=32000,
            llm_temperature=1,
            agent_type="custom",
            use_own_browser=True,
            llm_provider="openai",
            disable_security=True,
            enable_recording=True,
            keep_browser_open=False,
            max_actions_per_step=10,
            tool_calling_method="auto",
            add_infos=guidelines_prompt,
            api_name="/run_with_stream",
            llm_model_name="gpt-4o-mini",
            save_trace_path="./tmp/traces",
            save_recording_path="./tmp/record_videos",
            save_agent_history_path="./tmp/agent_history",
        )
        response = {
            "status": "Automation Completed",
            "result": result,
            "metadata": metadata,
        }
        logger.success(response)
        return build_response(body=response)
    except Exception as e:
        logger.exception("An error occurred while handling the request")
        return build_response(
            status_code=500,
            body={"error": f"Error while processing - {e}", "metadata": metadata},
        )


if __name__ == "__main__":
    try:
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

        byte_data = (
            b'{"linkedin_profile": "https://www.linkedin.com/in/francescapalmen"}'
        )
        test_event = TestEvent(
            method="POST",
            body=byte_data,
        )
        logger.debug(f"Local test event: {test_event}")
        response = handle(test_event, None)
        logger.info(f"Local test response: {response}")
    except Exception as e:
        logger.exception(f"An error occurred during local testing - {e}")
