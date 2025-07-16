# SPDX-License-Identifier: AGPL-3.0-or-later
"""Custom Search Engine Integration with gethomepage/homepage

This engine integrates with gethomepage/homepage service API
to provide search results for internal services and applications.

1. Copy file to `/usr/local/searxng/searx/engines/dashboard_services.py`
2. Add the following configuration to your `settings.yml` file:

\```yaml
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
\```

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
engine_type = 'online'
categories = ['general']
disabled = False
timeout = 10.0
paging = False
send_accept_language_header = False

# API endpoint
base_url = f"{HOMEPAGE_BASE_URL}/api/services"

# Store the current query
_current_query = ""

def request(query, params):
    """Build the request parameters for the dashboard services API."""
    global _current_query
    _current_query = query.lower()  # Store for filtering in response

    params['url'] = base_url
    params['method'] = 'GET'
    params['headers'] = {
        'Accept': 'application/json',
        'User-Agent': 'SearXNG Dashboard Services Engine'
    }
    return params

def response(resp):
    """Parse the API response and return search results."""
    global _current_query
    results = []

    try:
        # Check if response is empty
        if not resp.text.strip():
            print("Dashboard Services Engine: Empty response")
            return results

        # Parse JSON response
        json_data = loads(resp.text)

        # Get the query for filtering
        query = _current_query
        if not query:
            print("Dashboard Services Engine: No query available")
            return results  # No query, no results

        # Collect all matching services with their scores
        matched_services = []

        # Process each group in the response
        for group in json_data:
            group_name = group.get('name', 'Unknown Group')

            # Process direct services
            if 'services' in group:
                for service in group['services']:
                    score = _calculate_match_score(service, group_name, query)
                    if score > 0:  # Only include if there's a match
                        matched_services.append({
                            'service': service,
                            'group_name': group_name,
                            'score': score
                        })

            # Process nested groups
            if 'groups' in group:
                for subgroup in group['groups']:
                    subgroup_name = subgroup.get('name', 'Unknown Subgroup')
                    if 'services' in subgroup:
                        for service in subgroup['services']:
                            score = _calculate_match_score(service, f"{group_name} > {subgroup_name}", query)
                            if score > 0:  # Only include if there's a match
                                matched_services.append({
                                    'service': service,
                                    'group_name': f"{group_name} > {subgroup_name}",
                                    'score': score
                                })

        # Sort by score (highest first)
        matched_services.sort(key=lambda x: x['score'], reverse=True)

        # Create results from sorted matches
        for match in matched_services:
            results.append(_create_service_result(match['service'], match['group_name']))

    except Exception as e:
        print(f"Dashboard Services Engine Error: {e}")
        print(f"Response content: {resp.text[:200]}...")  # Show first 200 chars for debugging

    return results

def _calculate_match_score(service, group_name, query):
    """Calculate a relevance score based on where the query matches."""
    score = 0

    # Get the values to check, converting to lowercase and handling None values
    name = (service.get('name', '') or '').lower()
    description = (service.get('description', '') or '').lower()
    server = (service.get('server', '') or '').lower()
    container = (service.get('container', '') or '').lower()
    group_name = (group_name or '').lower()

    # Check for matches in different fields with different weights
    if query in name:
        score += 10  # Highest weight for name match
    if query in description:
        score += 5  # Medium weight for description match
    if query in server:
        score += 2  # Lower weight for server/container matches
    if query in container:
        score += 2
    if query in group_name:
        score += 3  # Medium-low weight for group match

    return score

def _create_service_result(service, group_name):
    """Create a search result from a service object."""
    name = service.get('name', 'Unknown Service')
    description = service.get('description', 'No description available')
    href = service.get('href', '#')
    server = service.get('server', '')
    container = service.get('container', '')
    icon = service.get('icon', '')

    # Simple content creation
    content = description
    if server:
        content += f" | Server: {server}"
    if container:
        content += f" | Container: {container}"

    result = {
        'url': href,
        'title': f"{name} ({group_name})",
        'content': content,
    }

    # Add icon if available
    if icon:
        if icon.startswith('http'):
            result['img_src'] = icon
        elif icon.startswith('/'):
            # Local icon path
            result['img_src'] = f"{HOMEPAGE_BASE_URL}{icon}"

    return result
