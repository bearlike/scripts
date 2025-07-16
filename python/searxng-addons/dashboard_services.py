# SPDX-License-Identifier: AGPL-3.0-or-later
"""Custom Search Engine Integration with gethomepage/homepage

This engine integrates with gethomepage/homepage service API
to provide search results for internal services and applications.

1. Copy file to `/usr/local/searxng/searx/engines/dashboard_services.py`
2. Add the following configuration to your `settings.yml` file:

```yaml
engines:
  - name: selfhosted
    engine: dashboard_services
    categories: [general]
    shortcut: dash
    timeout: 10.0
    disabled: false
    enable_http: true
    enable_http2: true
    weight: 0.5  # Higher priority than regular search engines
```

For use with https://github.com/searxng/searxng
"""

from json import loads
from searx.result_types import EngineResults

# Point to your self-hosted homepage instance
HOMEPAGE_BASE_URL = "http://X.X.X.X:3000"

# Engine metadata
about = {
    "website": HOMEPAGE_BASE_URL,
    "wikidata_id": None,
    "official_api_documentation": f"{HOMEPAGE_BASE_URL}",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

# Engine configuration
engine_type = "online"
categories = ["general"]
disabled = False
timeout = 10.0
paging = False
send_accept_language_header = False

# API endpoint
base_url = f"{HOMEPAGE_BASE_URL}/api/services"


def request(query, params):
    """Build the request parameters for the dashboard services API."""
    params["url"] = base_url
    params["method"] = "GET"
    params["headers"] = {
        "Accept": "application/json",
        "User-Agent": "SearXNG Dashboard Services Engine",
    }
    return params


def response(resp) -> EngineResults:
    """Parse the API response and return search results."""
    results = EngineResults()

    try:
        # Check if response is empty
        if not resp.text.strip():
            print("Dashboard Services Engine: Empty response")
            return results

        # Parse JSON response
        json_data = loads(resp.text)

        # Get query from the original request (simplified)
        query = ""
        if hasattr(resp, "url") and "?" in str(resp.url):
            # Try to extract query from URL params if available
            pass

        # Process each group in the response
        for group in json_data:
            group_name = group.get("name", "Unknown Group")

            # Process direct services
            if "services" in group:
                for service in group["services"]:
                    results.append(_create_service_result(service, group_name))

            # Process nested groups
            if "groups" in group:
                for subgroup in group["groups"]:
                    subgroup_name = subgroup.get("name", "Unknown Subgroup")
                    if "services" in subgroup:
                        for service in subgroup["services"]:
                            results.append(
                                _create_service_result(
                                    service, f"{group_name} > {subgroup_name}"
                                )
                            )

    except Exception as e:
        print(f"Dashboard Services Engine Error: {e}")
        print(
            f"Response content: {resp.text[:200]}..."
        )  # Show first 200 chars for debugging

    return results


def _create_service_result(service, group_name):
    """Create a search result from a service object."""
    name = service.get("name", "Unknown Service")
    description = service.get("description", "No description available")
    href = service.get("href", "#")
    server = service.get("server", "")
    container = service.get("container", "")

    # Simple content creation
    content = description
    if server:
        content += f" | Server: {server}"
    if container:
        content += f" | Container: {container}"

    return {
        "url": href,
        "title": f"{name} ({group_name})",
        "content": content,
        "category": "dashboard_services",
    }
