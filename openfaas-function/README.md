# Krishna's OpenFAAS function (akin to Lambda functions)

> [!NOTE]
> For development and deployment instructions, see the [OpenFaaS documentation](https://docs.openfaas.com/). This repository is for tracking the functions I create.

## Overview

This repository contains OpenFaaS functions. [OpenFaaS](https://www.openfaas.com/) is a framework for building serverless functions on top of containers that makes it easy to deploy event-driven functions and microservices to Kubernetes without repetitive boilerplate coding.

### Why did I choose OpenFaaS?

- Portable across cloud and on-premises environments
- Build and deploy using familiar containers
- Automatic scaling based on demand
- Metrics and logs for observability
- Write functions in any programming language and framework using templates

### Deployment

The `stack.yml` file contains the function definitions and deployment configuration. To deploy the functions, run:

```bash
# Copy the stack.sample.yml to stack.yml
# Update the stack.yml with your environment variables
cp stack.sample.yml stack.yml
```

OpenFaaS supports various languages through its own templates concept. We use their [`python3-http`](https://github.com/openfaas/python-flask-template) template, which is based on Alpine Linux and has a small footprint.

```bash
# This is an official template maintained by OpenFaaS
faas-cli template store pull python3-http
```

```bash
faas-cli update -f stack.yml
```

## Serverless Functions

Within the intranet, the serverless orchestration is done using OpenFaaS. It is available at [https://functions.server.local](http://functions.server.local).

---

### Function Catalog

#### llm-global-spend

- **Endpoint:** `/function/llm-global-spend`
- `Content-Type: application/json`

Calculates spend from Lite-LLM API logs instead of using the periodic spend API endpoint, which is now paywalled. Tested to work with `1.53.7`.

![Sample Request](docs/litellm-sample.png)

> [!WARNING]
> Requires a hosted [Lite-LLM](https://github.com/BerriAI/litellm) instance. You need to add `LITELLM_API_KEY` and `LITELLM_API_BASE_URL` environment variables in `stack.yaml` for the function to work.

| Description                                                                                                                 | Features                                                           | Method | Request Body | Sample Responses                                                                                   |
| --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------ | ------------ | -------------------------------------------------------------------------------------------------- |
| Retrieves spending logs for a specified user from an API endpoint and calculates the total spend within a given date range. | Queries spend logs API with user ID and date range parameters      | GET    | None         | ```{ "global_spend": 622.5803327750004, "current_month_spend": 1.10207825, "today_spend": 0.0 }``` |

---

#### spot-start-service

- **Endpoint:** `/function/spot-start-service`
- `Content-Type: application/json`

> [!WARNING]
> Requires a hosted [Portainer](https://github.com/portainer/portainer) instance. You need to add `PORTAINER_API_URL`, `PORTAINER_USERNAME` and `PORTAINER_PASSWORD` environment variables in `stack.yaml` for the function to work.

| Description                                                                                             | Features                                    | Method | Request Body                                           | Sample Responses                                                                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Starts or restarts Docker service stacks managed by Portainer.                                          | Accepts service name as input parameter     | POST   | ```{"service": "stopped_service"}```                   | ```{ "success": true, "message": "Service nextcloud successfully started", "details": { "service": "nextcloud", "endpoint": "prod-vm-1", "stack_id": "80" } }```                                                          |
| It verifies if the specified service is running and starts it if it's stopped or in an unhealthy state. | Authenticates with Portainer API            | POST   | ```{"service": "unhealthy/partial_service"}```         | ```{ "success": true, "message": "Service mediaservice successfully restarted", "details": { "service": "mediaservice", "endpoint": "prod-vm-1", "stack_id": "119" } }```                                                 |
|                                                                                                         | Locates the correct endpoint and stack ID   | POST   | ```{"service": "healthy_service"}```                   | ```{ "success": true, "message": "Service n8n is already running and healthy", "details": { "service": "n8n", "endpoint": "prod-vm-1", "stack_id": "181", "status": "healthy" } }```                                      |
|                                                                                                         | Checks container status                     | POST   | ```{"referral_url": "https://example.server.local"}``` | ```{'statusCode': 200, 'body': '{"success": true, "message": "Service 'example-stack' is already running", "action": "none", "endpoint_id": "10, "stack_id": "200"}', 'headers': {'Content-Type': 'application/json'}}``` |
|                                                                                                         | Starts or restarts service stack as needed  |        |                                                        |                                                                                                                                                                                                                           |
|                                                                                                         | Returns JSON response with operation status |        |                                                        |                                                                                                                                                                                                                           |
