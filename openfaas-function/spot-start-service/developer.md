# Developer Documentation

## Step 1: Receive the name of the service to start

We should only start the service if it is not already running. This include restarting the service, when its some containers are not running or unhealthy.

```json
{
    "service": "nextcloud",
}
```

## Step 2: Authenticate against the API using the admin account

```bash
http --verify=no POST https://portainer.server.local/api/auth Username="<admin username>" Password="<adminpassword>"
```

The response is a JSON object containing the JWT token inside the `jwt` field. You will need to pass this token inside the authorization header when executing an authentication query against the API.

```json
{ "jwt":"ABCDEF.ABCDEF.ABCDEF"}
```

The value of the authorization header must be of the form `Bearer <JWT_TOKEN>`:

```raw
Bearer ABCDEF.ABCDEF.ABCDEF
```

This token is valid for 8 hours. Once it expires, you will need to generate another token to execute authenticated queries.

## Step 3: Use the below Endpoint to Service Stack Mapping

Update the endpoint and stack IDs in the mapping below. Find your endpoint and stack IDs through the Portainer API or UI.

```json
{
    "endpoints": {
        "100": {
            "name": "endpoint-primary",
            "docker_version": "v1.24",
            "stacks": {
                "100": "example_stack",
                "102": "service-media",
                "103": "service-pdf",
                "104": "service-ai",
                "105": "service-workflow",
                "106": "service-launcher",
                "107": "service-game",
                "108": "service-arcade"
            }
        },
        "2": {
            "name": "endpoint-secondary",
            "docker_version": "v1.24",
            "stacks": {
                "201": "service-dashboard"
            }
        }
    }
}
```

## Step 4: Find out statuses of docker containers running within in the stack

```bash
http --verify=no https://portainer.server.local/api/endpoints/12/docker/v1.24/containers/json?all=true "Authorization:Bearer <JWT_TOKEN>"
```

> Sample Response

Each entry in the response matching the service name is a container running within the stack. Check the `State` field to determine if the service is running or not, and the `Labels.com.docker.compose.project` field to determine if the container belongs to the correct stack. First gather all containers matching the docker-compose stack name, and then check the state of each container. When some containers are not running, or unhealthy, the service is considered not running. We will then start or restart the entire stack.

```json
[
    {
        "Created": 1600000000,
        "HostConfig": {
            "NetworkMode": "example_network"
        },
        "Id": "abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "Image": "example/service:latest",
        "ImageID": "sha256:abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "Labels": {
            "com.docker.compose.project": "example_stack", // Name of the service or docker-compose stack
            "home.resolve.domain": "example.server.local" // Add service domain name label to docker-compose file.
            "com.docker.compose.project.config_files": "/data/compose/100/docker-compose.yml",
            "com.docker.compose.project.environment_file": "/data/compose/100/stack.env",
            "com.docker.compose.project.working_dir": "/data/compose/100",
        },
        "Names": [
            "/example-container"
        ],
        // Can begin with "running", "exited", "exited - code 0", "exited - code 137", "exited - code 153", "healthy", "restarting", "paused", "removing"
        "State": "running",
        "Status": "Up 2 hours"
    },
    {
        "Created": 1600000001,
        "HostConfig": {
            "NetworkMode": "example_network"
        },
        "Id": "def456789abcdef0123456789abcdef0123456789abcdef0123456789abc123",
        "Image": "example/database:latest",
        "ImageID": "sha256:def456789abcdef0123456789abcdef0123456789abcdef0123456789abc123",
        "Labels": {
            "com.docker.compose.project": "example_stack",
            "com.docker.compose.project.config_files": "/data/compose/100/docker-compose.yml",
            "com.docker.compose.project.environment_file": "/data/compose/100/stack.env",
            "com.docker.compose.project.working_dir": "/data/compose/100"
        },
        "Names": [
            "/example-database"
        ],
        "State": "exited",
        "Status": "Exited (1) 30 minutes ago"
    }
    // More entries of all containers from the endpoint
]
```

## Step 5: Starting and Stopping Portainer Stacks

I use httpie for my API calls. The Stack start/stop commands are as follows: (you will need to change IP, IDs and key)

Stack Stop:

```bash
http --verify=no --form POST https://portainer.server.local/api/stacks/[STACK_ID]/stop?endpointId=[ENDPOINT_ID] "Authorization:Bearer <JWT_TOKEN>"
```

Stack Start:

```bash
http --verify=no --form POST https://portainer.server.local/api/stacks/[STACK_ID]/start?endpointId=[ENDPOINT_ID] "Authorization:Bearer <JWT_TOKEN>"
```
